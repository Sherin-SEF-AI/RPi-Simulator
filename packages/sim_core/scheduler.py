"""
Event Scheduler - Priority queue for simulation events
"""

import heapq
from typing import Any, Callable, List, Optional
from dataclasses import dataclass, field


@dataclass
class ScheduledEvent:
    """Event scheduled for future execution"""
    time: float
    priority: int
    callback: Callable[[], None]
    data: Any = None
    cancelled: bool = False
    event_id: int = field(default_factory=lambda: id(object()))
    
    def __lt__(self, other):
        """Compare for heap ordering (earlier time, higher priority first)"""
        if self.time != other.time:
            return self.time < other.time
        return self.priority < other.priority


class Scheduler:
    """
    Event scheduler using priority queue for efficient event ordering.
    Supports cancellation and recurring events.
    """
    
    def __init__(self):
        self._events: List[ScheduledEvent] = []
        self._next_event_id = 0
        
    def schedule(self, delay: float, callback: Callable[[], None], 
                priority: int = 0, data: Any = None) -> int:
        """
        Schedule an event for future execution
        
        Args:
            delay: Delay in simulation seconds
            callback: Function to execute
            priority: Event priority (lower = higher priority)
            data: Optional data to pass to callback
            
        Returns:
            Event ID for cancellation
        """
        event_id = self._next_event_id
        self._next_event_id += 1
        
        event = ScheduledEvent(
            time=delay,
            priority=priority,
            callback=callback,
            data=data,
            event_id=event_id
        )
        
        heapq.heappush(self._events, event)
        return event_id
        
    def schedule_at(self, sim_time: float, callback: Callable[[], None],
                   priority: int = 0, data: Any = None) -> int:
        """Schedule event at absolute simulation time"""
        event_id = self._next_event_id
        self._next_event_id += 1
        
        event = ScheduledEvent(
            time=sim_time,
            priority=priority,
            callback=callback,
            data=data,
            event_id=event_id
        )
        
        heapq.heappush(self._events, event)
        return event_id
        
    def cancel(self, event_id: int) -> bool:
        """
        Cancel a scheduled event
        
        Args:
            event_id: ID returned by schedule()
            
        Returns:
            True if event was found and cancelled
        """
        for event in self._events:
            if event.event_id == event_id:
                event.cancelled = True
                return True
        return False
        
    def process_events(self, current_time: float) -> int:
        """
        Process all events scheduled up to current time
        
        Args:
            current_time: Current simulation time
            
        Returns:
            Number of events processed
        """
        processed = 0
        
        while self._events and self._events[0].time <= current_time:
            event = heapq.heappop(self._events)
            
            if event.cancelled:
                continue
                
            try:
                if event.data is not None:
                    event.callback(event.data)
                else:
                    event.callback()
                processed += 1
            except Exception as e:
                print(f"Scheduled event error: {e}")
                
        return processed
        
    def peek_next_time(self) -> Optional[float]:
        """
        Get time of next scheduled event
        
        Returns:
            Time of next event, or None if no events
        """
        while self._events and self._events[0].cancelled:
            heapq.heappop(self._events)
            
        return self._events[0].time if self._events else None
        
    def clear(self) -> None:
        """Clear all scheduled events"""
        self._events.clear()
        
    def event_count(self) -> int:
        """Get number of pending events (including cancelled)"""
        return len(self._events)
        
    def active_event_count(self) -> int:
        """Get number of active (non-cancelled) events"""
        return sum(1 for e in self._events if not e.cancelled)