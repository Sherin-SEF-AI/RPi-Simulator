"""
Signal Processing - Digital and analog signal representation
"""

from enum import Enum
from typing import List, Optional, Tuple
from dataclasses import dataclass
import numpy as np


class SignalState(Enum):
    """Digital signal states"""
    LOW = 0
    HIGH = 1
    FLOATING = 2  # High impedance
    UNKNOWN = 3   # Undefined state


class Edge(Enum):
    """Signal edge types"""
    RISING = "rising"
    FALLING = "falling"
    BOTH = "both"


@dataclass
class SignalSample:
    """Single signal sample with timestamp"""
    timestamp: float  # Simulation time in seconds
    value: float      # Signal value (0-1 for digital, any for analog)
    state: SignalState = SignalState.UNKNOWN


class Signal:
    """
    Digital or analog signal with history and edge detection.
    Optimized for memory efficiency with configurable sample retention.
    """
    
    def __init__(self, name: str, is_analog: bool = False, max_samples: int = 10000):
        """
        Initialize signal
        
        Args:
            name: Signal identifier
            is_analog: True for analog signals, False for digital
            max_samples: Maximum samples to retain in history
        """
        self.name = name
        self.is_analog = is_analog
        self.max_samples = max_samples
        
        self._samples: List[SignalSample] = []
        self._current_value = 0.0
        self._current_state = SignalState.FLOATING
        self._last_edge_time = 0.0
        
        # Edge detection
        self._edge_callbacks: List[Tuple[Edge, callable]] = []
        
    @property
    def current_value(self) -> float:
        """Current signal value"""
        return self._current_value
        
    @property
    def current_state(self) -> SignalState:
        """Current digital state"""
        return self._current_state
        
    @property
    def sample_count(self) -> int:
        """Number of samples in history"""
        return len(self._samples)
        
    def set_value(self, value: float, timestamp: float, 
                  state: Optional[SignalState] = None) -> None:
        """
        Update signal value and detect edges
        
        Args:
            value: New signal value
            timestamp: Simulation time
            state: Digital state (auto-detected if None)
        """
        old_value = self._current_value
        old_state = self._current_state
        
        self._current_value = value
        
        # Auto-detect digital state for digital signals
        if not self.is_analog and state is None:
            if value >= 0.7:  # TTL high threshold
                state = SignalState.HIGH
            elif value <= 0.3:  # TTL low threshold
                state = SignalState.LOW
            else:
                state = SignalState.UNKNOWN
                
        if state is not None:
            self._current_state = state
            
        # Add sample to history
        sample = SignalSample(timestamp, value, self._current_state)
        self._samples.append(sample)
        
        # Trim history if needed
        if len(self._samples) > self.max_samples:
            self._samples.pop(0)
            
        # Detect edges for digital signals
        if not self.is_analog:
            self._detect_edges(old_state, self._current_state, timestamp)
            
    def _detect_edges(self, old_state: SignalState, new_state: SignalState, 
                     timestamp: float) -> None:
        """Detect and notify edge callbacks"""
        edge_type = None
        
        if old_state == SignalState.LOW and new_state == SignalState.HIGH:
            edge_type = Edge.RISING
        elif old_state == SignalState.HIGH and new_state == SignalState.LOW:
            edge_type = Edge.FALLING
            
        if edge_type:
            self._last_edge_time = timestamp
            
            for callback_edge, callback in self._edge_callbacks:
                if callback_edge == edge_type or callback_edge == Edge.BOTH:
                    try:
                        callback(self, edge_type, timestamp)
                    except Exception as e:
                        print(f"Edge callback error: {e}")
                        
    def on_edge(self, edge: Edge, callback: callable) -> None:
        """
        Register callback for edge detection
        
        Args:
            edge: Edge type to detect
            callback: Function called on edge (signal, edge_type, timestamp)
        """
        self._edge_callbacks.append((edge, callback))
        
    def get_samples(self, start_time: Optional[float] = None,
                   end_time: Optional[float] = None) -> List[SignalSample]:
        """
        Get signal samples within time range
        
        Args:
            start_time: Start time filter
            end_time: End time filter
            
        Returns:
            Filtered samples
        """
        samples = self._samples
        
        if start_time is not None:
            samples = [s for s in samples if s.timestamp >= start_time]
            
        if end_time is not None:
            samples = [s for s in samples if s.timestamp <= end_time]
            
        return samples
        
    def get_waveform(self, start_time: Optional[float] = None,
                    end_time: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get waveform data as numpy arrays for plotting
        
        Returns:
            Tuple of (timestamps, values)
        """
        samples = self.get_samples(start_time, end_time)
        
        if not samples:
            return np.array([]), np.array([])
            
        timestamps = np.array([s.timestamp for s in samples])
        values = np.array([s.value for s in samples])
        
        return timestamps, values
        
    def clear_history(self) -> None:
        """Clear sample history"""
        self._samples.clear()
        
    def get_frequency(self, window_s: float = 1.0) -> Optional[float]:
        """
        Calculate signal frequency over time window
        
        Args:
            window_s: Time window in seconds
            
        Returns:
            Frequency in Hz, or None if insufficient data
        """
        if self.is_analog:
            return None
            
        current_time = self._samples[-1].timestamp if self._samples else 0
        start_time = current_time - window_s
        
        # Count rising edges in window
        edge_count = 0
        last_state = SignalState.LOW
        
        for sample in self._samples:
            if sample.timestamp < start_time:
                continue
                
            if (last_state == SignalState.LOW and 
                sample.state == SignalState.HIGH):
                edge_count += 1
                
            last_state = sample.state
            
        return edge_count / window_s if edge_count > 0 else None