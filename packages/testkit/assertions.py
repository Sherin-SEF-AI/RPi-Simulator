"""
Test Assertions for PiStudio
"""

import time
from typing import List, Optional, Dict, Any
from sim_core import Event, EventType


class AssertionError(Exception):
    """Custom assertion error for PiStudio tests"""
    pass


class PinAssertions:
    """GPIO pin assertion helpers"""
    
    def __init__(self, event_bus, timeout_s: float = 5.0):
        self.event_bus = event_bus
        self.timeout_s = timeout_s
        
    def assert_pin_high(self, pin: int, within_ms: float = 1000) -> None:
        """Assert that pin goes high within time limit"""
        start_time = time.time()
        timeout = within_ms / 1000.0
        
        while time.time() - start_time < timeout:
            events = self.event_bus.get_events(EventType.GPIO_STATE)
            for event in events:
                if (event.data.get("pin") == pin and 
                    event.data.get("value") == 1 and
                    event.timestamp >= start_time):
                    return  # Success
            time.sleep(0.001)  # Small delay
            
        raise AssertionError(f"Pin {pin} did not go HIGH within {within_ms}ms")
        
    def assert_pin_low(self, pin: int, within_ms: float = 1000) -> None:
        """Assert that pin goes low within time limit"""
        start_time = time.time()
        timeout = within_ms / 1000.0
        
        while time.time() - start_time < timeout:
            events = self.event_bus.get_events(EventType.GPIO_STATE)
            for event in events:
                if (event.data.get("pin") == pin and 
                    event.data.get("value") == 0 and
                    event.timestamp >= start_time):
                    return  # Success
            time.sleep(0.001)
            
        raise AssertionError(f"Pin {pin} did not go LOW within {within_ms}ms")
        
    def assert_pin_toggle(self, pin: int, min_edges: int, within_ms: float = 2000) -> None:
        """Assert that pin toggles minimum number of times"""
        start_time = time.time()
        timeout = within_ms / 1000.0
        edge_count = 0
        
        while time.time() - start_time < timeout:
            events = self.event_bus.get_events(EventType.GPIO_EDGE)
            for event in events:
                if (event.data.get("pin") == pin and 
                    event.timestamp >= start_time):
                    edge_count += 1
                    
            if edge_count >= min_edges:
                return  # Success
                
            time.sleep(0.001)
            
        raise AssertionError(
            f"Pin {pin} only toggled {edge_count} times, expected {min_edges} within {within_ms}ms"
        )
        
    def assert_pwm_frequency(self, pin: int, expected_freq: float, tolerance: float = 0.1) -> None:
        """Assert PWM frequency within tolerance"""
        # This would analyze edge timing to calculate frequency
        # Simplified implementation
        events = self.event_bus.get_events(EventType.GPIO_EDGE)
        pin_events = [e for e in events if e.data.get("pin") == pin]
        
        if len(pin_events) < 4:
            raise AssertionError(f"Insufficient edges to measure frequency on pin {pin}")
            
        # Calculate frequency from edge timing
        rising_edges = [e for e in pin_events if e.data.get("edge") == "rising"]
        if len(rising_edges) < 2:
            raise AssertionError(f"Need at least 2 rising edges to measure frequency")
            
        periods = []
        for i in range(1, len(rising_edges)):
            period = rising_edges[i].timestamp - rising_edges[i-1].timestamp
            periods.append(period)
            
        avg_period = sum(periods) / len(periods)
        measured_freq = 1.0 / avg_period
        
        if abs(measured_freq - expected_freq) > tolerance:
            raise AssertionError(
                f"PWM frequency {measured_freq:.2f}Hz not within {tolerance}Hz of expected {expected_freq}Hz"
            )


class I2cAssertions:
    """I2C bus assertion helpers"""
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        
    def assert_i2c_write(self, address: int, data: List[int], within_ms: float = 1000) -> None:
        """Assert I2C write transaction occurred"""
        start_time = time.time()
        timeout = within_ms / 1000.0
        
        while time.time() - start_time < timeout:
            events = self.event_bus.get_events(EventType.I2C_TRANSACTION)
            for event in events:
                if (event.data.get("address") == address and
                    event.data.get("write") == True and
                    event.data.get("data") == data and
                    event.timestamp >= start_time):
                    return  # Success
            time.sleep(0.001)
            
        raise AssertionError(
            f"I2C write to 0x{address:02X} with data {data} not found within {within_ms}ms"
        )
        
    def assert_i2c_read(self, address: int, length: int, within_ms: float = 1000) -> List[int]:
        """Assert I2C read transaction and return data"""
        start_time = time.time()
        timeout = within_ms / 1000.0
        
        while time.time() - start_time < timeout:
            events = self.event_bus.get_events(EventType.I2C_TRANSACTION)
            for event in events:
                if (event.data.get("address") == address and
                    event.data.get("read") == True and
                    event.data.get("length") == length and
                    event.timestamp >= start_time):
                    return event.data.get("data", [])
            time.sleep(0.001)
            
        raise AssertionError(
            f"I2C read from 0x{address:02X} length {length} not found within {within_ms}ms"
        )


class TimingAssertions:
    """Timing-related assertions"""
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        
    def assert_event_sequence(self, expected_events: List[Dict[str, Any]], 
                            tolerance_ms: float = 10) -> None:
        """Assert sequence of events with timing tolerance"""
        tolerance_s = tolerance_ms / 1000.0
        
        all_events = self.event_bus.get_events()
        all_events.sort(key=lambda e: e.timestamp)
        
        event_index = 0
        for expected in expected_events:
            found = False
            
            while event_index < len(all_events):
                event = all_events[event_index]
                
                # Check if event matches expected
                if self._event_matches(event, expected):
                    # Check timing if specified
                    if "timestamp" in expected:
                        expected_time = expected["timestamp"]
                        if abs(event.timestamp - expected_time) > tolerance_s:
                            raise AssertionError(
                                f"Event timing mismatch: expected {expected_time}, "
                                f"got {event.timestamp} (tolerance: {tolerance_ms}ms)"
                            )
                    found = True
                    event_index += 1
                    break
                    
                event_index += 1
                
            if not found:
                raise AssertionError(f"Expected event not found: {expected}")
                
    def _event_matches(self, event: Event, expected: Dict[str, Any]) -> bool:
        """Check if event matches expected pattern"""
        if "type" in expected and event.type.value != expected["type"]:
            return False
            
        if "source" in expected and event.source != expected["source"]:
            return False
            
        if "data" in expected:
            for key, value in expected["data"].items():
                if event.data.get(key) != value:
                    return False
                    
        return True