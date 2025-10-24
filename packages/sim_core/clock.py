"""
Simulation Clock - Deterministic timing engine
"""

import time
from typing import Optional, Callable, List
from dataclasses import dataclass


@dataclass
class TimerEvent:
    """Scheduled timer event"""
    sim_time: float
    callback: Callable[[], None]
    repeat_interval: Optional[float] = None
    active: bool = True


class SimClock:
    """
    Deterministic simulation clock with configurable timestep.
    Provides microsecond precision timing for accurate hardware simulation.
    """
    
    def __init__(self, timestep_us: int = 1):
        """
        Initialize simulation clock
        
        Args:
            timestep_us: Simulation timestep in microseconds (1-1000)
        """
        self.timestep_us = max(1, min(1000, timestep_us))
        self.timestep_s = self.timestep_us / 1_000_000
        
        self._sim_time = 0.0  # Current simulation time in seconds
        self._real_start_time = 0.0
        self._running = False
        self._paused = False
        
        self._timers: List[TimerEvent] = []
        self._next_timer_id = 0
        
    @property
    def sim_time(self) -> float:
        """Current simulation time in seconds"""
        return self._sim_time
        
    @property
    def sim_time_us(self) -> int:
        """Current simulation time in microseconds"""
        return int(self._sim_time * 1_000_000)
        
    @property
    def running(self) -> bool:
        """Whether clock is running"""
        return self._running and not self._paused
        
    def start(self) -> None:
        """Start the simulation clock"""
        if not self._running:
            self._running = True
            self._real_start_time = time.time()
            
    def stop(self) -> None:
        """Stop the simulation clock"""
        self._running = False
        self._paused = False
        
    def pause(self) -> None:
        """Pause the simulation clock"""
        self._paused = True
        
    def resume(self) -> None:
        """Resume the simulation clock"""
        self._paused = False
        
    def reset(self) -> None:
        """Reset simulation time to zero"""
        self._sim_time = 0.0
        self._timers.clear()
        
    def tick(self) -> bool:
        """
        Advance simulation by one timestep
        
        Returns:
            True if clock advanced, False if stopped/paused
        """
        if not self.running:
            return False
            
        self._sim_time += self.timestep_s
        self._process_timers()
        return True
        
    def advance_to(self, target_time: float) -> None:
        """Advance simulation to specific time"""
        while self._sim_time < target_time and self.running:
            self.tick()
            
    def schedule_timer(self, delay_s: float, callback: Callable[[], None], 
                      repeat_interval: Optional[float] = None) -> int:
        """
        Schedule a timer callback
        
        Args:
            delay_s: Delay in seconds from current sim time
            callback: Function to call when timer fires
            repeat_interval: If set, timer repeats every N seconds
            
        Returns:
            Timer ID for cancellation
        """
        timer_id = self._next_timer_id
        self._next_timer_id += 1
        
        timer = TimerEvent(
            sim_time=self._sim_time + delay_s,
            callback=callback,
            repeat_interval=repeat_interval
        )
        
        self._timers.append(timer)
        self._timers.sort(key=lambda t: t.sim_time)
        
        return timer_id
        
    def cancel_timer(self, timer_id: int) -> None:
        """Cancel a scheduled timer"""
        for timer in self._timers:
            if id(timer) == timer_id:
                timer.active = False
                break
                
    def _process_timers(self) -> None:
        """Process any timers that should fire at current sim time"""
        fired_timers = []
        
        for timer in self._timers[:]:
            if not timer.active:
                self._timers.remove(timer)
                continue
                
            if timer.sim_time <= self._sim_time:
                fired_timers.append(timer)
                self._timers.remove(timer)
                
        for timer in fired_timers:
            try:
                timer.callback()
            except Exception as e:
                print(f"Timer callback error: {e}")
                
            # Reschedule repeating timer
            if timer.repeat_interval and timer.active:
                timer.sim_time = self._sim_time + timer.repeat_interval
                self._timers.append(timer)
                
        if self._timers:
            self._timers.sort(key=lambda t: t.sim_time)