"""
SPI Controller - Serial Peripheral Interface
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from sim_core import EventBus, Event, EventType


class SpiDevice:
    """Base class for SPI devices"""
    
    def __init__(self, name: str = ""):
        self.name = name
        
    def transfer(self, data: List[int]) -> List[int]:
        """
        Handle SPI transfer (simultaneous read/write)
        
        Args:
            data: Bytes to write
            
        Returns:
            Bytes read during transfer
        """
        return [0] * len(data)  # Default: return zeros


@dataclass
class SpiTransaction:
    """SPI transaction record"""
    timestamp: float
    device: int
    data_out: List[int]
    data_in: List[int]
    clock_freq: int
    mode: int


class SpiController:
    """
    SPI controller with protocol-accurate timing
    """
    
    def __init__(self, bus_id: int, event_bus: EventBus):
        self.bus_id = bus_id
        self.event_bus = event_bus
        
        # SPI configuration
        self.clock_freq = 1000000  # 1 MHz default
        self.mode = 0              # SPI mode (0-3)
        self.bits_per_word = 8
        
        # Connected devices (by chip select)
        self.devices: Dict[int, SpiDevice] = {}
        
        # Transaction history
        self.transactions: List[SpiTransaction] = []
        
    def add_device(self, device: SpiDevice, chip_select: int = 0) -> None:
        """Add SPI device"""
        self.devices[chip_select] = device
        
    def remove_device(self, chip_select: int) -> None:
        """Remove SPI device"""
        if chip_select in self.devices:
            del self.devices[chip_select]
            
    def set_clock_freq(self, freq: int) -> None:
        """Set SPI clock frequency"""
        self.clock_freq = max(1000, min(32000000, freq))  # 1kHz to 32MHz
        
    def set_mode(self, mode: int) -> None:
        """Set SPI mode (0-3)"""
        self.mode = mode & 0x3
        
    def transfer(self, data: List[int], chip_select: int = 0, 
                timestamp: float = 0.0) -> Optional[List[int]]:
        """
        Perform SPI transfer
        
        Args:
            data: Data bytes to send
            chip_select: Chip select line (0 or 1)
            timestamp: Transaction start time
            
        Returns:
            Data bytes received, or None if no device
        """
        device = self.devices.get(chip_select)
        if not device:
            return None
            
        # Simulate transfer timing
        bit_time = 1.0 / self.clock_freq
        transfer_time = len(data) * 8 * bit_time
        
        # Perform transfer
        received_data = device.transfer(data)
        
        # Record transaction
        transaction = SpiTransaction(
            timestamp=timestamp,
            device=chip_select,
            data_out=data.copy(),
            data_in=received_data.copy(),
            clock_freq=self.clock_freq,
            mode=self.mode
        )
        self.transactions.append(transaction)
        
        # Publish event
        self.event_bus.publish(Event(
            type=EventType.SPI_TRANSACTION,
            timestamp=timestamp,
            source=f"SPI{self.bus_id}",
            data={
                "device": chip_select,
                "data_out": data,
                "data_in": received_data,
                "clock_freq": self.clock_freq,
                "mode": self.mode,
                "duration": transfer_time
            }
        ))
        
        return received_data
        
    def get_device(self, chip_select: int) -> Optional[SpiDevice]:
        """Get device by chip select"""
        return self.devices.get(chip_select)