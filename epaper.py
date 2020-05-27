'''

SSD1619A EPD IC Framebuf-derived Display Driver for MicroPython

Written by Thomas Wilkinson - github.com/T-Wilko

'''

from micropython import const
from machine import SPI, Pin
from time import sleep_ms
import ustruct, framebuf

DRIVER_CTRL            = const(0x01)
GATE_SCAN_START        = const(0x0F)
DATA_ENTRY_MODE        = const(0x11)
RAM_X_ADDRESS          = const(0x44)
RAM_Y_ADDRESS          = const(0x45)
SET_RAM_COUNTER_X      = const(0x4E)
SET_RAM_COUNTER_Y      = const(0x4F)
SOFT_RESET             = const(0x12)
MASTER_ACTIVATION      = const(0x20)
DISP_UPDATE_1          = const(0x21)
DISP_UPDATE_2          = const(0x22)
WRITE_RAM_BW           = const(0x24)
WRITE_RAM_RED          = const(0x26)


class EPD(framebuf.FrameBuffer):
    def __init__(self, spi, dc, cs, rst, busy, width, height):
        
        self.spi = spi
        #self.spi = SPI(1, 10000000, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
        self.spi.init()
        self.dc = Pin(dc)
        self.cs = Pin(cs)
        self.rst = Pin(rst)
        self.busy = Pin(busy)
        
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.busy.init(self.busy.IN)
        self.width = width
        self.height = height
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()
    
    
    def init_display(self):
        
        # SW reset
        self._command(SOFT_RESET)
        self.wait_until_idle()
        
        # Set analogue then digital block control
        self._command('b\x74','b\x54')
        self._command('b\x7E','b\x3B')
        
        # Set driver output control
        self._command(DRIVER_CTRL)
        # Set dummy line period, gate line width, waveform control
        self._command('b\x3A')
        self._command('b\x3B')
        self._command('b\x3C')
        
        # Set RAM start/end positions
        self._command(RAM_X_ADDRESS)
        self._command(RAM_Y_ADDRESS)
        self._command(SET_RAM_COUNTER_X)
        self._command(SET_RAM_COUNTER_Y)
        
        
    def _command(self, command, data=None):
        self.cs(1) # according to LOLIN_EPD
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.cs(1) # according to LOLIN_EPD
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)
    
    def wait_until_idle(self):
        while self.busy == 1:
            pass
        return

    def reset(self):
        self.rst(1)
        sleep_ms(1)

        self.rst(0)
        sleep_ms(10)

        self.rst(1)
        

class EPD_RED(EPD):
    
    def write(self):
        self._command(WRITE_RAM_RED)
        self._data(self.buffer)
    
    def show(self):
        self._command(DISP_UPDATE_2)
        self._command(MASTER_ACTIVATION)
        self.wait_until_idle()

class EPD_BW(EPD):
    
    def write(self):
        self._command(WRITE_RAM_BW)
        self._data(self.buffer)
    
    def show(self):
        self._command(DISP_UPDATE_2)
        self._command(MASTER_ACTIVATION)
        self.wait_until_idle()
    