"""
Project Management
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class DeviceConfig:
    """Device configuration"""
    type: str
    name: str
    connection: Dict[str, Any]
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ConnectionConfig:
    """Pin connection configuration"""
    from_pin: str
    to_pin: str
    wire_color: str = "red"


class Project:
    """PiStudio project management"""
    
    def __init__(self, path: Path, config: Dict[str, Any]):
        self.path = path
        self.config = config
        self.devices: List[DeviceConfig] = []
        self.connections: List[ConnectionConfig] = []
        
        # Load devices and connections from config
        for device_data in config.get('devices', []):
            self.devices.append(DeviceConfig(**device_data))
            
        for conn_data in config.get('connections', []):
            self.connections.append(ConnectionConfig(**conn_data))
    
    @classmethod
    def create(cls, name: str, template: str = "python", board: str = "pi4") -> 'Project':
        """Create a new project"""
        project_path = Path(name)
        
        if project_path.exists():
            raise ValueError(f"Project directory already exists: {name}")
            
        # Create project structure
        project_path.mkdir()
        (project_path / "src").mkdir()
        (project_path / "tests").mkdir()
        
        # Create project config
        config = {
            "name": name,
            "template": template,
            "board": board,
            "version": "0.1.0",
            "devices": [],
            "connections": [],
            "environment": {
                "temperature": 25.0,
                "humidity": 50.0,
                "light_level": 100.0
            }
        }
        
        # Copy template files
        cls._copy_template(template, project_path)
        
        # Save project config
        with open(project_path / "pistudio.json", "w") as f:
            json.dump(config, f, indent=2)
            
        return cls(project_path, config)
    
    @classmethod
    def load(cls, path: Path) -> 'Project':
        """Load existing project"""
        config_file = path / "pistudio.json"
        
        if not config_file.exists():
            raise ValueError(f"No pistudio.json found in {path}")
            
        with open(config_file) as f:
            config = json.load(f)
            
        return cls(path, config)
    
    @classmethod
    def load_current(cls) -> 'Project':
        """Load project from current directory"""
        return cls.load(Path.cwd())
    
    def save(self) -> None:
        """Save project configuration"""
        # Update config with current devices and connections
        self.config['devices'] = [asdict(device) for device in self.devices]
        self.config['connections'] = [asdict(conn) for conn in self.connections]
        
        config_file = self.path / "pistudio.json"
        with open(config_file, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def add_device(self, device_type: str, name: str, connection: Dict[str, Any]) -> None:
        """Add device to project"""
        device = DeviceConfig(device_type, name, connection)
        self.devices.append(device)
    
    def remove_device(self, name: str) -> bool:
        """Remove device from project"""
        for i, device in enumerate(self.devices):
            if device.name == name:
                del self.devices[i]
                return True
        return False
    
    def add_connection(self, from_pin: str, to_pin: str, color: str = "red") -> None:
        """Add pin connection"""
        connection = ConnectionConfig(from_pin, to_pin, color)
        self.connections.append(connection)
    
    def get_device(self, name: str) -> Optional[DeviceConfig]:
        """Get device by name"""
        for device in self.devices:
            if device.name == name:
                return device
        return None
    
    @staticmethod
    def _copy_template(template: str, project_path: Path) -> None:
        """Copy template files to project"""
        # This would copy from templates directory
        # For now, create basic files
        
        if template == "python":
            # Create main.py
            main_py = """#!/usr/bin/env python3
\"\"\"
PiStudio Project - Python Template
\"\"\"

import RPiSim.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
LED_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    print("Starting LED blink demo...")
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
"""
            with open(project_path / "src" / "main.py", "w") as f:
                f.write(main_py)
                
        elif template == "c":
            # Create main.c
            main_c = """/*
 * PiStudio Project - C Template
 */

#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include "pistudio.h"

#define LED_PIN 18

volatile int running = 1;

void signal_handler(int sig) {
    running = 0;
}

int main() {
    signal(SIGINT, signal_handler);
    
    // Setup GPIO
    if (gpio_setup() != 0) {
        printf("Failed to setup GPIO\\n");
        return 1;
    }
    
    gpio_set_mode(LED_PIN, GPIO_OUT);
    
    printf("Starting LED blink demo...\\n");
    
    while (running) {
        gpio_write(LED_PIN, 1);
        printf("LED ON\\n");
        usleep(500000);
        
        gpio_write(LED_PIN, 0);
        printf("LED OFF\\n");
        usleep(500000);
    }
    
    printf("\\nStopping...\\n");
    gpio_cleanup();
    
    return 0;
}
"""
            with open(project_path / "src" / "main.c", "w") as f:
                f.write(main_c)