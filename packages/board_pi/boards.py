"""
Raspberry Pi Board Models
"""

from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from .pins import GpioPin, PinDefinition, PI_PIN_DEFINITIONS


class PiBoard(ABC):
    """Base class for Raspberry Pi board models"""
    
    def __init__(self, name: str, cpu: str, ram_mb: int):
        self.name = name
        self.cpu = cpu
        self.ram_mb = ram_mb
        
        # Initialize GPIO pins
        self.pins: Dict[int, GpioPin] = {}
        self._init_pins()
        
    def _init_pins(self) -> None:
        """Initialize GPIO pins from definitions"""
        for pin_def in PI_PIN_DEFINITIONS:
            if pin_def.bcm_num > 0 or pin_def.power_pin or pin_def.ground_pin:
                self.pins[pin_def.board_num] = GpioPin(pin_def)
                
    def get_pin_by_bcm(self, bcm_num: int) -> Optional[GpioPin]:
        """Get pin by BCM GPIO number"""
        for pin in self.pins.values():
            if pin.bcm_num == bcm_num:
                return pin
        return None
        
    def get_pin_by_board(self, board_num: int) -> Optional[GpioPin]:
        """Get pin by board number (1-40)"""
        return self.pins.get(board_num)
        
    @property
    def gpio_pins(self) -> List[GpioPin]:
        """Get all GPIO pins (excluding power/ground)"""
        return [pin for pin in self.pins.values() if pin.is_gpio]


class Pi3B(PiBoard):
    """Raspberry Pi 3 Model B"""
    
    def __init__(self):
        super().__init__(
            name="Raspberry Pi 3 Model B",
            cpu="BCM2837 (ARM Cortex-A53)",
            ram_mb=1024
        )


class Pi4B(PiBoard):
    """Raspberry Pi 4 Model B"""
    
    def __init__(self, ram_mb: int = 4096):
        super().__init__(
            name=f"Raspberry Pi 4 Model B ({ram_mb}MB)",
            cpu="BCM2711 (ARM Cortex-A72)",
            ram_mb=ram_mb
        )


class PiZero2W(PiBoard):
    """Raspberry Pi Zero 2 W"""
    
    def __init__(self):
        super().__init__(
            name="Raspberry Pi Zero 2 W",
            cpu="BCM2710A1 (ARM Cortex-A53)",
            ram_mb=512
        )