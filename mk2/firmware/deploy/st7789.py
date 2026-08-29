import utime
from machine import Pin


class ST7789:
    SWRESET = 0x01
    SLPOUT = 0x11
    NORON = 0x13
    INVOFF = 0x20
    INVON = 0x21
    DISPON = 0x29
    CASET = 0x2A
    RASET = 0x2B
    RAMWR = 0x2C
    MADCTL = 0x36
    COLMOD = 0x3A

    def __init__(self, spi, width, height, reset=None, dc=None, cs=None, xstart=0, ystart=0, rotation=0, inversion=True):
        self.spi = spi
        self.width = width
        self.height = height
        self.reset_pin = reset
        self.dc = dc
        self.cs = cs
        self.xstart = xstart
        self.ystart = ystart
        self.rotation = rotation
        self.inversion = inversion

        if self.cs:
            self.cs.init(Pin.OUT, value=1)
        if self.dc:
            self.dc.init(Pin.OUT, value=0)
        if self.reset_pin:
            self.reset_pin.init(Pin.OUT, value=1)

    def _write(self, command=None, data=None):
        if self.cs:
            self.cs.value(0)
        if command is not None:
            self.dc.value(0)
            self.spi.write(bytearray([command]))
        if data is not None:
            self.dc.value(1)
            self.spi.write(data)
        if self.cs:
            self.cs.value(1)

    def _command(self, command):
        self._write(command=command)

    def _data(self, data):
        if isinstance(data, int):
            data = bytearray([data])
        self._write(data=data)

    def hard_reset(self):
        if not self.reset_pin:
            return
        self.reset_pin.value(1)
        utime.sleep_ms(50)
        self.reset_pin.value(0)
        utime.sleep_ms(50)
        self.reset_pin.value(1)
        utime.sleep_ms(150)

    def init(self):
        self.hard_reset()
        self._command(self.SWRESET)
        utime.sleep_ms(150)
        self._command(self.SLPOUT)
        utime.sleep_ms(150)
        self._write(self.COLMOD, bytearray([0x55]))  # 16-bit RGB565
        self._write(self.MADCTL, bytearray([self._madctl_value()]))
        self._command(self.INVON if self.inversion else self.INVOFF)
        self._command(self.NORON)
        utime.sleep_ms(10)
        self._command(self.DISPON)
        utime.sleep_ms(120)

    def _madctl_value(self):
        values = (0x00, 0x60, 0xC0, 0xA0)
        return values[self.rotation % 4]

    def _set_window(self, x0, y0, x1, y1):
        x0 += self.xstart
        x1 += self.xstart
        y0 += self.ystart
        y1 += self.ystart
        self._write(self.CASET, bytearray([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF]))
        self._write(self.RASET, bytearray([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF]))
        self._command(self.RAMWR)

    def blit_buffer(self, buffer, x, y, width, height):
        self._set_window(x, y, x + width - 1, y + height - 1)
        self._data(buffer)

    def fill(self, color):
        high = color >> 8
        low = color & 0xFF
        line = bytearray(self.width * 2)
        for i in range(0, len(line), 2):
            line[i] = high
            line[i + 1] = low
        self._set_window(0, 0, self.width - 1, self.height - 1)
        for _ in range(self.height):
            self._data(line)
