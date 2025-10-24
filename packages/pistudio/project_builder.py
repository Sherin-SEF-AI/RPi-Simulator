"""
Interactive Project Builder - Guided project creation and configuration
"""

import json
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from .project import Project, DeviceConfig, ConnectionConfig


class ProjectTemplate:
    """Project template definition"""
    
    def __init__(self, name: str, description: str, devices: List[Dict], 
                 connections: List[Dict], code: str, difficulty: str = "beginner"):
        self.name = name
        self.description = description
        self.devices = devices
        self.connections = connections
        self.code = code
        self.difficulty = difficulty


class ProjectBuilder:
    """Interactive project builder with templates and wizards"""
    
    def __init__(self):
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, ProjectTemplate]:
        """Load built-in project templates"""
        templates = {}
        
        # LED Blink Template
        templates["led_blink"] = ProjectTemplate(
            name="LED Blink",
            description="Basic LED blinking - perfect for beginners",
            devices=[
                {"type": "led", "name": "LED1", "connection": {"pin": 18}}
            ],
            connections=[
                {"from_pin": "GPIO18", "to_pin": "LED1:anode", "wire_color": "red"},
                {"from_pin": "GND", "to_pin": "LED1:cathode", "wire_color": "black"}
            ],
            code='''#!/usr/bin/env python3
import RPiSim.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
LED_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    print("LED Blink Demo - Press Ctrl+C to stop")
    while True:
        GPIO.output(LED_PIN, GPIO.HIGH)
        print("LED ON")
        time.sleep(0.5)
        
        GPIO.output(LED_PIN, GPIO.LOW)
        print("LED OFF")
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\\nStopping...")
    
finally:
    GPIO.cleanup()
''',
            difficulty="beginner"
        )
        
        # Traffic Light Template
        templates["traffic_light"] = ProjectTemplate(
            name="Traffic Light Controller",
            description="3-LED traffic light sequence with timing control",
            devices=[
                {"type": "led", "name": "Red_LED", "connection": {"pin": 18}, "parameters": {"color": "red"}},
                {"type": "led", "name": "Yellow_LED", "connection": {"pin": 19}, "parameters": {"color": "yellow"}},
                {"type": "led", "name": "Green_LED", "connection": {"pin": 20}, "parameters": {"color": "green"}}
            ],
            connections=[
                {"from_pin": "GPIO18", "to_pin": "Red_LED:anode", "wire_color": "red"},
                {"from_pin": "GPIO19", "to_pin": "Yellow_LED:anode", "wire_color": "yellow"},
                {"from_pin": "GPIO20", "to_pin": "Green_LED:anode", "wire_color": "green"},
                {"from_pin": "GND", "to_pin": "Red_LED:cathode", "wire_color": "black"},
                {"from_pin": "GND", "to_pin": "Yellow_LED:cathode", "wire_color": "black"},
                {"from_pin": "GND", "to_pin": "Green_LED:cathode", "wire_color": "black"}
            ],
            code='''#!/usr/bin/env python3
import RPiSim.GPIO as GPIO
import time

# Pin definitions
RED_PIN = 18
YELLOW_PIN = 19
GREEN_PIN = 20

# Timing (seconds)
RED_TIME = 5
YELLOW_TIME = 2
GREEN_TIME = 5

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_PIN, GPIO.OUT)
GPIO.setup(YELLOW_PIN, GPIO.OUT)
GPIO.setup(GREEN_PIN, GPIO.OUT)

def all_off():
    GPIO.output(RED_PIN, GPIO.LOW)
    GPIO.output(YELLOW_PIN, GPIO.LOW)
    GPIO.output(GREEN_PIN, GPIO.LOW)

try:
    print("Traffic Light Controller - Press Ctrl+C to stop")
    while True:
        # Red light
        all_off()
        GPIO.output(RED_PIN, GPIO.HIGH)
        print("RED - Stop!")
        time.sleep(RED_TIME)
        
        # Green light
        all_off()
        GPIO.output(GREEN_PIN, GPIO.HIGH)
        print("GREEN - Go!")
        time.sleep(GREEN_TIME)
        
        # Yellow light
        all_off()
        GPIO.output(YELLOW_PIN, GPIO.HIGH)
        print("YELLOW - Caution!")
        time.sleep(YELLOW_TIME)
        
except KeyboardInterrupt:
    print("\\nStopping traffic light...")
    
finally:
    all_off()
    GPIO.cleanup()
''',
            difficulty="beginner"
        )
        
        # Temperature Monitor Template
        templates["temp_monitor"] = ProjectTemplate(
            name="Temperature Monitor",
            description="BME280 sensor with LCD display and alerts",
            devices=[
                {"type": "bme280", "name": "TempSensor", "connection": {"i2c": 0x76}},
                {"type": "lcd1602", "name": "Display", "connection": {"i2c": 0x27}},
                {"type": "led", "name": "Alert_LED", "connection": {"pin": 18}, "parameters": {"color": "red"}},
                {"type": "buzzer", "name": "Buzzer", "connection": {"pin": 19}}
            ],
            connections=[
                {"from_pin": "GPIO2", "to_pin": "TempSensor:SDA", "wire_color": "blue"},
                {"from_pin": "GPIO3", "to_pin": "TempSensor:SCL", "wire_color": "yellow"},
                {"from_pin": "GPIO2", "to_pin": "Display:SDA", "wire_color": "blue"},
                {"from_pin": "GPIO3", "to_pin": "Display:SCL", "wire_color": "yellow"},
                {"from_pin": "3V3", "to_pin": "TempSensor:VCC", "wire_color": "red"},
                {"from_pin": "5V", "to_pin": "Display:VCC", "wire_color": "red"},
                {"from_pin": "GND", "to_pin": "TempSensor:GND", "wire_color": "black"},
                {"from_pin": "GND", "to_pin": "Display:GND", "wire_color": "black"}
            ],
            code='''#!/usr/bin/env python3
from sim_i2c import I2C
import RPiSim.GPIO as GPIO
import time

# Configuration
TEMP_THRESHOLD = 30.0  # Alert above 30°C
ALERT_LED_PIN = 18
BUZZER_PIN = 19

# I2C addresses
BME280_ADDR = 0x76
LCD_ADDR = 0x27

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(ALERT_LED_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

i2c = I2C(1)

def read_bme280():
    """Read temperature from BME280"""
    try:
        # Configure BME280
        i2c.write_byte_data(BME280_ADDR, 0xF4, 0x27)
        time.sleep(0.1)
        
        # Read data
        data = i2c.read_i2c_block_data(BME280_ADDR, 0xF7, 6)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        
        # Convert to Celsius (simplified)
        temperature = (temp_raw / 5120.0) - 40.0
        return temperature
    except:
        return None

def update_lcd(temp, humidity, pressure):
    """Update LCD display"""
    try:
        # Clear display
        i2c.write_byte_data(LCD_ADDR, 0x00, 0x01)
        time.sleep(0.01)
        
        # Write temperature line
        line1 = f"Temp: {temp:.1f}C"
        for char in line1:
            i2c.write_byte_data(LCD_ADDR, 0x40, ord(char))
            
        # Set cursor to line 2
        i2c.write_byte_data(LCD_ADDR, 0x00, 0xC0)
        
        # Write humidity line
        line2 = f"Hum: {humidity:.1f}%"
        for char in line2:
            i2c.write_byte_data(LCD_ADDR, 0x40, ord(char))
    except:
        pass

def alert(active):
    """Control alert LED and buzzer"""
    GPIO.output(ALERT_LED_PIN, GPIO.HIGH if active else GPIO.LOW)
    GPIO.output(BUZZER_PIN, GPIO.HIGH if active else GPIO.LOW)

try:
    print("Temperature Monitor Starting...")
    
    while True:
        temp = read_bme280()
        
        if temp is not None:
            # Simulate humidity and pressure
            humidity = 50.0
            pressure = 1013.25
            
            print(f"Temperature: {temp:.1f}°C")
            update_lcd(temp, humidity, pressure)
            
            # Check for alert condition
            if temp > TEMP_THRESHOLD:
                print("⚠️  HIGH TEMPERATURE ALERT!")
                alert(True)
                time.sleep(0.5)
                alert(False)
                time.sleep(0.5)
            else:
                alert(False)
        else:
            print("Sensor read error")
            
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\\nStopping monitor...")
    
finally:
    alert(False)
    GPIO.cleanup()
''',
            difficulty="intermediate"
        )
        
        # Servo Control Template
        templates["servo_control"] = ProjectTemplate(
            name="Servo Motor Control",
            description="Interactive servo control with button input",
            devices=[
                {"type": "servo", "name": "Servo1", "connection": {"pin": 18}},
                {"type": "button", "name": "Left_Btn", "connection": {"pin": 2}},
                {"type": "button", "name": "Right_Btn", "connection": {"pin": 3}},
                {"type": "led", "name": "Status_LED", "connection": {"pin": 20}}
            ],
            connections=[
                {"from_pin": "GPIO18", "to_pin": "Servo1:signal", "wire_color": "orange"},
                {"from_pin": "5V", "to_pin": "Servo1:power", "wire_color": "red"},
                {"from_pin": "GND", "to_pin": "Servo1:ground", "wire_color": "black"},
                {"from_pin": "GPIO2", "to_pin": "Left_Btn:pin", "wire_color": "blue"},
                {"from_pin": "GPIO3", "to_pin": "Right_Btn:pin", "wire_color": "green"}
            ],
            code='''#!/usr/bin/env python3
import RPiSim.GPIO as GPIO
import time

# Pin definitions
SERVO_PIN = 18
LEFT_BTN = 2
RIGHT_BTN = 3
STATUS_LED = 20

# Servo parameters
current_angle = 90
min_angle = 0
max_angle = 180
step_size = 10

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(LEFT_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RIGHT_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(STATUS_LED, GPIO.OUT)

# Create PWM instance
servo_pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz
servo_pwm.start(0)

def angle_to_duty_cycle(angle):
    """Convert angle to PWM duty cycle"""
    # 0° = 2.5% duty, 180° = 12.5% duty
    return 2.5 + (angle / 180.0) * 10.0

def set_servo_angle(angle):
    """Set servo to specific angle"""
    duty = angle_to_duty_cycle(angle)
    servo_pwm.ChangeDutyCycle(duty)
    time.sleep(0.1)
    servo_pwm.ChangeDutyCycle(0)  # Stop PWM signal

def blink_status():
    """Blink status LED"""
    GPIO.output(STATUS_LED, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(STATUS_LED, GPIO.LOW)

try:
    print("Servo Control Demo")
    print("Left button: rotate left, Right button: rotate right")
    print("Press Ctrl+C to stop")
    
    # Set initial position
    set_servo_angle(current_angle)
    print(f"Initial position: {current_angle}°")
    
    while True:
        # Check left button
        if GPIO.input(LEFT_BTN) == GPIO.LOW:
            if current_angle > min_angle:
                current_angle -= step_size
                set_servo_angle(current_angle)
                print(f"Moved left to: {current_angle}°")
                blink_status()
            time.sleep(0.2)  # Debounce
            
        # Check right button
        if GPIO.input(RIGHT_BTN) == GPIO.LOW:
            if current_angle < max_angle:
                current_angle += step_size
                set_servo_angle(current_angle)
                print(f"Moved right to: {current_angle}°")
                blink_status()
            time.sleep(0.2)  # Debounce
            
        time.sleep(0.05)
        
except KeyboardInterrupt:
    print("\\nStopping servo control...")
    
finally:
    servo_pwm.stop()
    GPIO.cleanup()
''',
            difficulty="intermediate"
        )
        
        return templates
        
    def list_templates(self, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available project templates"""
        templates = []
        
        for key, template in self.templates.items():
            if difficulty is None or template.difficulty == difficulty:
                templates.append({
                    "id": key,
                    "name": template.name,
                    "description": template.description,
                    "difficulty": template.difficulty,
                    "device_count": len(template.devices),
                    "connection_count": len(template.connections)
                })
                
        return templates
        
    def create_from_template(self, template_id: str, project_name: str, 
                           project_path: Optional[Path] = None) -> Project:
        """Create project from template"""
        if template_id not in self.templates:
            raise ValueError(f"Template '{template_id}' not found")
            
        template = self.templates[template_id]
        
        if project_path is None:
            project_path = Path(project_name)
            
        # Create project directory
        project_path.mkdir(exist_ok=True)
        (project_path / "src").mkdir(exist_ok=True)
        
        # Create project config
        config = {
            "name": project_name,
            "template": template_id,
            "board": "pi4",
            "version": "0.1.0",
            "devices": template.devices,
            "connections": template.connections,
            "environment": {
                "temperature": 25.0,
                "humidity": 50.0,
                "light_level": 100.0
            }
        }
        
        # Save main code file
        with open(project_path / "src" / "main.py", "w") as f:
            f.write(template.code)
            
        # Save project config
        with open(project_path / "pistudio.json", "w") as f:
            json.dump(config, f, indent=2)
            
        return Project.load(project_path)
        
    def interactive_wizard(self) -> Dict[str, Any]:
        """Interactive project creation wizard"""
        print("🚀 PiStudio Project Wizard")
        print("=" * 40)
        
        # Project name
        project_name = input("Enter project name: ").strip()
        if not project_name:
            project_name = "my_pi_project"
            
        # Board selection
        print("\\nSelect Raspberry Pi board:")
        boards = [
            ("pi4", "Raspberry Pi 4 Model B (recommended)"),
            ("pi3b", "Raspberry Pi 3 Model B+"),
            ("zero2w", "Raspberry Pi Zero 2 W")
        ]
        
        for i, (board_id, board_name) in enumerate(boards, 1):
            print(f"  {i}. {board_name}")
            
        board_choice = input("Enter choice (1-3) [1]: ").strip()
        board_map = {"1": "pi4", "2": "pi3b", "3": "zero2w", "": "pi4"}
        board = board_map.get(board_choice, "pi4")
        
        # Template or custom
        print("\\nProject type:")
        print("  1. Use template (recommended for beginners)")
        print("  2. Create custom project")
        
        type_choice = input("Enter choice (1-2) [1]: ").strip()
        
        if type_choice == "2":
            return self._custom_project_wizard(project_name, board)
        else:
            return self._template_wizard(project_name, board)
            
    def _template_wizard(self, project_name: str, board: str) -> Dict[str, Any]:
        """Template selection wizard"""
        print("\\nAvailable templates:")
        
        # Group by difficulty
        difficulties = ["beginner", "intermediate", "advanced"]
        
        for difficulty in difficulties:
            templates = self.list_templates(difficulty)
            if templates:
                print(f"\\n{difficulty.title()} Projects:")
                for i, template in enumerate(templates, 1):
                    print(f"  {template['id']}: {template['name']}")
                    print(f"     {template['description']}")
                    print(f"     Devices: {template['device_count']}, "
                          f"Connections: {template['connection_count']}")
                    
        template_id = input("\\nEnter template ID: ").strip()
        
        if template_id in self.templates:
            project = self.create_from_template(template_id, project_name)
            return {
                "success": True,
                "project": project,
                "message": f"Project '{project_name}' created from template '{template_id}'"
            }
        else:
            return {
                "success": False,
                "message": f"Template '{template_id}' not found"
            }
            
    def _custom_project_wizard(self, project_name: str, board: str) -> Dict[str, Any]:
        """Custom project creation wizard"""
        print("\\n🔧 Custom Project Setup")
        
        devices = []
        connections = []
        
        # Device selection
        print("\\nAdd devices to your project:")
        available_devices = {
            "led": "LED (Light Emitting Diode)",
            "rgb_led": "RGB LED (Multi-color LED)",
            "button": "Push Button",
            "servo": "Servo Motor",
            "stepper": "Stepper Motor",
            "dc_motor": "DC Motor",
            "buzzer": "Piezo Buzzer",
            "relay": "Electromagnetic Relay",
            "dht22": "DHT22 Temperature/Humidity Sensor",
            "bme280": "BME280 Environmental Sensor (I2C)",
            "hcsr04": "HC-SR04 Ultrasonic Distance Sensor",
            "mpu6050": "MPU6050 6-axis IMU (I2C)",
            "lcd1602": "16x2 Character LCD (I2C)",
            "ssd1306": "128x64 OLED Display (I2C)",
            "neopixel": "NeoPixel LED Strip",
            "7segment": "7-Segment Display"
        }
        
        print("Available devices:")
        for device_id, description in available_devices.items():
            print(f"  {device_id}: {description}")
            
        while True:
            device_type = input("\\nAdd device (type 'done' to finish): ").strip().lower()
            
            if device_type == "done":
                break
                
            if device_type not in available_devices:
                print(f"Unknown device type: {device_type}")
                continue
                
            device_name = input(f"Enter name for {device_type}: ").strip()
            if not device_name:
                device_name = f"{device_type}1"
                
            # Get connection info
            connection = self._get_device_connection(device_type)
            
            devices.append({
                "type": device_type,
                "name": device_name,
                "connection": connection
            })
            
            print(f"✓ Added {device_name} ({device_type})")
            
        # Create project
        project_path = Path(project_name)
        project_path.mkdir(exist_ok=True)
        (project_path / "src").mkdir(exist_ok=True)
        
        config = {
            "name": project_name,
            "template": "custom",
            "board": board,
            "version": "0.1.0",
            "devices": devices,
            "connections": connections,
            "environment": {
                "temperature": 25.0,
                "humidity": 50.0,
                "light_level": 100.0
            }
        }
        
        # Generate basic code template
        code = self._generate_basic_code(devices)
        
        with open(project_path / "src" / "main.py", "w") as f:
            f.write(code)
            
        with open(project_path / "pistudio.json", "w") as f:
            json.dump(config, f, indent=2)
            
        project = Project.load(project_path)
        
        return {
            "success": True,
            "project": project,
            "message": f"Custom project '{project_name}' created with {len(devices)} devices"
        }
        
    def _get_device_connection(self, device_type: str) -> Dict[str, Any]:
        """Get connection parameters for device type"""
        if device_type in ["led", "button", "buzzer", "relay"]:
            pin = input(f"Enter GPIO pin number: ").strip()
            return {"pin": int(pin) if pin.isdigit() else 18}
            
        elif device_type in ["rgb_led"]:
            r_pin = input("Enter Red pin: ").strip()
            g_pin = input("Enter Green pin: ").strip()
            b_pin = input("Enter Blue pin: ").strip()
            return {
                "pins": [
                    int(r_pin) if r_pin.isdigit() else 18,
                    int(g_pin) if g_pin.isdigit() else 19,
                    int(b_pin) if b_pin.isdigit() else 20
                ]
            }
            
        elif device_type in ["servo", "dc_motor", "neopixel"]:
            pin = input(f"Enter control pin: ").strip()
            return {"pin": int(pin) if pin.isdigit() else 18}
            
        elif device_type in ["stepper"]:
            step_pin = input("Enter step pin: ").strip()
            dir_pin = input("Enter direction pin: ").strip()
            return {
                "step_pin": int(step_pin) if step_pin.isdigit() else 18,
                "dir_pin": int(dir_pin) if dir_pin.isdigit() else 19
            }
            
        elif device_type in ["hcsr04"]:
            trig_pin = input("Enter trigger pin: ").strip()
            echo_pin = input("Enter echo pin: ").strip()
            return {
                "trigger_pin": int(trig_pin) if trig_pin.isdigit() else 23,
                "echo_pin": int(echo_pin) if echo_pin.isdigit() else 24
            }
            
        elif device_type in ["bme280", "mpu6050", "lcd1602", "ssd1306"]:
            addr = input(f"Enter I2C address (hex, e.g., 0x76): ").strip()
            if addr.startswith("0x"):
                return {"i2c": int(addr, 16)}
            else:
                # Default addresses
                defaults = {
                    "bme280": 0x76,
                    "mpu6050": 0x68,
                    "lcd1602": 0x27,
                    "ssd1306": 0x3C
                }
                return {"i2c": defaults.get(device_type, 0x76)}
                
        elif device_type in ["7segment"]:
            pins = []
            for segment in ["a", "b", "c", "d", "e", "f", "g", "dp"]:
                pin = input(f"Enter pin for segment {segment}: ").strip()
                pins.append(int(pin) if pin.isdigit() else (2 + len(pins)))
            return {"pins": pins}
            
        else:
            return {"pin": 18}  # Default
            
    def _generate_basic_code(self, devices: List[Dict]) -> str:
        """Generate basic code template for devices"""
        code = '''#!/usr/bin/env python3
"""
Custom PiStudio Project
Generated by Project Wizard
"""

import RPiSim.GPIO as GPIO
import time

# Setup GPIO
GPIO.setmode(GPIO.BCM)

'''
        
        # Add device setup
        for device in devices:
            device_type = device["type"]
            device_name = device["name"]
            connection = device["connection"]
            
            if device_type in ["led", "buzzer", "relay"]:
                pin = connection.get("pin", 18)
                code += f"# {device_name} setup\\n"
                code += f"{device_name.upper()}_PIN = {pin}\\n"
                code += f"GPIO.setup({device_name.upper()}_PIN, GPIO.OUT)\\n\\n"
                
            elif device_type == "button":
                pin = connection.get("pin", 2)
                code += f"# {device_name} setup\\n"
                code += f"{device_name.upper()}_PIN = {pin}\\n"
                code += f"GPIO.setup({device_name.upper()}_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)\\n\\n"
                
        code += '''try:
    print("Project starting... Press Ctrl+C to stop")
    
    while True:
        # Add your main code here
        print("Running...")
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\\nStopping...")
    
finally:
    GPIO.cleanup()
'''
        
        return code
        
    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed template information"""
        if template_id not in self.templates:
            return None
            
        template = self.templates[template_id]
        
        return {
            "name": template.name,
            "description": template.description,
            "difficulty": template.difficulty,
            "devices": template.devices,
            "connections": template.connections,
            "code_preview": template.code[:500] + "..." if len(template.code) > 500 else template.code
        }