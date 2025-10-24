"""
UART Controller - Universal Asynchronous Receiver-Transmitter
"""

import queue
import threading
from typing import Optional, List, Callable
from dataclasses import dataclass
from sim_core import EventBus, Event, EventType


@dataclass
class UartConfig:
    """UART configuration parameters"""
    baud_rate: int = 9600
    data_bits: int = 8
    parity: str = "none"  # "none", "even", "odd"
    stop_bits: int = 1
    flow_control: bool = False


class UartController:
    """
    UART controller with configurable parameters and error injection
    """
    
    def __init__(self, port: int, event_bus: EventBus, config: Optional[UartConfig] = None):
        self.port = port
        self.event_bus = event_bus
        self.config = config or UartConfig()
        
        # Buffers
        self.tx_buffer = queue.Queue(maxsize=1024)
        self.rx_buffer = queue.Queue(maxsize=1024)
        
        # State
        self.open = False
        self.tx_pin = 14  # GPIO14 - UART TX
        self.rx_pin = 15  # GPIO15 - UART RX
        
        # Callbacks
        self.data_received_callback: Optional[Callable] = None
        
        # Error injection
        self.error_rate = 0.0  # Probability of bit errors
        
    def open_port(self) -> bool:
        """Open UART port"""
        if self.open:
            return True
            
        self.open = True
        
        # Clear buffers
        while not self.tx_buffer.empty():
            self.tx_buffer.get()
        while not self.rx_buffer.empty():
            self.rx_buffer.get()
            
        return True
        
    def close_port(self) -> None:
        """Close UART port"""
        self.open = False
        
    def configure(self, config: UartConfig) -> None:
        """Configure UART parameters"""
        self.config = config
        
    def write(self, data: bytes, timestamp: float = 0.0) -> int:
        """
        Write data to UART
        
        Args:
            data: Data bytes to send
            timestamp: Transmission start time
            
        Returns:
            Number of bytes written
        """
        if not self.open:
            return 0
            
        bytes_written = 0
        
        for byte in data:
            if not self.tx_buffer.full():
                self.tx_buffer.put(byte)
                bytes_written += 1
                
                # Simulate transmission timing
                bit_time = 1.0 / self.config.baud_rate
                frame_bits = (1 +  # Start bit
                            self.config.data_bits +
                            (1 if self.config.parity != "none" else 0) +
                            self.config.stop_bits)
                transmission_time = frame_bits * bit_time
                
                # Publish event
                self.event_bus.publish(Event(
                    type=EventType.UART_DATA,
                    timestamp=timestamp,
                    source=f"UART{self.port}",
                    data={
                        "direction": "tx",
                        "data": byte,
                        "baud_rate": self.config.baud_rate,
                        "duration": transmission_time
                    }
                ))
                
        return bytes_written
        
    def read(self, max_bytes: int = 1) -> bytes:
        """
        Read data from UART
        
        Args:
            max_bytes: Maximum bytes to read
            
        Returns:
            Received data bytes
        """
        if not self.open:
            return b""
            
        data = []
        
        for _ in range(max_bytes):
            try:
                byte = self.rx_buffer.get_nowait()
                data.append(byte)
            except queue.Empty:
                break
                
        return bytes(data)
        
    def available(self) -> int:
        """Get number of bytes available to read"""
        return self.rx_buffer.qsize()
        
    def inject_data(self, data: bytes, timestamp: float = 0.0) -> None:
        """
        Inject received data (for simulation)
        
        Args:
            data: Data bytes received
            timestamp: Reception time
        """
        if not self.open:
            return
            
        for byte in data:
            # Apply error injection
            if self.error_rate > 0:
                import random
                if random.random() < self.error_rate:
                    # Flip a random bit
                    bit_pos = random.randint(0, 7)
                    byte ^= (1 << bit_pos)
                    
            if not self.rx_buffer.full():
                self.rx_buffer.put(byte)
                
                # Publish event
                self.event_bus.publish(Event(
                    type=EventType.UART_DATA,
                    timestamp=timestamp,
                    source=f"UART{self.port}",
                    data={
                        "direction": "rx",
                        "data": byte,
                        "baud_rate": self.config.baud_rate
                    }
                ))
                
                # Call callback if set
                if self.data_received_callback:
                    self.data_received_callback(byte)
                    
    def set_error_rate(self, rate: float) -> None:
        """Set bit error rate (0.0 to 1.0)"""
        self.error_rate = max(0.0, min(1.0, rate))
        
    def on_data_received(self, callback: Callable[[int], None]) -> None:
        """Set callback for received data"""
        self.data_received_callback = callback
        
    def flush_tx(self) -> None:
        """Flush transmit buffer"""
        while not self.tx_buffer.empty():
            self.tx_buffer.get()
            
    def flush_rx(self) -> None:
        """Flush receive buffer"""
        while not self.rx_buffer.empty():
            self.rx_buffer.get()