"""
PWM Controller - Pulse Width Modulation
"""

from typing import Dict, Optional
from sim_core import EventBus, Event, EventType, Signal


class PwmChannel:
    """Individual PWM channel"""
    
    def __init__(self, channel: int, pin: int):
        self.channel = channel
        self.pin = pin
        self.frequency = 1000.0  # Hz
        self.duty_cycle = 0.0    # 0-100%
        self.enabled = False
        
        # Signal for waveform generation
        self.signal = Signal(f"PWM{channel}", is_analog=False)
        
    def set_frequency(self, freq: float) -> None:
        """Set PWM frequency"""
        self.frequency = max(1.0, min(100000.0, freq))
        
    def set_duty_cycle(self, duty: float) -> None:
        """Set PWM duty cycle (0-100%)"""
        self.duty_cycle = max(0.0, min(100.0, duty))
        
    def start(self) -> None:
        """Start PWM output"""
        self.enabled = True
        
    def stop(self) -> None:
        """Stop PWM output"""
        self.enabled = False
        
    def update(self, sim_time: float) -> None:
        """Update PWM signal"""
        if not self.enabled:
            return
            
        # Calculate PWM period and high time
        period = 1.0 / self.frequency
        high_time = period * (self.duty_cycle / 100.0)
        
        # Determine current state within period
        time_in_period = sim_time % period
        
        if time_in_period < high_time:
            value = 1.0
        else:
            value = 0.0
            
        self.signal.set_value(value, sim_time)


class PwmController:
    """
    PWM controller managing multiple channels
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.channels: Dict[int, PwmChannel] = {}
        
        # Standard Pi PWM pins
        self._init_channels()
        
    def _init_channels(self) -> None:
        """Initialize PWM channels"""
        # Pi has 2 hardware PWM channels
        self.channels[0] = PwmChannel(0, 18)  # GPIO18 - PWM0
        self.channels[1] = PwmChannel(1, 19)  # GPIO19 - PWM1
        
    def get_channel(self, pin: int) -> Optional[PwmChannel]:
        """Get PWM channel for GPIO pin"""
        for channel in self.channels.values():
            if channel.pin == pin:
                return channel
        return None
        
    def set_frequency(self, pin: int, frequency: float) -> bool:
        """Set PWM frequency for pin"""
        channel = self.get_channel(pin)
        if channel:
            old_freq = channel.frequency
            channel.set_frequency(frequency)
            
            # Publish event
            self.event_bus.publish(Event(
                type=EventType.PWM_UPDATE,
                timestamp=0.0,  # Would use actual sim time
                source=f"PWM{channel.channel}",
                data={
                    "pin": pin,
                    "frequency": frequency,
                    "old_frequency": old_freq
                }
            ))
            return True
        return False
        
    def set_duty_cycle(self, pin: int, duty_cycle: float) -> bool:
        """Set PWM duty cycle for pin"""
        channel = self.get_channel(pin)
        if channel:
            old_duty = channel.duty_cycle
            channel.set_duty_cycle(duty_cycle)
            
            # Publish event
            self.event_bus.publish(Event(
                type=EventType.PWM_UPDATE,
                timestamp=0.0,
                source=f"PWM{channel.channel}",
                data={
                    "pin": pin,
                    "duty_cycle": duty_cycle,
                    "old_duty_cycle": old_duty
                }
            ))
            return True
        return False
        
    def start_pwm(self, pin: int) -> bool:
        """Start PWM on pin"""
        channel = self.get_channel(pin)
        if channel:
            channel.start()
            return True
        return False
        
    def stop_pwm(self, pin: int) -> bool:
        """Stop PWM on pin"""
        channel = self.get_channel(pin)
        if channel:
            channel.stop()
            return True
        return False
        
    def update(self, sim_time: float) -> None:
        """Update all PWM channels"""
        for channel in self.channels.values():
            channel.update(sim_time)
            
    def get_signal(self, pin: int) -> Optional[Signal]:
        """Get PWM signal for logic analyzer"""
        channel = self.get_channel(pin)
        return channel.signal if channel else None