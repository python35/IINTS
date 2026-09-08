#!/usr/bin/env python3
"""Browser-based live mirror for the IINTS MK2 Pico display.

The desktop requests one frame at a time, so the Pico never streams when this
program is not connected and cannot build up an output backlog.

Frames arrive as *deltas*: the Pico cuts the display into horizontal bands and
only sends the bands whose contents changed since the previous transfer. A
typical screen update touches a few bands instead of the whole 115 KB frame,
which is what makes the mirror run at a smooth frame rate over USB serial.
"""

from __future__ import annotations

import argparse
import io
import json
import socket
import struct
import threading
import time
import webbrowser
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import serial
import serial.tools.list_ports
from PIL import Image, ImageDraw, ImageFont


WIDTH = 240
HEIGHT = 240
FRAME_BYTES = WIDTH * HEIGHT * 2

MIRROR_MAGIC = b"IINTS2D!"
MIRROR_PROTOCOL_VERSION = 2
MIRROR_REQUEST = b"F"
MIRROR_RESET_REQUEST = b"R"
HEADER = struct.Struct("<8sBBHIII")

# Nothing changed on the Pico: wait briefly instead of hammering its main loop.
IDLE_REQUEST_INTERVAL_SECONDS = 0.01
SERIAL_READ_BYTES = 65536
FRAME_TIMEOUT_SECONDS = 5.0
RETRY_DELAY_SECONDS = 0.5
RECONNECT_DELAY_SECONDS = 1.0
STREAM_KEEPALIVE_SECONDS = 5.0
PNG_COMPRESS_LEVEL = 1


def load_font(size: int, bold: bool = False):
    names = (
        "/System/Library/Fonts/SFNSRounded.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def create_placeholder():
    image = Image.new("RGB", (WIDTH, HEIGHT), (13, 17, 23))
    draw = ImageDraw.Draw(image)
    title_font = load_font(17, bold=True)
    body_font = load_font(11)
    draw.text((WIDTH // 2, 98), "IINTS MK2", fill=(235, 241, 247), font=title_font, anchor="mm")
    draw.text(
        (WIDTH // 2, 124),
        "Waiting for Pico display",
        fill=(148, 163, 184),
        font=body_font,
        anchor="mm",
    )
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


latest_png = create_placeholder()
latest_frame_version = 0
frame_condition = threading.Condition()

status_lock = threading.Lock()
mirror_status = {
    "state": "searching",
    "message": "Searching for Raspberry Pi Pico",
    "port": "",
    "frames": 0,
    "fps": 0.0,
    "answers": 0,
    "answers_per_second": 0.0,
    "response_ms": 0.0,
    "kilobytes_per_second": 0.0,
    "changed_band_percent": 0.0,
    "pico_free_bytes": None,
    "last_frame_at": None,
    "last_answer_at": None,
}


def set_status(state: str, message: str, port: str = ""):
    with status_lock:
        mirror_status["state"] = state
        mirror_status["message"] = message
        mirror_status["port"] = port


def status_snapshot():
    with status_lock:
        result = dict(mirror_status)
    result.pop("last_answer_at")
    last_frame_at = result.pop("last_frame_at")
    result["last_frame_age"] = (
        None if last_frame_at is None else max(0.0, time.monotonic() - last_frame_at)
    )
    return result


def find_pico_port(preferred_port: str | None = None):
    if preferred_port:
        return preferred_port
    for port in serial.tools.list_ports.comports():
        if (
            "usbmodem" in port.device
            or "MicroPython" in port.description
            or port.vid == 0x2E8A
        ):
            return port.device
    return None


def rgb565_to_image(raw_frame: bytes) -> Image.Image:
    """Turn the display's big-endian RGB565 bytes into an RGB image.

    Pillow's raw "BGR;16" decoder reads little-endian RGB565, so the byte pairs
    are swapped first with a C-speed strided copy. That is roughly seven times
    faster than converting pixel by pixel in Python.
    """
    swapped = bytearray(len(raw_frame))
    swapped[0::2] = raw_frame[1::2]
    swapped[1::2] = raw_frame[0::2]
    return Image.frombytes("RGB", (WIDTH, HEIGHT), bytes(swapped), "raw", "BGR;16")


class DeltaFrame:
    __slots__ = ("sequence", "pico_free_bytes", "changed_bands", "band_count", "payload_bytes")

    def __init__(self, sequence, pico_free_bytes, changed_bands, band_count, payload_bytes):
        self.sequence = sequence
        self.pico_free_bytes = pico_free_bytes
        self.changed_bands = changed_bands
        self.band_count = band_count
        self.payload_bytes = payload_bytes


class FrameParser:
    """Parse banded delta frames from a noisy serial stream into a canvas."""

    def __init__(self):
        self.buffer = bytearray()
        self.canvas = bytearray(FRAME_BYTES)
        self.invalid_frames = 0
        self.complete = False

    def reset(self):
        """Drop everything; the next frame from the Pico is a full keyframe."""
        self.buffer.clear()
        self.complete = False

    def feed(self, data: bytes):
        self.buffer.extend(data)
        frames = []

        while True:
            magic_index = self.buffer.find(MIRROR_MAGIC)
            if magic_index < 0:
                keep = len(MIRROR_MAGIC) - 1
                if len(self.buffer) > keep:
                    del self.buffer[:-keep]
                break
            if magic_index:
                del self.buffer[:magic_index]
            if len(self.buffer) < HEADER.size:
                break

            (
                magic,
                version,
                band_count,
                band_rows,
                sequence,
                payload_bytes,
                pico_free_bytes,
            ) = HEADER.unpack_from(self.buffer)

            band_bytes = band_rows * WIDTH * 2
            mask_bytes = (band_count + 7) // 8
            if (
                magic != MIRROR_MAGIC
                or version != MIRROR_PROTOCOL_VERSION
                or band_count == 0
                or band_rows == 0
                or band_rows * band_count != HEIGHT
                or payload_bytes > FRAME_BYTES
                or payload_bytes % band_bytes
            ):
                del self.buffer[0]
                self.invalid_frames += 1
                continue

            frame_end = HEADER.size + mask_bytes + payload_bytes + 4
            if len(self.buffer) < frame_end:
                break

            mask_start = HEADER.size
            payload_start = mask_start + mask_bytes
            payload_end = payload_start + payload_bytes
            checksum = struct.unpack_from("<I", self.buffer, payload_end)[0]
            if zlib.crc32(memoryview(self.buffer)[mask_start:payload_end]) & 0xFFFFFFFF != checksum:
                del self.buffer[0]
                self.invalid_frames += 1
                continue

            mask = bytes(self.buffer[mask_start:payload_start])
            selected_bands = sum(byte.bit_count() for byte in mask)
            unused_bits = band_count % 8
            if (
                selected_bands * band_bytes != payload_bytes
                or (unused_bits and mask[-1] >> unused_bits)
            ):
                del self.buffer[:frame_end]
                self.invalid_frames += 1
                self.complete = False
                continue
            changed_bands = 0
            source = payload_start
            for band in range(band_count):
                if not (mask[band >> 3] >> (band & 7)) & 1:
                    continue
                target = band * band_bytes
                self.canvas[target : target + band_bytes] = self.buffer[source : source + band_bytes]
                source += band_bytes
                changed_bands += 1

            del self.buffer[:frame_end]
            if changed_bands == band_count:
                self.complete = True
            if self.complete:
                frames.append(
                    DeltaFrame(sequence, pico_free_bytes, changed_bands, band_count, payload_bytes)
                )

        return frames


def publish_frame(raw_frame: bytes):
    global latest_png, latest_frame_version

    output = io.BytesIO()
    rgb565_to_image(raw_frame).save(output, format="PNG", compress_level=PNG_COMPRESS_LEVEL)
    png = output.getvalue()

    with frame_condition:
        latest_png = png
        latest_frame_version += 1
        frame_condition.notify_all()


def record_answer(frame: DeltaFrame, wire_bytes: int, round_trip: float):
    now = time.monotonic()
    rendered = bool(frame.payload_bytes)
    with status_lock:
        mirror_status["state"] = "live"
        mirror_status["message"] = "Live Pico display"
        mirror_status["pico_free_bytes"] = frame.pico_free_bytes
        mirror_status["answers"] += 1
        mirror_status["response_ms"] = round_trip * 1000.0

        previous_answer_at = mirror_status["last_answer_at"]
        if previous_answer_at is not None:
            rate = 1.0 / max(0.001, now - previous_answer_at)
            old_rate = float(mirror_status["answers_per_second"])
            mirror_status["answers_per_second"] = (
                rate if old_rate == 0.0 else old_rate * 0.9 + rate * 0.1
            )
        mirror_status["last_answer_at"] = now

        if not rendered:
            # The screen did not change, so this is not a new frame.
            return

        previous_frame_at = mirror_status["last_frame_at"]
        elapsed = None if previous_frame_at is None else max(0.001, now - previous_frame_at)

        if elapsed is not None:
            instant_fps = 1.0 / elapsed
            old_fps = float(mirror_status["fps"])
            mirror_status["fps"] = (
                instant_fps if old_fps == 0.0 else old_fps * 0.75 + instant_fps * 0.25
            )
            instant_rate = wire_bytes / 1024.0 / elapsed
            old_rate = float(mirror_status["kilobytes_per_second"])
            mirror_status["kilobytes_per_second"] = (
                instant_rate if old_rate == 0.0 else old_rate * 0.75 + instant_rate * 0.25
            )

        band_percent = 100.0 * frame.changed_bands / frame.band_count
        old_percent = float(mirror_status["changed_band_percent"])
        mirror_status["changed_band_percent"] = (
            band_percent if mirror_status["frames"] == 0 else old_percent * 0.8 + band_percent * 0.2
        )
        mirror_status["frames"] += 1
        mirror_status["last_frame_at"] = now
        rendered_frames = mirror_status["frames"]
        fps = mirror_status["fps"]
        rate = mirror_status["kilobytes_per_second"]

    if rendered_frames % 50 == 0:
        print(
            "Frame {}: {}/{} bands, {:.1f} fps, {:.0f} KB/s, Pico free RAM {:.1f} KB".format(
                rendered_frames,
                frame.changed_bands,
                frame.band_count,
                fps,
                rate,
                frame.pico_free_bytes / 1024,
            ),
            flush=True,
        )


def serial_reader_thread(preferred_port: str | None = None):
    while True:
        port = find_pico_port(preferred_port)
        if not port:
            set_status("searching", "Raspberry Pi Pico not found")
            time.sleep(RECONNECT_DELAY_SECONDS)
            continue

        try:
            set_status("connecting", "Connecting to Pico", port)
            with serial.Serial(port, 115200, timeout=0, write_timeout=0.5) as connection:
                connection.reset_input_buffer()
                parser = FrameParser()
                awaiting_frame = False
                request_started = 0.0
                wire_bytes = 0
                next_request = MIRROR_RESET_REQUEST
                next_request_at = time.monotonic()
                set_status("waiting", "Pico found, waiting for display frame", port)
                print("Connected to {}".format(port), flush=True)

                while True:
                    now = time.monotonic()
                    if not awaiting_frame and now >= next_request_at:
                        connection.write(next_request)
                        connection.flush()
                        next_request = MIRROR_REQUEST
                        awaiting_frame = True
                        request_started = now

                    chunk = connection.read(SERIAL_READ_BYTES)
                    if not chunk:
                        time.sleep(0.001)
                    else:
                        wire_bytes += len(chunk)
                        invalid_before = parser.invalid_frames
                        frames = parser.feed(chunk)
                        if parser.invalid_frames != invalid_before:
                            # Re-sync from a clean full frame.
                            parser.reset()
                            next_request = MIRROR_RESET_REQUEST
                            awaiting_frame = False
                            next_request_at = time.monotonic()
                        elif frames:
                            frame = frames[-1]
                            # Ask for the next frame before rendering this one, so
                            # the Pico redraws while the desktop encodes the PNG.
                            awaiting_frame = False
                            next_request_at = time.monotonic() + (
                                0.0 if frame.payload_bytes else IDLE_REQUEST_INTERVAL_SECONDS
                            )
                            if frame.payload_bytes:
                                publish_frame(bytes(parser.canvas))
                            record_answer(frame, wire_bytes, time.monotonic() - request_started)
                            wire_bytes = 0

                    if awaiting_frame and time.monotonic() - request_started > FRAME_TIMEOUT_SECONDS:
                        # The pump sleeps its screen or runs a long animation
                        # without servicing the mirror. It will answer again by
                        # itself, so keep the port and simply ask once more.
                        set_status("waiting", "Pico display is off or busy", port)
                        parser.reset()
                        next_request = MIRROR_RESET_REQUEST
                        awaiting_frame = False
                        next_request_at = time.monotonic() + RETRY_DELAY_SECONDS

        except (OSError, serial.SerialException) as error:
            message = str(error) or type(error).__name__
            if "readiness to read" in message:
                # The USB serial link drops while the pump is in power save.
                set_status("waiting", "Pico is in power save, waiting for wake-up", port)
            else:
                set_status("error", message, port)
                print("Mirror connection error: {}".format(message), flush=True)
            time.sleep(RECONNECT_DELAY_SECONDS)


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>IINTS MK2 Live Display</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #0d1117;
      color: #e6edf3;
    }
    main { width: min(92vw, 640px); padding: 24px 0; }
    header {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 14px;
    }
    h1 { margin: 0; font-size: 18px; letter-spacing: 0; }
    header span { color: #8b949e; font-size: 13px; }
    .screen {
      width: 100%;
      aspect-ratio: 1;
      overflow: hidden;
      border: 1px solid #30363d;
      border-radius: 8px;
      background: #000;
      box-shadow: 0 18px 50px rgba(0, 0, 0, 0.45);
    }
    .screen img {
      display: block;
      width: 100%;
      height: 100%;
      object-fit: contain;
      image-rendering: pixelated;
    }
    .status {
      display: flex;
      align-items: center;
      gap: 9px;
      min-height: 24px;
      margin-top: 14px;
      color: #8b949e;
      font-size: 13px;
    }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: #d29922; flex: 0 0 auto; }
    .dot.live { background: #3fb950; }
    .dot.error { background: #f85149; }
    #stats { margin-left: auto; white-space: nowrap; }
    @media (max-width: 520px) {
      main { width: min(94vw, 640px); padding: 14px 0; }
      header { margin-bottom: 10px; }
      #stats { display: none; }
    }
  </style>
</head>
<body>
  <main>
    <header><h1>IINTS MK2</h1><span>Live display mirror</span></header>
    <div class="screen"><img id="frame" alt="Live Pico display"></div>
    <div class="status">
      <span id="dot" class="dot"></span>
      <span id="message">Starting mirror</span>
      <span id="stats"></span>
    </div>
  </main>
  <script>
    const frame = document.getElementById('frame');
    const dot = document.getElementById('dot');
    const message = document.getElementById('message');
    const stats = document.getElementById('stats');

    let shownVersion = null;
    let imageUrl = null;
    async function refreshFrame() {
      try {
        const response = await fetch('/frame.png', {
          cache: 'no-store', signal: AbortSignal.timeout(2000)
        });
        if (!response.ok) throw new Error('Frame unavailable');
        const version = response.headers.get('X-IINTS-Frame');
        const blob = await response.blob();
        if (version !== shownVersion) {
          const nextUrl = URL.createObjectURL(blob);
          const previousUrl = imageUrl;
          frame.src = nextUrl;
          imageUrl = nextUrl;
          shownVersion = version;
          if (previousUrl) URL.revokeObjectURL(previousUrl);
        }
      } catch (_error) {
        // Retry without queuing requests or replacing the last valid image.
      } finally {
        setTimeout(refreshFrame, 40);
      }
    }
    refreshFrame();

    async function refreshStatus() {
      try {
        const response = await fetch('/status', { cache: 'no-store' });
        const state = await response.json();
        dot.className = 'dot ' + (state.state === 'live' ? 'live' : state.state === 'error' ? 'error' : '');
        message.textContent = state.message;
        const memory = state.pico_free_bytes == null ? '' : ' | Pico RAM ' + (state.pico_free_bytes / 1024).toFixed(1) + ' KB';
        // Frames only arrive when the pump actually redraws, so show how
        // responsive the link is as well; that is the real health signal.
        const link = state.answers
          ? state.answers_per_second.toFixed(0) + ' checks/s | ' + state.response_ms.toFixed(0) + ' ms'
          : '';
        const motion = state.frames
          ? state.fps.toFixed(1) + ' fps | ' + state.kilobytes_per_second.toFixed(0) + ' KB/s | '
            + state.changed_band_percent.toFixed(0) + '% screen | '
          : '';
        stats.textContent = state.answers ? motion + link + memory : '';
      } catch (_error) {
        dot.className = 'dot error';
        message.textContent = 'Mirror server unavailable';
        stats.textContent = '';
      }
    }

    setInterval(refreshStatus, 500);
    refreshStatus();
  </script>
</body>
</html>
""".encode("utf-8")

STREAM_BOUNDARY = "iintsframe"


class MirrorHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, _format, *_args):
        return

    def send_bytes(self, data: bytes, content_type: str):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def stream_frames(self):
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "multipart/x-mixed-replace; boundary={}".format(STREAM_BOUNDARY),
        )
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Connection", "close")
        self.close_connection = True
        self.end_headers()
        if self.command == "HEAD":
            return

        sent_version = -1
        try:
            while True:
                with frame_condition:
                    if latest_frame_version == sent_version:
                        frame_condition.wait(timeout=STREAM_KEEPALIVE_SECONDS)
                    png = latest_png
                    sent_version = latest_frame_version
                self.wfile.write(
                    "--{}\r\nContent-Type: image/png\r\nContent-Length: {}\r\n\r\n".format(
                        STREAM_BOUNDARY, len(png)
                    ).encode("ascii")
                )
                self.wfile.write(png)
                self.wfile.write(b"\r\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self.send_bytes(INDEX_HTML, "text/html; charset=utf-8")
            return
        if path == "/stream":
            self.stream_frames()
            return
        if path == "/frame.png":
            with frame_condition:
                frame = latest_png
                version = latest_frame_version
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(frame)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("X-IINTS-Frame", str(version))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(frame)
            return
        if path == "/status":
            payload = json.dumps(status_snapshot()).encode("utf-8")
            self.send_bytes(payload, "application/json; charset=utf-8")
            return
        if path == "/favicon.ico":
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_error(404)


def find_available_http_port(start_port: int):
    for port in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            if probe.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No available local HTTP port found")


def parse_args():
    parser = argparse.ArgumentParser(description="Mirror the IINTS MK2 Pico display in a browser")
    parser.add_argument("--port", help="Pico serial port; auto-detected when omitted")
    parser.add_argument("--http-port", type=int, default=8082)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    serial_thread = threading.Thread(
        target=serial_reader_thread,
        args=(args.port,),
        daemon=True,
    )
    serial_thread.start()

    http_port = find_available_http_port(args.http_port)
    server = ThreadingHTTPServer(("127.0.0.1", http_port), MirrorHandler)
    server.daemon_threads = True
    url = "http://127.0.0.1:{}".format(http_port)
    print("IINTS MK2 live mirror: {}".format(url), flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
