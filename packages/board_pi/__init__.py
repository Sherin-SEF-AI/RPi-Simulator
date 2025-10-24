"""
Raspberry Pi Board Definitions

Provides board profiles, pin mappings, and hardware specifications
for different Raspberry Pi models.
"""

from .boards import PiBoard, Pi3B, Pi4B, PiZero2W
from .pins import PinMode, PinFunction, GpioPin

__all__ = [
    "PiBoard",
    "Pi3B", 
    "Pi4B",
    "PiZero2W",
    "PinMode",
    "PinFunction", 
    "GpioPin"
]