"""
Main PiStudio Simulator
"""

import time
import threading
from typing import Dict, Any, Optional, List
from pathlib import Path

from sim_core import SimClock, EventBus, Scheduler
from board_pi import Pi4B, Pi3B, PiZero2W
from peripherals import GpioController, I2cController, PwmController
from devices import DHT22, BME280, HCSR04
from runner import CodeRunner


class PiSimulator:
    """
    Main Raspberry Pi Simulator
    
    Coordinates all simulation components and provides high-level interface
    for running embedded code and managing virtual hardware.
    """
    
    def __init__(self, project_config: Dict[str, Any]):
        self.config = project_config
        self.running = False
        
        # Initialize simulation core
        self.clock = SimClock(timestep_us=10)  # 10µs timestep
        self.event_bus = EventBus()
        self.scheduler = Scheduler()
        
        # Initialize board
        self.board = self._create_board()
        
        # Initialize peripherals
        self.gpio = GpioController(self.board.pins, self.event_bus)
        self.i2c = I2cController(1, self.event_bus)  # I2C bus 1
        self.pwm = PwmController(self.event_bus)
        
        # Initialize devices
        self.devices = {}
        self._create_devices()
        
        # Code runner
        self.code_runner = CodeRunner(self)
        
        # Simulation thread
        self.sim_thread = None
        self.stop_event = threading.Event()
        
    def _create_board(self):
        """Create board instance based on config"""
        board_type = self.config.get("board", "pi4")
        
        if board_type == "pi4":
            return Pi4B()
        elif board_type == "pi3b":
            return Pi3B()
        elif board_type == "zero2w":
            return PiZero2W()
        else:
            raise ValueError(f"Unknown board type: {board_type}")
            
    def _create_devices(self):
        """Create virtual devices from config"""
        for device_config in self.config.get("devices", []):
            device_type = device_config["type"]
            device_name = device_config["name"]
            connection = device_config["connection"]
            
            if device_type == "led":
                from devices.actuators import LED
                pin = connection.get("pin", 18)
                device = LED(device_name, pin)
                
            elif device_type == "dht22":
                pin = connection.get("pin", 4)
                device = DHT22(device_name, pin)
                
            elif device_type == "bme280":
                address = connection.get("i2c", 0x76)
                device = BME280(address, device_name)
                self.i2c.add_device(device)
                
            elif device_type == "hcsr04":
                trigger_pin = connection.get("trigger_pin", 23)
                echo_pin = connection.get("echo_pin", 24)
                device = HCSR04(device_name, trigger_pin, echo_pin)
                
            else:
                print(f"Unknown device type: {device_type}")
                continue
                
            self.devices[device_name] = device
            
    def start(self) -> None:
        """Start simulation"""
        if self.running:
            return
            
        self.running = True
        self.stop_event.clear()
        self.clock.start()
        self.event_bus.start_recording()
        
        # Start simulation thread
        self.sim_thread = threading.Thread(target=self._simulation_loop)
        self.sim_thread.start()
        
        print("Simulation started")
        
    def stop(self) -> None:
        """Stop simulation"""
        if not self.running:
            return
            
        self.running = False
        self.stop_event.set()
        self.clock.stop()
        
        # Wait for simulation thread to finish
        if self.sim_thread:
            self.sim_thread.join(timeout=1.0)
            
        print("Simulation stopped")
        
    def pause(self) -> None:
        """Pause simulation"""
        self.clock.pause()
        
    def resume(self) -> None:
        """Resume simulation"""
        self.clock.resume()
        
    def reset(self) -> None:
        """Reset simulation state"""
        self.clock.reset()
        self.event_bus.clear_history()
        
        # Reset all devices
        for device in self.devices.values():
            device.reset()
            
    def _simulation_loop(self) -> None:
        """Main simulation loop"""
        while self.running and not self.stop_event.is_set():
            # Advance simulation clock
            if self.clock.tick():
                current_time = self.clock.sim_time
                dt = self.clock.timestep_s
                
                # Process scheduled events
                self.scheduler.process_events(current_time)
                
                # Update devices
                for device in self.devices.values():
                    if device.enabled:
                        device.update(current_time, dt)
                        
            else:
                # Clock is paused or stopped
                time.sleep(0.01)
                
    def execute_code(self, code: str, language: str = "python") -> bool:
        """
        Execute user code in simulation environment
        
        Args:
            code: Source code to execute
            language: Programming language (python, c, node)
            
        Returns:
            True if execution successful
        """
        return self.code_runner.execute(code, language)
        
    def run_headless(self, script_path: Optional[str] = None) -> None:
        """Run simulation in headless mode"""
        self.start()
        
        try:
            if script_path:
                # Run specific script
                with open(script_path) as f:
                    code = f.read()
                success = self.execute_code(code)
            else:
                # Run main project script
                main_script = Path(self.config.get("main_script", "src/main.py"))
                if main_script.exists():
                    with open(main_script) as f:
                        code = f.read()
                    success = self.execute_code(code)
                else:
                    print("No main script found")
                    success = False
                    
            if success:
                print("Code execution completed successfully")
            else:
                print("Code execution failed")
                
        except KeyboardInterrupt:
            print("\nSimulation interrupted")
        finally:
            self.stop()
            
    def run_gui(self) -> None:
        """Run simulation with GUI"""
        # This would launch the PyQt6 GUI
        try:
            import sys
            import os
            # Add the project root to Python path
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            from apps.desktop.__main__ import main
            main()
        except ImportError as e:
            print(f"GUI not available: {e}")
            print("Running in headless mode instead...")
            self.run_headless()
        
    def record_trace(self, output_file: str, duration: Optional[float] = None) -> None:
        """Record simulation trace to file"""
        self.start()
        
        try:
            if duration:
                time.sleep(duration)
            else:
                # Record until interrupted
                while self.running:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            pass
        finally:
            events = self.event_bus.stop_recording()
            
            # Save trace to file
            import json
            trace_data = {
                "version": "1.0",
                "config": self.config,
                "events": [
                    {
                        "type": event.type.value,
                        "timestamp": event.timestamp,
                        "source": event.source,
                        "data": event.data
                    }
                    for event in events
                ]
            }
            
            with open(output_file, "w") as f:
                json.dump(trace_data, f, indent=2)
                
            print(f"Trace saved to {output_file}")
            self.stop()
            
    def replay_trace(self, trace_file: str, assert_script: Optional[str] = None) -> bool:
        """Replay simulation from trace file"""
        # Load trace
        import json
        with open(trace_file) as f:
            trace_data = json.load(f)
            
        # TODO: Implement trace replay
        print(f"Replaying trace from {trace_file}")
        
        if assert_script:
            # Run assertion script
            with open(assert_script) as f:
                code = f.read()
            # Execute assertions
            
        return True
        
    def get_pin_state(self, pin: int) -> Dict[str, Any]:
        """Get current state of GPIO pin"""
        gpio_pin = self.board.get_pin_by_bcm(pin)
        if gpio_pin:
            return {
                "pin": pin,
                "mode": gpio_pin.mode.value,
                "value": gpio_pin.value,
                "pull_up": gpio_pin.pull_up,
                "pull_down": gpio_pin.pull_down
            }
        return {}
        
    def set_environment(self, **kwargs) -> None:
        """Set environment parameters"""
        env = self.config.setdefault("environment", {})
        env.update(kwargs)
        
        # Update device parameters
        for device in self.devices.values():
            if hasattr(device, "set_parameter"):
                if "temperature" in kwargs:
                    device.set_parameter("temperature", kwargs["temperature"])
                if "humidity" in kwargs:
                    device.set_parameter("humidity", kwargs["humidity"])