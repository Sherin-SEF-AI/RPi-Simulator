"""
GPIO Pin definitions and management
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass


class PinMode(Enum):
    """GPIO pin modes"""
    INPUT = "input"
    OUTPUT = "output"
    ALT0 = "alt0"  # Alternative function 0
    ALT1 = "alt1"
    ALT2 = "alt2"
    ALT3 = "alt3"
    ALT4 = "alt4"
    ALT5 = "alt5"


class PinFunction(Enum):
    """GPIO alternative functions"""
    GPIO = "gpio"
    I2C_SDA = "i2c_sda"
    I2C_SCL = "i2c_scl"
    SPI_MOSI = "spi_mosi"
    SPI_MISO = "spi_miso"
    SPI_SCLK = "spi_sclk"
    SPI_CE0 = "spi_ce0"
    SPI_CE1 = "spi_ce1"
    UART_TX = "uart_tx"
    UART_RX = "uart_rx"
    PWM0 = "pwm0"
    PWM1 = "pwm1"
    PCM_CLK = "pcm_clk"
    PCM_FS = "pcm_fs"
    PCM_DIN = "pcm_din"
    PCM_DOUT = "pcm_dout"


@dataclass
class PinDefinition:
    """Pin definition with alternative functions"""
    bcm_num: int
    board_num: int
    name: str
    alt_functions: Dict[PinMode, PinFunction]
    power_pin: bool = False
    ground_pin: bool = False


class GpioPin:
    """
    Individual GPIO pin with state management
    """
    
    def __init__(self, definition: PinDefinition):
        self.definition = definition
        self.mode = PinMode.INPUT
        self.value = 0
        self.pull_up = False
        self.pull_down = False
        self.function = PinFunction.GPIO
        
        # Event callbacks
        self._edge_callbacks: List[callable] = []
        
    @property
    def bcm_num(self) -> int:
        """BCM GPIO number"""
        return self.definition.bcm_num
        
    @property
    def board_num(self) -> int:
        """Board pin number (1-40)"""
        return self.definition.board_num
        
    @property
    def name(self) -> str:
        """Pin name/label"""
        return self.definition.name
        
    @property
    def is_power(self) -> bool:
        """True if this is a power pin"""
        return self.definition.power_pin
        
    @property
    def is_ground(self) -> bool:
        """True if this is a ground pin"""
        return self.definition.ground_pin
        
    @property
    def is_gpio(self) -> bool:
        """True if pin can be used as GPIO"""
        return not (self.is_power or self.is_ground)
        
    def set_mode(self, mode: PinMode) -> None:
        """Set pin mode"""
        if not self.is_gpio:
            raise ValueError(f"Pin {self.name} is not a GPIO pin")
            
        self.mode = mode
        
        # Set function based on mode
        if mode in self.definition.alt_functions:
            self.function = self.definition.alt_functions[mode]
        else:
            self.function = PinFunction.GPIO
            
    def set_pull(self, pull_up: bool = False, pull_down: bool = False) -> None:
        """Set pull-up/pull-down resistors"""
        if pull_up and pull_down:
            raise ValueError("Cannot enable both pull-up and pull-down")
            
        self.pull_up = pull_up
        self.pull_down = pull_down
        
    def get_effective_value(self) -> int:
        """Get effective pin value considering pulls"""
        if self.mode == PinMode.INPUT:
            if self.pull_up and self.value == 0:
                return 1  # Pull-up overrides low input
            elif self.pull_down and self.value == 1:
                return 0  # Pull-down overrides high input
                
        return self.value
        
    def on_edge(self, callback: callable) -> None:
        """Register edge detection callback"""
        self._edge_callbacks.append(callback)
        
    def _trigger_edge(self, old_value: int, new_value: int) -> None:
        """Trigger edge callbacks"""
        for callback in self._edge_callbacks:
            try:
                callback(self, old_value, new_value)
            except Exception as e:
                print(f"Edge callback error: {e}")


# Standard Raspberry Pi pin definitions
PI_PIN_DEFINITIONS = [
    # Power and Ground pins
    PinDefinition(0, 1, "3V3", {}, power_pin=True),
    PinDefinition(0, 2, "5V", {}, power_pin=True),
    PinDefinition(0, 4, "5V", {}, power_pin=True),
    PinDefinition(0, 6, "GND", {}, ground_pin=True),
    PinDefinition(0, 9, "GND", {}, ground_pin=True),
    PinDefinition(0, 14, "GND", {}, ground_pin=True),
    PinDefinition(0, 17, "3V3", {}, power_pin=True),
    PinDefinition(0, 20, "GND", {}, ground_pin=True),
    PinDefinition(0, 25, "GND", {}, ground_pin=True),
    PinDefinition(0, 30, "GND", {}, ground_pin=True),
    PinDefinition(0, 34, "GND", {}, ground_pin=True),
    PinDefinition(0, 39, "GND", {}, ground_pin=True),
    
    # GPIO pins with alternative functions
    PinDefinition(2, 3, "GPIO2", {
        PinMode.ALT0: PinFunction.I2C_SDA
    }),
    PinDefinition(3, 5, "GPIO3", {
        PinMode.ALT0: PinFunction.I2C_SCL
    }),
    PinDefinition(4, 7, "GPIO4", {}),
    PinDefinition(5, 29, "GPIO5", {}),
    PinDefinition(6, 31, "GPIO6", {}),
    PinDefinition(7, 26, "GPIO7", {
        PinMode.ALT0: PinFunction.SPI_CE1
    }),
    PinDefinition(8, 24, "GPIO8", {
        PinMode.ALT0: PinFunction.SPI_CE0
    }),
    PinDefinition(9, 21, "GPIO9", {
        PinMode.ALT0: PinFunction.SPI_MISO
    }),
    PinDefinition(10, 19, "GPIO10", {
        PinMode.ALT0: PinFunction.SPI_MOSI
    }),
    PinDefinition(11, 23, "GPIO11", {
        PinMode.ALT0: PinFunction.SPI_SCLK
    }),
    PinDefinition(12, 32, "GPIO12", {
        PinMode.ALT0: PinFunction.PWM0
    }),
    PinDefinition(13, 33, "GPIO13", {
        PinMode.ALT0: PinFunction.PWM1
    }),
    PinDefinition(14, 8, "GPIO14", {
        PinMode.ALT0: PinFunction.UART_TX
    }),
    PinDefinition(15, 10, "GPIO15", {
        PinMode.ALT0: PinFunction.UART_RX
    }),
    PinDefinition(16, 36, "GPIO16", {}),
    PinDefinition(17, 11, "GPIO17", {}),
    PinDefinition(18, 12, "GPIO18", {
        PinMode.ALT5: PinFunction.PWM0
    }),
    PinDefinition(19, 35, "GPIO19", {
        PinMode.ALT5: PinFunction.PWM1
    }),
    PinDefinition(20, 38, "GPIO20", {}),
    PinDefinition(21, 40, "GPIO21", {}),
    PinDefinition(22, 15, "GPIO22", {}),
    PinDefinition(23, 16, "GPIO23", {}),
    PinDefinition(24, 18, "GPIO24", {}),
    PinDefinition(25, 22, "GPIO25", {}),
    PinDefinition(26, 37, "GPIO26", {}),
    PinDefinition(27, 13, "GPIO27", {}),
]