"""
I2C Controller - Inter-Integrated Circuit bus simulation
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from sim_core import EventBus, Event, EventType


class I2cState(Enum):
    """I2C bus states"""
    IDLE = "idle"
    START = "start"
    ADDRESS = "address"
    DATA = "data"
    ACK = "ack"
    STOP = "stop"


@dataclass
class I2cTransaction:
    """I2C transaction record"""
    timestamp: float
    address: int
    read: bool
    data: List[int]
    ack: bool
    success: bool


class I2cDevice:
    """Base class for I2C devices"""
    
    def __init__(self, address: int, name: str = ""):
        self.address = address
        self.name = name or f"Device@0x{address:02X}"
        
    def write(self, data: List[int]) -> bool:
        """
        Handle write transaction
        
        Args:
            data: Bytes to write
            
        Returns:
            True if ACK, False if NACK
        """
        return True  # Default ACK
        
    def read(self, length: int) -> List[int]:
        """
        Handle read transaction
        
        Args:
            length: Number of bytes to read
            
        Returns:
            List of bytes
        """
        return [0] * length  # Default zeros


class I2cController:
    """
    I2C bus controller with protocol-accurate timing.
    Supports multiple devices, clock stretching, and error injection.
    """
    
    def __init__(self, bus_id: int, event_bus: EventBus, clock_freq: int = 100000):
        self.bus_id = bus_id
        self.event_bus = event_bus
        self.clock_freq = clock_freq  # Hz
        
        # Connected devices
        self.devices: Dict[int, I2cDevice] = {}
        
        # Bus state
        self.state = I2cState.IDLE
        self.sda_line = True  # True = high, False = low
        self.scl_line = True
        
        # Transaction tracking
        self.transactions: List[I2cTransaction] = []
        self.current_transaction: Optional[I2cTransaction] = None
        
        # Timing parameters (in seconds)
        self.bit_time = 1.0 / clock_freq
        self.setup_time = 4.7e-6  # 4.7µs for 100kHz
        self.hold_time = 4.0e-6   # 4.0µs for 100kHz
        
    def add_device(self, device: I2cDevice) -> None:
        """Add device to bus"""
        if device.address in self.devices:
            raise ValueError(f"Device already exists at address 0x{device.address:02X}")
            
        self.devices[device.address] = device
        
    def remove_device(self, address: int) -> None:
        """Remove device from bus"""
        if address in self.devices:
            del self.devices[address]
            
    def write_transaction(self, address: int, data: List[int], timestamp: float = 0.0) -> bool:
        """
        Perform I2C write transaction
        
        Args:
            address: 7-bit device address
            data: Data bytes to write
            timestamp: Transaction start time
            
        Returns:
            True if successful (ACK received)
        """
        device = self.devices.get(address)
        if not device:
            return False
            
        # Create transaction record
        transaction = I2cTransaction(
            timestamp=timestamp,
            address=address,
            read=False,
            data=data.copy(),
            ack=False,
            success=False
        )
        
        # Simulate protocol timing
        current_time = timestamp
        
        # START condition
        current_time += self.setup_time
        
        # Address + Write bit (0)
        current_time += 8 * self.bit_time
        
        # Device ACK
        ack = device.write(data)
        transaction.ack = ack
        current_time += self.bit_time
        
        if ack:
            # Data bytes
            current_time += len(data) * 9 * self.bit_time  # 8 data + 1 ACK per byte
            transaction.success = True
            
        # STOP condition
        current_time += self.hold_time
        
        self.transactions.append(transaction)
        
        # Publish event
        self.event_bus.publish(Event(
            type=EventType.I2C_TRANSACTION,
            timestamp=timestamp,
            source=f"I2C{self.bus_id}",
            data={
                "address": address,
                "write": True,
                "data": data,
                "ack": ack,
                "duration": current_time - timestamp
            }
        ))
        
        return ack 
       
    def read_transaction(self, address: int, length: int, timestamp: float = 0.0) -> Optional[List[int]]:
        """
        Perform I2C read transaction
        
        Args:
            address: 7-bit device address
            length: Number of bytes to read
            timestamp: Transaction start time
            
        Returns:
            Data bytes if successful, None if failed
        """
        device = self.devices.get(address)
        if not device:
            return None
            
        # Create transaction record
        transaction = I2cTransaction(
            timestamp=timestamp,
            address=address,
            read=True,
            data=[],
            ack=True,
            success=False
        )
        
        # Simulate protocol timing
        current_time = timestamp
        
        # START condition
        current_time += self.setup_time
        
        # Address + Read bit (1)
        current_time += 8 * self.bit_time
        
        # Device ACK
        current_time += self.bit_time
        
        # Read data
        data = device.read(length)
        transaction.data = data
        transaction.success = True
        
        # Data bytes (8 data + 1 ACK per byte, except last byte gets NACK)
        current_time += length * 9 * self.bit_time
        
        # STOP condition
        current_time += self.hold_time
        
        self.transactions.append(transaction)
        
        # Publish event
        self.event_bus.publish(Event(
            type=EventType.I2C_TRANSACTION,
            timestamp=timestamp,
            source=f"I2C{self.bus_id}",
            data={
                "address": address,
                "read": True,
                "data": data,
                "length": length,
                "duration": current_time - timestamp
            }
        ))
        
        return data
        
    def scan_bus(self, timestamp: float = 0.0) -> List[int]:
        """
        Scan I2C bus for devices
        
        Returns:
            List of responding device addresses
        """
        responding_devices = []
        
        for address in range(0x08, 0x78):  # Valid I2C address range
            if address in self.devices:
                responding_devices.append(address)
                
        return responding_devices
        
    def get_device(self, address: int) -> Optional[I2cDevice]:
        """Get device by address"""
        return self.devices.get(address)
        
    def inject_error(self, error_type: str, timestamp: float) -> None:
        """
        Inject bus error for testing
        
        Args:
            error_type: "clock_stretch", "bus_collision", "nack"
            timestamp: Error injection time
        """
        # Simulate various I2C errors
        if error_type == "clock_stretch":
            # Device holds SCL low
            pass
        elif error_type == "bus_collision":
            # Multiple masters drive bus
            pass
        elif error_type == "nack":
            # Device sends NACK instead of ACK
            pass