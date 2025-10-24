"""
Event System - Pub/sub messaging for simulation components
"""

from enum import Enum
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass
import weakref


class EventType(Enum):
    """Standard simulation event types"""
    GPIO_EDGE = "gpio_edge"
    GPIO_STATE = "gpio_state"
    I2C_TRANSACTION = "i2c_transaction"
    SPI_TRANSACTION = "spi_transaction"
    UART_DATA = "uart_data"
    PWM_UPDATE = "pwm_update"
    DEVICE_UPDATE = "device_update"
    SIMULATION_START = "simulation_start"
    SIMULATION_STOP = "simulation_stop"
    SIMULATION_RESET = "simulation_reset"


@dataclass
class Event:
    """Simulation event with timestamp and data"""
    type: EventType
    timestamp: float  # Simulation time in seconds
    source: str
    data: Dict[str, Any]
    
    def __post_init__(self):
        """Ensure data is a dictionary"""
        if not isinstance(self.data, dict):
            self.data = {"value": self.data}


class EventBus:
    """
    Central event bus for simulation components.
    Provides pub/sub messaging with weak references to prevent memory leaks.
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[weakref.WeakMethod]] = {}
        self._event_history: List[Event] = []
        self._recording = False
        self._max_history = 10000
        
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """
        Subscribe to events of a specific type
        
        Args:
            event_type: Type of events to receive
            callback: Function to call when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
            
        # Use weak reference to prevent memory leaks
        weak_callback = weakref.WeakMethod(callback)
        self._subscribers[event_type].append(weak_callback)
        
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Unsubscribe from events"""
        if event_type not in self._subscribers:
            return
            
        # Remove matching weak references
        self._subscribers[event_type] = [
            weak_cb for weak_cb in self._subscribers[event_type]
            if weak_cb() is not callback
        ]
        
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers
        
        Args:
            event: Event to publish
        """
        # Record event if recording enabled
        if self._recording:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
                
        # Notify subscribers
        if event.type in self._subscribers:
            dead_refs = []
            
            for weak_callback in self._subscribers[event.type]:
                callback = weak_callback()
                if callback is None:
                    dead_refs.append(weak_callback)
                else:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"Event callback error: {e}")
                        
            # Clean up dead references
            for dead_ref in dead_refs:
                self._subscribers[event.type].remove(dead_ref)
                
    def start_recording(self) -> None:
        """Start recording events for replay"""
        self._recording = True
        self._event_history.clear()
        
    def stop_recording(self) -> List[Event]:
        """Stop recording and return event history"""
        self._recording = False
        return self._event_history.copy()
        
    def get_events(self, event_type: Optional[EventType] = None, 
                   start_time: Optional[float] = None,
                   end_time: Optional[float] = None) -> List[Event]:
        """
        Get filtered event history
        
        Args:
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            Filtered list of events
        """
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.type == event_type]
            
        if start_time is not None:
            events = [e for e in events if e.timestamp >= start_time]
            
        if end_time is not None:
            events = [e for e in events if e.timestamp <= end_time]
            
        return events
        
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()