"""
Test for LED Blink Example
"""

import pytest
import time
from pistudio import PiSimulator, Project
from testkit import PinAssertions


class TestBlinkLED:
    """Test cases for LED blink functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create a minimal project for testing
        self.project_config = {
            "name": "Test LED Blink",
            "template": "python",
            "board": "pi4",
            "devices": [
                {
                    "type": "led",
                    "name": "LED1",
                    "connection": {"pin": 18}
                }
            ],
            "connections": []
        }
        
        # Create simulator
        self.simulator = PiSimulator(self.project_config)
        self.pin_assertions = PinAssertions(self.simulator.event_bus)
        
    def test_led_blink_basic(self):
        """Test basic LED blinking functionality"""
        # Start simulation
        self.simulator.start()
        
        try:
            # Run blink code
            code = '''
import RPiSim.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)

# Blink 3 times
for i in range(3):
    GPIO.output(18, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(18, GPIO.LOW)
    time.sleep(0.1)

GPIO.cleanup()
'''
            
            self.simulator.execute_code(code)
            
            # Assert LED toggled at least 6 times (3 on + 3 off)
            self.pin_assertions.assert_pin_toggle(18, min_edges=6, within_ms=2000)
            
        finally:
            self.simulator.stop()
            
    def test_led_on_off_timing(self):
        """Test LED on/off timing accuracy"""
        self.simulator.start()
        
        try:
            code = '''
import RPiSim.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)

GPIO.output(18, GPIO.HIGH)
time.sleep(0.5)
GPIO.output(18, GPIO.LOW)

GPIO.cleanup()
'''
            
            start_time = time.time()
            self.simulator.execute_code(code)
            
            # Assert LED goes high quickly
            self.pin_assertions.assert_pin_high(18, within_ms=100)
            
            # Assert LED goes low after ~500ms
            self.pin_assertions.assert_pin_low(18, within_ms=600)
            
        finally:
            self.simulator.stop()
            
    def test_multiple_leds(self):
        """Test multiple LED control"""
        # Add second LED to project
        self.project_config["devices"].append({
            "type": "led",
            "name": "LED2", 
            "connection": {"pin": 19}
        })
        
        self.simulator = PiSimulator(self.project_config)
        self.pin_assertions = PinAssertions(self.simulator.event_bus)
        self.simulator.start()
        
        try:
            code = '''
import RPiSim.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(19, GPIO.OUT)

# Alternating blink
for i in range(3):
    GPIO.output(18, GPIO.HIGH)
    GPIO.output(19, GPIO.LOW)
    time.sleep(0.1)
    
    GPIO.output(18, GPIO.LOW)
    GPIO.output(19, GPIO.HIGH)
    time.sleep(0.1)

GPIO.cleanup()
'''
            
            self.simulator.execute_code(code)
            
            # Both LEDs should toggle
            self.pin_assertions.assert_pin_toggle(18, min_edges=6, within_ms=2000)
            self.pin_assertions.assert_pin_toggle(19, min_edges=6, within_ms=2000)
            
        finally:
            self.simulator.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])