"""
Protocol Decoders - Decode digital communication protocols
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ProtocolEvent(Enum):
    """Protocol event types"""
    START = "start"
    STOP = "stop"
    DATA = "data"
    ADDRESS = "address"
    ACK = "ack"
    NACK = "nack"
    ERROR = "error"


@dataclass
class DecodedFrame:
    """Decoded protocol frame"""
    start_time: float
    end_time: float
    event_type: ProtocolEvent
    data: Any
    description: str
    error: Optional[str] = None


class ProtocolDecoder(ABC):
    """Base class for protocol decoders"""
    
    def __init__(self, name: str):
        self.name = name
        self.frames: List[DecodedFrame] = []
        
    @abstractmethod
    def decode(self, signals: Dict[str, Tuple[np.ndarray, np.ndarray]]) -> List[DecodedFrame]:
        """Decode protocol from signal data"""
        pass
        
    def clear(self) -> None:
        """Clear decoded frames"""
        self.frames.clear()
        
    def get_frames(self, start_time: float = 0, end_time: Optional[float] = None) -> List[DecodedFrame]:
        """Get frames within time range"""
        if end_time is None:
            return [f for f in self.frames if f.start_time >= start_time]
        else:
            return [f for f in self.frames if start_time <= f.start_time <= end_time]


class I2CDecoder(ProtocolDecoder):
    """I2C Protocol Decoder"""
    
    def __init__(self):
        super().__init__("I2C")
        self.clock_threshold = 0.5
        self.data_threshold = 0.5
        
    def decode(self, signals: Dict[str, Tuple[np.ndarray, np.ndarray]]) -> List[DecodedFrame]:
        """Decode I2C protocol"""
        self.frames.clear()
        
        if "SCL" not in signals or "SDA" not in signals:
            return self.frames
            
        scl_time, scl_data = signals["SCL"]
        sda_time, sda_data = signals["SDA"]
        
        if len(scl_time) == 0 or len(sda_time) == 0:
            return self.frames
            
        # Align time bases (simplified - assumes same sampling)
        min_len = min(len(scl_time), len(sda_time))
        time_base = scl_time[:min_len]
        scl_digital = (scl_data[:min_len] > self.clock_threshold).astype(int)
        sda_digital = (sda_data[:min_len] > self.data_threshold).astype(int)
        
        # Find I2C events
        i = 0
        while i < len(time_base) - 1:
            # Look for START condition (SDA falling while SCL high)
            if (scl_digital[i] == 1 and scl_digital[i+1] == 1 and
                sda_digital[i] == 1 and sda_digital[i+1] == 0):
                
                start_time = time_base[i]
                i = self._decode_transaction(time_base, scl_digital, sda_digital, i, start_time)
            else:
                i += 1
                
        return self.frames
        
    def _decode_transaction(self, time_base: np.ndarray, scl: np.ndarray, 
                          sda: np.ndarray, start_idx: int, start_time: float) -> int:
        """Decode a complete I2C transaction"""
        # Add START frame
        self.frames.append(DecodedFrame(
            start_time=start_time,
            end_time=start_time,
            event_type=ProtocolEvent.START,
            data=None,
            description="START condition"
        ))
        
        i = start_idx + 1
        
        # Decode address byte
        address, i = self._decode_byte(time_base, scl, sda, i)
        if address is not None:
            rw_bit = address & 0x01
            addr_7bit = (address >> 1) & 0x7F
            
            self.frames.append(DecodedFrame(
                start_time=time_base[start_idx],
                end_time=time_base[min(i, len(time_base)-1)],
                event_type=ProtocolEvent.ADDRESS,
                data={"address": addr_7bit, "read": bool(rw_bit)},
                description=f"Address: 0x{addr_7bit:02X} {'R' if rw_bit else 'W'}"
            ))
            
            # Decode ACK/NACK
            ack, i = self._decode_ack(time_base, scl, sda, i)
            if ack is not None:
                self.frames.append(DecodedFrame(
                    start_time=time_base[min(i-1, len(time_base)-1)],
                    end_time=time_base[min(i, len(time_base)-1)],
                    event_type=ProtocolEvent.ACK if ack else ProtocolEvent.NACK,
                    data=ack,
                    description="ACK" if ack else "NACK"
                ))
                
                # Decode data bytes
                while i < len(time_base) - 8:
                    # Check for STOP condition
                    if self._is_stop_condition(scl, sda, i):
                        self.frames.append(DecodedFrame(
                            start_time=time_base[i],
                            end_time=time_base[i],
                            event_type=ProtocolEvent.STOP,
                            data=None,
                            description="STOP condition"
                        ))
                        break
                        
                    # Decode data byte
                    data_byte, i = self._decode_byte(time_base, scl, sda, i)
                    if data_byte is not None:
                        self.frames.append(DecodedFrame(
                            start_time=time_base[i-8],
                            end_time=time_base[min(i, len(time_base)-1)],
                            event_type=ProtocolEvent.DATA,
                            data=data_byte,
                            description=f"Data: 0x{data_byte:02X} ({data_byte})"
                        ))
                        
                        # Decode ACK/NACK
                        ack, i = self._decode_ack(time_base, scl, sda, i)
                        if ack is not None:
                            self.frames.append(DecodedFrame(
                                start_time=time_base[min(i-1, len(time_base)-1)],
                                end_time=time_base[min(i, len(time_base)-1)],
                                event_type=ProtocolEvent.ACK if ack else ProtocolEvent.NACK,
                                data=ack,
                                description="ACK" if ack else "NACK"
                            ))
                    else:
                        break
                        
        return i
        
    def _decode_byte(self, time_base: np.ndarray, scl: np.ndarray, 
                    sda: np.ndarray, start_idx: int) -> Tuple[Optional[int], int]:
        """Decode 8-bit byte from I2C signals"""
        if start_idx + 16 >= len(scl):  # Need at least 8 clock cycles
            return None, start_idx
            
        byte_value = 0
        i = start_idx
        
        # Find 8 clock cycles
        for bit in range(8):
            # Find rising edge of clock
            while i < len(scl) - 1 and not (scl[i] == 0 and scl[i+1] == 1):
                i += 1
                
            if i >= len(scl) - 1:
                return None, i
                
            # Sample SDA on clock high
            i += 1  # Move to clock high
            if i < len(sda):
                bit_value = sda[i]
                byte_value = (byte_value << 1) | bit_value
                
            # Find falling edge
            while i < len(scl) - 1 and scl[i] == 1:
                i += 1
                
        return byte_value, i
        
    def _decode_ack(self, time_base: np.ndarray, scl: np.ndarray, 
                   sda: np.ndarray, start_idx: int) -> Tuple[Optional[bool], int]:
        """Decode ACK/NACK bit"""
        if start_idx + 2 >= len(scl):
            return None, start_idx
            
        i = start_idx
        
        # Find clock rising edge
        while i < len(scl) - 1 and not (scl[i] == 0 and scl[i+1] == 1):
            i += 1
            
        if i >= len(scl) - 1:
            return None, i
            
        # Sample SDA during clock high
        i += 1
        if i < len(sda):
            ack_bit = sda[i] == 0  # ACK is low, NACK is high
            return ack_bit, i + 1
            
        return None, i
        
    def _is_stop_condition(self, scl: np.ndarray, sda: np.ndarray, idx: int) -> bool:
        """Check for STOP condition (SDA rising while SCL high)"""
        if idx + 1 >= len(scl):
            return False
            
        return (scl[idx] == 1 and scl[idx+1] == 1 and
                sda[idx] == 0 and sda[idx+1] == 1)


class SPIDecoder(ProtocolDecoder):
    """SPI Protocol Decoder"""
    
    def __init__(self):
        super().__init__("SPI")
        self.clock_threshold = 0.5
        self.data_threshold = 0.5
        self.mode = 0  # SPI mode (0-3)
        
    def decode(self, signals: Dict[str, Tuple[np.ndarray, np.ndarray]]) -> List[DecodedFrame]:
        """Decode SPI protocol"""
        self.frames.clear()
        
        required_signals = ["SCLK", "MOSI"]
        if not all(sig in signals for sig in required_signals):
            return self.frames
            
        sclk_time, sclk_data = signals["SCLK"]
        mosi_time, mosi_data = signals["MOSI"]
        
        # Optional MISO
        miso_data = None
        if "MISO" in signals:
            _, miso_data = signals["MISO"]
            
        # Optional CS (Chip Select)
        cs_data = None
        if "CS" in signals:
            _, cs_data = signals["CS"]
            
        if len(sclk_time) == 0:
            return self.frames
            
        # Align signals
        min_len = min(len(sclk_time), len(mosi_time))
        time_base = sclk_time[:min_len]
        sclk_digital = (sclk_data[:min_len] > self.clock_threshold).astype(int)
        mosi_digital = (mosi_data[:min_len] > self.data_threshold).astype(int)
        
        if miso_data is not None:
            miso_digital = (miso_data[:min_len] > self.data_threshold).astype(int)
        else:
            miso_digital = np.zeros_like(mosi_digital)
            
        if cs_data is not None:
            cs_digital = (cs_data[:min_len] > self.data_threshold).astype(int)
        else:
            cs_digital = np.zeros_like(mosi_digital)  # Assume always selected
            
        # Decode SPI transactions
        i = 0
        while i < len(time_base) - 16:  # Need at least 8 clock cycles
            # Look for transaction start (CS active)
            if cs_data is None or cs_digital[i] == 0:  # CS active low
                byte_start = i
                mosi_byte, miso_byte, i = self._decode_spi_byte(
                    time_base, sclk_digital, mosi_digital, miso_digital, i
                )
                
                if mosi_byte is not None:
                    # Create frame for MOSI data
                    self.frames.append(DecodedFrame(
                        start_time=time_base[byte_start],
                        end_time=time_base[min(i, len(time_base)-1)],
                        event_type=ProtocolEvent.DATA,
                        data={"mosi": mosi_byte, "miso": miso_byte},
                        description=f"MOSI: 0x{mosi_byte:02X}, MISO: 0x{miso_byte:02X}"
                    ))
            else:
                i += 1
                
        return self.frames
        
    def _decode_spi_byte(self, time_base: np.ndarray, sclk: np.ndarray,
                        mosi: np.ndarray, miso: np.ndarray, 
                        start_idx: int) -> Tuple[Optional[int], Optional[int], int]:
        """Decode one byte from SPI signals"""
        mosi_byte = 0
        miso_byte = 0
        i = start_idx
        
        # Decode 8 bits
        for bit in range(8):
            # Find clock edge based on SPI mode
            if self.mode in [0, 2]:  # Sample on rising edge
                while i < len(sclk) - 1 and not (sclk[i] == 0 and sclk[i+1] == 1):
                    i += 1
            else:  # Sample on falling edge
                while i < len(sclk) - 1 and not (sclk[i] == 1 and sclk[i+1] == 0):
                    i += 1
                    
            if i >= len(sclk) - 1:
                return None, None, i
                
            # Sample data
            i += 1
            if i < len(mosi):
                mosi_bit = mosi[i]
                miso_bit = miso[i]
                
                # MSB first
                mosi_byte = (mosi_byte << 1) | mosi_bit
                miso_byte = (miso_byte << 1) | miso_bit
                
        return mosi_byte, miso_byte, i


class UARTDecoder(ProtocolDecoder):
    """UART Protocol Decoder"""
    
    def __init__(self, baud_rate: int = 9600):
        super().__init__("UART")
        self.baud_rate = baud_rate
        self.data_bits = 8
        self.parity = "none"  # "none", "even", "odd"
        self.stop_bits = 1
        self.threshold = 0.5
        
    def decode(self, signals: Dict[str, Tuple[np.ndarray, np.ndarray]]) -> List[DecodedFrame]:
        """Decode UART protocol"""
        self.frames.clear()
        
        if "TX" not in signals and "RX" not in signals:
            return self.frames
            
        # Decode TX if available
        if "TX" in signals:
            tx_time, tx_data = signals["TX"]
            self._decode_uart_line(tx_time, tx_data, "TX")
            
        # Decode RX if available
        if "RX" in signals:
            rx_time, rx_data = signals["RX"]
            self._decode_uart_line(rx_time, rx_data, "RX")
            
        # Sort frames by time
        self.frames.sort(key=lambda f: f.start_time)
        
        return self.frames
        
    def _decode_uart_line(self, time_data: np.ndarray, signal_data: np.ndarray, 
                         line_name: str) -> None:
        """Decode UART data from one line"""
        if len(time_data) == 0:
            return
            
        digital_data = (signal_data > self.threshold).astype(int)
        
        # Calculate bit time
        bit_time = 1.0 / self.baud_rate
        sample_rate = 1.0 / (time_data[1] - time_data[0]) if len(time_data) > 1 else 1e6
        samples_per_bit = int(sample_rate * bit_time)
        
        i = 0
        while i < len(digital_data) - samples_per_bit * 10:  # Need space for full frame
            # Look for start bit (falling edge from idle high)
            if digital_data[i] == 1 and digital_data[i + samples_per_bit//2] == 0:
                frame_start_time = time_data[i]
                
                # Decode the byte
                byte_value, parity_ok, i = self._decode_uart_byte(
                    digital_data, i, samples_per_bit
                )
                
                if byte_value is not None:
                    frame_end_time = time_data[min(i, len(time_data)-1)]
                    
                    # Create frame
                    description = f"{line_name}: 0x{byte_value:02X}"
                    if 32 <= byte_value <= 126:  # Printable ASCII
                        description += f" ('{chr(byte_value)}')"
                        
                    error = None
                    if self.parity != "none" and not parity_ok:
                        error = "Parity error"
                        
                    self.frames.append(DecodedFrame(
                        start_time=frame_start_time,
                        end_time=frame_end_time,
                        event_type=ProtocolEvent.DATA,
                        data={"value": byte_value, "line": line_name},
                        description=description,
                        error=error
                    ))
            else:
                i += 1
                
    def _decode_uart_byte(self, data: np.ndarray, start_idx: int, 
                         samples_per_bit: int) -> Tuple[Optional[int], bool, int]:
        """Decode one UART byte"""
        i = start_idx
        
        # Skip start bit
        i += samples_per_bit
        
        # Decode data bits
        byte_value = 0
        for bit in range(self.data_bits):
            if i + samples_per_bit//2 >= len(data):
                return None, False, i
                
            # Sample in middle of bit period
            bit_value = data[i + samples_per_bit//2]
            byte_value |= (bit_value << bit)  # LSB first
            
            i += samples_per_bit
            
        # Check parity if enabled
        parity_ok = True
        if self.parity != "none":
            if i + samples_per_bit//2 >= len(data):
                return None, False, i
                
            parity_bit = data[i + samples_per_bit//2]
            
            if self.parity == "even":
                expected_parity = bin(byte_value).count('1') % 2
            else:  # odd
                expected_parity = (bin(byte_value).count('1') + 1) % 2
                
            parity_ok = (parity_bit == expected_parity)
            i += samples_per_bit
            
        # Skip stop bits
        i += samples_per_bit * self.stop_bits
        
        return byte_value, parity_ok, i