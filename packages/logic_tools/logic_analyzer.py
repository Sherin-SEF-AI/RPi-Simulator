"""
Logic Analyzer - Multi-channel digital signal analysis
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from sim_core import Signal, EventBus, Event, EventType


class TriggerType(Enum):
    """Trigger types for logic analyzer"""
    RISING_EDGE = "rising"
    FALLING_EDGE = "falling"
    BOTH_EDGES = "both"
    HIGH_LEVEL = "high"
    LOW_LEVEL = "low"
    PATTERN = "pattern"


@dataclass
class ChannelConfig:
    """Logic analyzer channel configuration"""
    name: str
    signal: Signal
    enabled: bool = True
    color: str = "#00FF00"
    threshold: float = 1.65  # Logic threshold in volts
    invert: bool = False


@dataclass
class TriggerConfig:
    """Trigger configuration"""
    channel: int
    trigger_type: TriggerType
    pattern: Optional[List[bool]] = None  # For pattern trigger
    pre_trigger_samples: int = 1000
    post_trigger_samples: int = 9000


class LogicAnalyzer:
    """
    Multi-channel logic analyzer with advanced triggering and analysis
    """
    
    def __init__(self, event_bus: EventBus, max_channels: int = 16):
        self.event_bus = event_bus
        self.max_channels = max_channels
        
        # Channels
        self.channels: Dict[int, ChannelConfig] = {}
        
        # Acquisition settings
        self.sample_rate = 1_000_000  # 1 MHz default
        self.memory_depth = 10_000
        self.time_base = 1e-3  # 1ms per division
        
        # Trigger settings
        self.trigger_config: Optional[TriggerConfig] = None
        self.auto_trigger = True
        self.trigger_timeout = 5.0  # seconds
        
        # Acquisition state
        self.acquiring = False
        self.triggered = False
        self.trigger_time = 0.0
        
        # Data storage
        self.sample_buffer: Dict[int, np.ndarray] = {}
        self.time_buffer: np.ndarray = np.array([])
        
        # Analysis results
        self.measurements: Dict[str, Any] = {}
        self.protocol_data: List[Dict] = []
        
    def add_channel(self, channel_id: int, name: str, signal: Signal, 
                   color: str = "#00FF00") -> bool:
        """Add a channel to the logic analyzer"""
        if channel_id >= self.max_channels:
            return False
            
        self.channels[channel_id] = ChannelConfig(
            name=name,
            signal=signal,
            color=color
        )
        
        # Initialize sample buffer
        self.sample_buffer[channel_id] = np.zeros(self.memory_depth, dtype=bool)
        
        return True
        
    def remove_channel(self, channel_id: int) -> bool:
        """Remove a channel"""
        if channel_id in self.channels:
            del self.channels[channel_id]
            if channel_id in self.sample_buffer:
                del self.sample_buffer[channel_id]
            return True
        return False
        
    def set_trigger(self, channel: int, trigger_type: TriggerType, 
                   pattern: Optional[List[bool]] = None) -> None:
        """Set trigger configuration"""
        self.trigger_config = TriggerConfig(
            channel=channel,
            trigger_type=trigger_type,
            pattern=pattern
        )
        
    def start_acquisition(self) -> None:
        """Start data acquisition"""
        if not self.channels:
            return
            
        self.acquiring = True
        self.triggered = False
        self.trigger_time = 0.0
        
        # Clear buffers
        for channel_id in self.sample_buffer:
            self.sample_buffer[channel_id].fill(False)
            
        # Generate time base
        sample_period = 1.0 / self.sample_rate
        self.time_buffer = np.arange(0, self.memory_depth * sample_period, sample_period)
        
        print(f"Logic analyzer acquisition started - {len(self.channels)} channels")
        
    def stop_acquisition(self) -> None:
        """Stop data acquisition"""
        self.acquiring = False
        print("Logic analyzer acquisition stopped")
        
    def update(self, sim_time: float) -> None:
        """Update acquisition (called from simulation loop)"""
        if not self.acquiring:
            return
            
        # Check for trigger condition
        if not self.triggered and self.trigger_config:
            if self._check_trigger(sim_time):
                self.triggered = True
                self.trigger_time = sim_time
                print(f"Logic analyzer triggered at {sim_time:.6f}s")
                
        # Sample all channels
        if self.triggered or self.auto_trigger:
            self._sample_channels(sim_time)
            
    def _check_trigger(self, sim_time: float) -> bool:
        """Check if trigger condition is met"""
        if not self.trigger_config:
            return False
            
        trigger_channel = self.trigger_config.channel
        if trigger_channel not in self.channels:
            return False
            
        signal = self.channels[trigger_channel].signal
        trigger_type = self.trigger_config.trigger_type
        
        # Get current and previous values
        current_value = signal.current_value > 0.5
        
        # Simple edge detection (would be more sophisticated in real implementation)
        if trigger_type == TriggerType.RISING_EDGE:
            return current_value and not getattr(self, '_last_trigger_value', False)
        elif trigger_type == TriggerType.FALLING_EDGE:
            return not current_value and getattr(self, '_last_trigger_value', True)
        elif trigger_type == TriggerType.HIGH_LEVEL:
            return current_value
        elif trigger_type == TriggerType.LOW_LEVEL:
            return not current_value
            
        self._last_trigger_value = current_value
        return False
        
    def _sample_channels(self, sim_time: float) -> None:
        """Sample all enabled channels"""
        if not self.triggered and not self.auto_trigger:
            return
            
        # Calculate sample index
        if self.triggered:
            time_offset = sim_time - self.trigger_time
        else:
            time_offset = sim_time
            
        sample_index = int(time_offset * self.sample_rate) % self.memory_depth
        
        # Sample each channel
        for channel_id, config in self.channels.items():
            if config.enabled and channel_id in self.sample_buffer:
                value = config.signal.current_value > config.threshold
                if config.invert:
                    value = not value
                    
                self.sample_buffer[channel_id][sample_index] = value
                
    def get_waveform_data(self, channel_id: int) -> Tuple[np.ndarray, np.ndarray]:
        """Get waveform data for a channel"""
        if channel_id not in self.sample_buffer:
            return np.array([]), np.array([])
            
        return self.time_buffer.copy(), self.sample_buffer[channel_id].copy()
        
    def measure_frequency(self, channel_id: int, start_time: float = 0, 
                         end_time: Optional[float] = None) -> Optional[float]:
        """Measure signal frequency"""
        if channel_id not in self.sample_buffer:
            return None
            
        time_data, signal_data = self.get_waveform_data(channel_id)
        
        if len(time_data) == 0:
            return None
            
        # Find time range
        if end_time is None:
            end_time = time_data[-1]
            
        mask = (time_data >= start_time) & (time_data <= end_time)
        time_slice = time_data[mask]
        signal_slice = signal_data[mask]
        
        if len(signal_slice) < 3:
            return None
            
        # Count rising edges
        rising_edges = np.where(np.diff(signal_slice.astype(int)) > 0)[0]
        
        if len(rising_edges) < 2:
            return None
            
        # Calculate frequency from edge timing
        edge_times = time_slice[rising_edges]
        periods = np.diff(edge_times)
        
        if len(periods) > 0:
            avg_period = np.mean(periods)
            return 1.0 / avg_period if avg_period > 0 else None
            
        return None
        
    def measure_duty_cycle(self, channel_id: int, start_time: float = 0,
                          end_time: Optional[float] = None) -> Optional[float]:
        """Measure PWM duty cycle"""
        if channel_id not in self.sample_buffer:
            return None
            
        time_data, signal_data = self.get_waveform_data(channel_id)
        
        if len(time_data) == 0:
            return None
            
        # Find time range
        if end_time is None:
            end_time = time_data[-1]
            
        mask = (time_data >= start_time) & (time_data <= end_time)
        signal_slice = signal_data[mask]
        
        if len(signal_slice) == 0:
            return None
            
        # Calculate duty cycle
        high_samples = np.sum(signal_slice)
        total_samples = len(signal_slice)
        
        return (high_samples / total_samples) * 100.0
        
    def find_edges(self, channel_id: int, edge_type: str = "both") -> List[Tuple[float, str]]:
        """Find signal edges"""
        if channel_id not in self.sample_buffer:
            return []
            
        time_data, signal_data = self.get_waveform_data(channel_id)
        
        if len(time_data) < 2:
            return []
            
        # Find edges
        diff = np.diff(signal_data.astype(int))
        
        edges = []
        
        if edge_type in ["rising", "both"]:
            rising_indices = np.where(diff > 0)[0]
            for idx in rising_indices:
                edges.append((time_data[idx + 1], "rising"))
                
        if edge_type in ["falling", "both"]:
            falling_indices = np.where(diff < 0)[0]
            for idx in falling_indices:
                edges.append((time_data[idx + 1], "falling"))
                
        # Sort by time
        edges.sort(key=lambda x: x[0])
        
        return edges
        
    def export_data(self, filename: str, format: str = "csv") -> bool:
        """Export captured data"""
        try:
            if format.lower() == "csv":
                import csv
                
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Header
                    header = ["Time"]
                    for channel_id in sorted(self.channels.keys()):
                        header.append(self.channels[channel_id].name)
                    writer.writerow(header)
                    
                    # Data
                    for i, time_val in enumerate(self.time_buffer):
                        row = [f"{time_val:.9f}"]
                        for channel_id in sorted(self.channels.keys()):
                            if i < len(self.sample_buffer[channel_id]):
                                row.append("1" if self.sample_buffer[channel_id][i] else "0")
                            else:
                                row.append("0")
                        writer.writerow(row)
                        
            elif format.lower() == "vcd":
                # VCD (Value Change Dump) format
                with open(filename, 'w') as vcdfile:
                    # VCD header
                    vcdfile.write("$version PiStudio Logic Analyzer $end\\n")
                    vcdfile.write("$timescale 1ns $end\\n")
                    
                    # Variable definitions
                    vcdfile.write("$scope module top $end\\n")
                    for channel_id in sorted(self.channels.keys()):
                        symbol = chr(ord('A') + channel_id)
                        name = self.channels[channel_id].name
                        vcdfile.write(f"$var wire 1 {symbol} {name} $end\\n")
                    vcdfile.write("$upscope $end\\n")
                    vcdfile.write("$enddefinitions $end\\n")
                    
                    # Initial values
                    vcdfile.write("$dumpvars\\n")
                    for channel_id in sorted(self.channels.keys()):
                        symbol = chr(ord('A') + channel_id)
                        initial_val = "1" if self.sample_buffer[channel_id][0] else "0"
                        vcdfile.write(f"{initial_val}{symbol}\\n")
                    vcdfile.write("$end\\n")
                    
                    # Value changes
                    for i, time_val in enumerate(self.time_buffer[1:], 1):
                        time_ns = int(time_val * 1e9)
                        vcdfile.write(f"#{time_ns}\\n")
                        
                        for channel_id in sorted(self.channels.keys()):
                            if i < len(self.sample_buffer[channel_id]):
                                current_val = self.sample_buffer[channel_id][i]
                                prev_val = self.sample_buffer[channel_id][i-1]
                                
                                if current_val != prev_val:
                                    symbol = chr(ord('A') + channel_id)
                                    val = "1" if current_val else "0"
                                    vcdfile.write(f"{val}{symbol}\\n")
                                    
            return True
            
        except Exception as e:
            print(f"Export error: {e}")
            return False
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get acquisition statistics"""
        stats = {
            "channels": len(self.channels),
            "sample_rate": self.sample_rate,
            "memory_depth": self.memory_depth,
            "triggered": self.triggered,
            "trigger_time": self.trigger_time
        }
        
        # Per-channel statistics
        for channel_id, config in self.channels.items():
            if channel_id in self.sample_buffer:
                data = self.sample_buffer[channel_id]
                
                stats[f"ch{channel_id}_name"] = config.name
                stats[f"ch{channel_id}_transitions"] = np.sum(np.diff(data.astype(int)) != 0)
                stats[f"ch{channel_id}_high_time"] = np.sum(data) / self.sample_rate
                stats[f"ch{channel_id}_duty_cycle"] = (np.sum(data) / len(data)) * 100
                
        return stats