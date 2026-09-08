# Live Pico Display

Install the desktop dependencies from `mk2/requirements.txt` and deploy the
matching `mk2/firmware/deploy/pico_app.mpy` to the Pico using the existing loader.
Connect the Pico over USB, then run from the repository root:

```sh
python3 mk2/tools/pico_web_mirror.py --http-port 8082
```

Open http://127.0.0.1:8082. Close other serial clients, such as Thonny, first.
Stop the mirror process before uploading firmware.

The Pico sends changed horizontal bands instead of complete frames. The browser
requests the newest available image every 40 ms, with one request at a time to
avoid a backlog. Checks per second measure link responses, not animation FPS;
unchanged screens do not produce new frames. Full-screen changes take longer.

The desktop validates frame checksums and band lengths and requests a complete
image after a transfer error or reconnection.
