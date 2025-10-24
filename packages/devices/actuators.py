"""
Actuator Device Implementations
"""

import math
import time
from typing import List, Tuple, Optional, Dict, Any
from .base import VirtualDevice, DeviceParameter


class LED(VirtualDevice):
    """Single LED with brightness control"""
    
    def __init__(self, name: str = "LED", pin: int = 18):
        super().__init__(name, "actuator")
        self.pin = pin
        
        # Parameters
        self.parameters = {
            "brightness": DeviceParameter("Brightness", 0, 0, 255, "", "LED brightness"),
            "color": DeviceParameter("Color", "red", description="LED color"),
            "forward_voltage": DeviceParameter("Forward Voltage", 2.0, 1.5, 4.0, "V"),
            "max_current": DeviceParameter("Max Current", 20, 1, 100, "mA")
        }
        
        # State
        self.is_on = False
        self.pwm_value = 0
        self.current_ma = 0.0
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update LED state"""
        self.last_update = sim_time
        
        # Calculate current based on brightness
        brightness = self.get_parameter("brightness")
        max_current = self.get_parameter("max_current")
        self.current_ma = (brightness / 255.0) * max_current
        self.is_on = brightness > 0
        
    def set_brightness(self, brightness: int) -> None:
        """Set LED brightness (0-255)"""
        self.set_parameter("brightness", max(0, min(255, brightness)))
        
    def turn_on(self) -> None:
        """Turn LED on at full brightness"""
        self.set_brightness(255)
        
    def turn_off(self) -> None:
        """Turn LED off"""
        self.set_brightness(0)
        
    def set_pwm(self, duty_cycle: float) -> None:
        """Set PWM duty cycle (0.0-1.0)"""
        self.pwm_value = max(0.0, min(1.0, duty_cycle))
        self.set_brightness(int(self.pwm_value * 255))
        
    def get_power_consumption(self) -> float:
        """Get power consumption in mW"""
        voltage = self.get_parameter("forward_voltage")
        return self.current_ma * voltage
        
    def reset(self) -> None:
        """Reset LED"""
        self.turn_off()
        self.pwm_value = 0


class RGBLED(VirtualDevice):
    """RGB LED with individual color control"""
    
    def __init__(self, name: str = "RGB_LED", pins: Tuple[int, int, int] = (18, 19, 20)):
        super().__init__(name, "actuator")
        self.red_pin, self.green_pin, self.blue_pin = pins
        
        # Parameters
        self.parameters = {
            "red": DeviceParameter("Red", 0, 0, 255, "", "Red intensity"),
            "green": DeviceParameter("Green", 0, 0, 255, "", "Green intensity"),
            "blue": DeviceParameter("Blue", 0, 0, 255, "", "Blue intensity"),
            "brightness": DeviceParameter("Brightness", 100, 0, 100, "%", "Global brightness"),
            "common_anode": DeviceParameter("Common Anode", False, description="Common anode configuration")
        }
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update RGB LED state"""
        self.last_update = sim_time
        
    def set_color(self, r: int, g: int, b: int) -> None:
        """Set RGB color values (0-255)"""
        self.set_parameter("red", max(0, min(255, r)))
        self.set_parameter("green", max(0, min(255, g)))
        self.set_parameter("blue", max(0, min(255, b)))
        
    def set_hsv(self, h: float, s: float, v: float) -> None:
        """Set color using HSV values (0-1)"""
        r, g, b = self._hsv_to_rgb(h, s, v)
        self.set_color(int(r * 255), int(g * 255), int(b * 255))
        
    def set_hex_color(self, hex_color: str) -> None:
        """Set color using hex string (#RRGGBB)"""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            self.set_color(r, g, b)
            
    def get_rgb(self) -> Tuple[int, int, int]:
        """Get current RGB values"""
        brightness = self.get_parameter("brightness") / 100.0
        return (
            int(self.get_parameter("red") * brightness),
            int(self.get_parameter("green") * brightness),
            int(self.get_parameter("blue") * brightness)
        )
        
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[float, float, float]:
        """Convert HSV to RGB"""
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        
        i = i % 6
        if i == 0: return v, t, p
        elif i == 1: return q, v, p
        elif i == 2: return p, v, t
        elif i == 3: return p, q, v
        elif i == 4: return t, p, v
        else: return v, p, q
        
    def reset(self) -> None:
        """Reset RGB LED"""
        self.set_color(0, 0, 0)


class Servo(VirtualDevice):
    """SG90-style Servo Motor"""
    
    def __init__(self, name: str = "Servo", pin: int = 18):
        super().__init__(name, "actuator")
        self.pin = pin
        
        # Parameters
        self.parameters = {
            "position": DeviceParameter("Position", 90, 0, 180, "°", "Servo angle"),
            "speed": DeviceParameter("Speed", 60, 10, 300, "°/s", "Movement speed"),
            "min_pulse": DeviceParameter("Min Pulse", 1.0, 0.5, 2.0, "ms", "Minimum pulse width"),
            "max_pulse": DeviceParameter("Max Pulse", 2.0, 1.5, 2.5, "ms", "Maximum pulse width"),
            "frequency": DeviceParameter("Frequency", 50, 40, 100, "Hz", "PWM frequency")
        }
        
        # State
        self.target_position = 90
        self.current_position = 90
        self.moving = False
        self.last_command_time = 0.0
        
        # Movement history for analysis
        self.position_history: List[Tuple[float, float]] = []
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update servo position"""
        self.last_update = sim_time
        
        if self.moving and self.current_position != self.target_position:
            speed = self.get_parameter("speed")  # degrees per second
            max_move = speed * dt
            
            diff = self.target_position - self.current_position
            if abs(diff) <= max_move:
                self.current_position = self.target_position
                self.moving = False
            else:
                self.current_position += max_move if diff > 0 else -max_move
                
            # Record position history
            self.position_history.append((sim_time, self.current_position))
            if len(self.position_history) > 1000:  # Limit history
                self.position_history.pop(0)
                
    def set_angle(self, angle: float) -> None:
        """Set target servo angle"""
        angle = max(0, min(180, angle))
        self.target_position = angle
        self.set_parameter("position", angle)
        
        if abs(self.current_position - self.target_position) > 0.1:
            self.moving = True
            
    def get_pulse_width(self) -> float:
        """Get current PWM pulse width in milliseconds"""
        min_pulse = self.get_parameter("min_pulse")
        max_pulse = self.get_parameter("max_pulse")
        
        # Linear interpolation between min and max pulse
        ratio = self.current_position / 180.0
        return min_pulse + (max_pulse - min_pulse) * ratio
        
    def get_duty_cycle(self) -> float:
        """Get PWM duty cycle (0-1)"""
        frequency = self.get_parameter("frequency")
        pulse_width_ms = self.get_pulse_width()
        period_ms = 1000.0 / frequency
        
        return pulse_width_ms / period_ms
        
    def is_moving(self) -> bool:
        """Check if servo is currently moving"""
        return self.moving
        
    def get_load(self) -> float:
        """Get simulated load (0-100%)"""
        # Simulate higher load when moving or at extreme positions
        load = 10  # Base load
        
        if self.moving:
            load += 30
            
        # Higher load at extremes
        if self.current_position < 10 or self.current_position > 170:
            load += 20
            
        return min(100, load)
        
    def reset(self) -> None:
        """Reset servo to center position"""
        self.set_angle(90)
        self.current_position = 90
        self.moving = False
        self.position_history.clear()


class StepperMotor(VirtualDevice):
    """Stepper Motor with A4988 Driver"""
    
    def __init__(self, name: str = "Stepper", step_pin: int = 18, dir_pin: int = 19):
        super().__init__(name, "actuator")
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        
        # Parameters
        self.parameters = {
            "steps_per_rev": DeviceParameter("Steps/Rev", 200, 48, 400, "", "Steps per revolution"),
            "max_speed": DeviceParameter("Max Speed", 1000, 1, 5000, "steps/s", "Maximum step rate"),
            "acceleration": DeviceParameter("Acceleration", 500, 10, 2000, "steps/s²", "Acceleration rate"),
            "microsteps": DeviceParameter("Microsteps", 1, 1, 32, "", "Microstepping factor"),
            "current_limit": DeviceParameter("Current Limit", 1.0, 0.1, 3.0, "A", "Motor current limit")
        }
        
        # State
        self.position = 0  # Current position in steps
        self.target_position = 0
        self.velocity = 0.0  # Current velocity in steps/s
        self.direction = 1  # 1 for forward, -1 for reverse
        self.moving = False
        
        # Step tracking
        self.total_steps = 0
        self.step_history: List[Tuple[float, int]] = []
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update stepper motor state"""
        self.last_update = sim_time
        
        if self.moving and self.position != self.target_position:
            max_speed = self.get_parameter("max_speed")
            acceleration = self.get_parameter("acceleration")
            
            # Calculate required direction
            steps_to_go = self.target_position - self.position
            required_direction = 1 if steps_to_go > 0 else -1
            
            # Update velocity with acceleration
            if abs(steps_to_go) > 1:
                target_velocity = required_direction * max_speed
                
                if self.velocity < target_velocity:
                    self.velocity = min(target_velocity, self.velocity + acceleration * dt)
                elif self.velocity > target_velocity:
                    self.velocity = max(target_velocity, self.velocity - acceleration * dt)
                    
                # Move based on current velocity
                step_increment = self.velocity * dt
                
                if abs(step_increment) >= 1.0:
                    steps = int(step_increment)
                    self.position += steps
                    self.total_steps += abs(steps)
                    
                    # Record step
                    self.step_history.append((sim_time, steps))
                    if len(self.step_history) > 1000:
                        self.step_history.pop(0)
            else:
                self.position = self.target_position
                self.velocity = 0
                self.moving = False
                
    def step(self, steps: int) -> None:
        """Move specified number of steps"""
        self.target_position += steps
        self.moving = True
        
    def move_to(self, position: int) -> None:
        """Move to absolute position"""
        self.target_position = position
        self.moving = True
        
    def rotate_degrees(self, degrees: float) -> None:
        """Rotate by specified degrees"""
        steps_per_rev = self.get_parameter("steps_per_rev")
        microsteps = self.get_parameter("microsteps")
        
        total_steps_per_rev = steps_per_rev * microsteps
        steps = int((degrees / 360.0) * total_steps_per_rev)
        self.step(steps)
        
    def get_angle(self) -> float:
        """Get current angle in degrees"""
        steps_per_rev = self.get_parameter("steps_per_rev")
        microsteps = self.get_parameter("microsteps")
        
        total_steps_per_rev = steps_per_rev * microsteps
        return (self.position % total_steps_per_rev) * 360.0 / total_steps_per_rev
        
    def stop(self) -> None:
        """Stop motor immediately"""
        self.target_position = self.position
        self.velocity = 0
        self.moving = False
        
    def home(self) -> None:
        """Return to home position (0)"""
        self.move_to(0)
        
    def get_rpm(self) -> float:
        """Get current RPM"""
        steps_per_rev = self.get_parameter("steps_per_rev")
        microsteps = self.get_parameter("microsteps")
        
        total_steps_per_rev = steps_per_rev * microsteps
        if total_steps_per_rev > 0:
            return abs(self.velocity) * 60.0 / total_steps_per_rev
        return 0.0
        
    def reset(self) -> None:
        """Reset motor"""
        self.position = 0
        self.target_position = 0
        self.velocity = 0
        self.moving = False
        self.total_steps = 0
        self.step_history.clear()


class DCMotor(VirtualDevice):
    """DC Motor with H-Bridge Control"""
    
    def __init__(self, name: str = "DCMotor", pins: Tuple[int, int] = (18, 19)):
        super().__init__(name, "actuator")
        self.in1_pin, self.in2_pin = pins
        
        # Parameters
        self.parameters = {
            "speed": DeviceParameter("Speed", 0, -100, 100, "%", "Motor speed (-100 to 100)"),
            "voltage": DeviceParameter("Voltage", 12.0, 3.0, 24.0, "V", "Supply voltage"),
            "current": DeviceParameter("Current", 0.5, 0.1, 5.0, "A", "Motor current"),
            "inertia": DeviceParameter("Inertia", 0.1, 0.01, 1.0, "", "Rotational inertia"),
            "friction": DeviceParameter("Friction", 0.05, 0.0, 0.5, "", "Friction coefficient")
        }
        
        # State
        self.rpm = 0.0
        self.direction = 0  # -1, 0, 1
        self.pwm_duty = 0.0
        self.brake_active = False
        
        # Physics simulation
        self.angular_velocity = 0.0  # rad/s
        self.torque = 0.0
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update motor physics"""
        self.last_update = sim_time
        
        speed_percent = self.get_parameter("speed")
        inertia = self.get_parameter("inertia")
        friction = self.get_parameter("friction")
        
        # Calculate target angular velocity
        max_rpm = 3000  # Typical DC motor max RPM
        target_rpm = (speed_percent / 100.0) * max_rpm
        target_angular_velocity = target_rpm * 2 * math.pi / 60.0
        
        # Simple physics: torque = inertia * angular_acceleration + friction
        friction_torque = friction * self.angular_velocity
        
        if self.brake_active:
            # Strong braking torque
            brake_torque = -10 * self.angular_velocity
            self.angular_velocity += brake_torque * dt / inertia
        else:
            # Motor torque to reach target velocity
            velocity_error = target_angular_velocity - self.angular_velocity
            motor_torque = velocity_error * 2.0  # Proportional control
            
            net_torque = motor_torque - friction_torque
            self.angular_velocity += net_torque * dt / inertia
            
        # Update RPM
        self.rpm = self.angular_velocity * 60.0 / (2 * math.pi)
        
        # Update direction
        if abs(self.rpm) < 1:
            self.direction = 0
        else:
            self.direction = 1 if self.rpm > 0 else -1
            
    def set_speed(self, speed: float) -> None:
        """Set motor speed (-100 to 100)"""
        speed = max(-100, min(100, speed))
        self.set_parameter("speed", speed)
        self.brake_active = False
        
    def forward(self, speed: float = 50) -> None:
        """Run motor forward"""
        self.set_speed(abs(speed))
        
    def reverse(self, speed: float = 50) -> None:
        """Run motor in reverse"""
        self.set_speed(-abs(speed))
        
    def brake(self) -> None:
        """Apply brake"""
        self.brake_active = True
        self.set_parameter("speed", 0)
        
    def coast(self) -> None:
        """Let motor coast to stop"""
        self.brake_active = False
        self.set_parameter("speed", 0)
        
    def get_power_consumption(self) -> float:
        """Get power consumption in watts"""
        voltage = self.get_parameter("voltage")
        current = self.get_parameter("current")
        
        # Current proportional to load
        load_factor = abs(self.get_parameter("speed")) / 100.0
        actual_current = current * load_factor
        
        return voltage * actual_current
        
    def reset(self) -> None:
        """Reset motor"""
        self.set_speed(0)
        self.angular_velocity = 0.0
        self.rpm = 0.0
        self.direction = 0
        self.brake_active = False


class Buzzer(VirtualDevice):
    """Piezo Buzzer"""
    
    def __init__(self, name: str = "Buzzer", pin: int = 18):
        super().__init__(name, "actuator")
        self.pin = pin
        
        # Parameters
        self.parameters = {
            "frequency": DeviceParameter("Frequency", 1000, 100, 10000, "Hz", "Buzzer frequency"),
            "volume": DeviceParameter("Volume", 50, 0, 100, "%", "Buzzer volume"),
            "active": DeviceParameter("Active", False, description="Buzzer on/off"),
            "duty_cycle": DeviceParameter("Duty Cycle", 50, 0, 100, "%", "PWM duty cycle")
        }
        
        # State
        self.tone_active = False
        self.current_note = ""
        
        # Musical notes (frequency in Hz)
        self.notes = {
            'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
            'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
            'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
            'G5': 783.99, 'A5': 880.00, 'B5': 987.77
        }
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update buzzer state"""
        self.last_update = sim_time
        
    def beep(self, frequency: float, duration: float = 0.1) -> None:
        """Generate a beep"""
        self.set_parameter("frequency", frequency)
        self.set_parameter("active", True)
        self.tone_active = True
        
        # In a real implementation, this would schedule a stop after duration
        
    def play_note(self, note: str, duration: float = 0.5) -> None:
        """Play a musical note"""
        if note.upper() in self.notes:
            frequency = self.notes[note.upper()]
            self.current_note = note.upper()
            self.beep(frequency, duration)
            
    def play_melody(self, notes: List[Tuple[str, float]]) -> None:
        """Play a sequence of notes"""
        # In a real implementation, this would schedule the note sequence
        for note, duration in notes:
            self.play_note(note, duration)
            
    def stop(self) -> None:
        """Stop buzzer"""
        self.set_parameter("active", False)
        self.tone_active = False
        self.current_note = ""
        
    def chirp(self, start_freq: float = 1000, end_freq: float = 2000, duration: float = 0.2) -> None:
        """Generate a frequency sweep"""
        # Simplified - would implement frequency ramping in real version
        self.beep(start_freq, duration / 2)
        self.beep(end_freq, duration / 2)
        
    def get_sound_level(self) -> float:
        """Get sound level in dB (simulated)"""
        if self.get_parameter("active"):
            volume = self.get_parameter("volume")
            return 40 + (volume / 100.0) * 40  # 40-80 dB range
        return 0
        
    def reset(self) -> None:
        """Reset buzzer"""
        self.stop()


class Relay(VirtualDevice):
    """Electromagnetic Relay"""
    
    def __init__(self, name: str = "Relay", coil_pin: int = 18):
        super().__init__(name, "actuator")
        self.coil_pin = coil_pin
        
        # Parameters
        self.parameters = {
            "energized": DeviceParameter("Energized", False, description="Relay coil energized"),
            "coil_voltage": DeviceParameter("Coil Voltage", 5.0, 3.0, 24.0, "V", "Coil operating voltage"),
            "coil_current": DeviceParameter("Coil Current", 50, 10, 200, "mA", "Coil current"),
            "switching_time": DeviceParameter("Switching Time", 5, 1, 50, "ms", "Contact switching time"),
            "contact_rating": DeviceParameter("Contact Rating", 10, 1, 30, "A", "Contact current rating")
        }
        
        # State
        self.contacts_closed = False
        self.switching = False
        self.switch_start_time = 0.0
        
        # Contact states (NO, NC, COM)
        self.no_contact = False  # Normally Open
        self.nc_contact = True   # Normally Closed
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update relay state"""
        self.last_update = sim_time
        
        energized = self.get_parameter("energized")
        switching_time_ms = self.get_parameter("switching_time")
        switching_time_s = switching_time_ms / 1000.0
        
        if self.switching:
            # Check if switching is complete
            if sim_time - self.switch_start_time >= switching_time_s:
                self.switching = False
                self.contacts_closed = energized
                self.no_contact = energized
                self.nc_contact = not energized
        elif self.contacts_closed != energized:
            # Start switching
            self.switching = True
            self.switch_start_time = sim_time
            
    def energize(self) -> None:
        """Energize relay coil"""
        self.set_parameter("energized", True)
        
    def de_energize(self) -> None:
        """De-energize relay coil"""
        self.set_parameter("energized", False)
        
    def toggle(self) -> None:
        """Toggle relay state"""
        current_state = self.get_parameter("energized")
        self.set_parameter("energized", not current_state)
        
    def is_switching(self) -> bool:
        """Check if relay is currently switching"""
        return self.switching
        
    def get_contact_state(self, contact_type: str) -> bool:
        """Get contact state (NO, NC, or COM)"""
        if contact_type.upper() == "NO":
            return self.no_contact
        elif contact_type.upper() == "NC":
            return self.nc_contact
        elif contact_type.upper() == "COM":
            return True  # Common is always connected
        return False
        
    def get_power_consumption(self) -> float:
        """Get coil power consumption in mW"""
        if self.get_parameter("energized"):
            voltage = self.get_parameter("coil_voltage")
            current_ma = self.get_parameter("coil_current")
            return voltage * current_ma
        return 0
        
    def reset(self) -> None:
        """Reset relay"""
        self.de_energize()
        self.switching = False
        self.contacts_closed = False
        self.no_contact = False
        self.nc_contact = True