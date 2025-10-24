"""
Python Code Runner with RPi.GPIO shim
"""

import sys
import io
import contextlib
import threading
import time
from typing import Dict, Any, Optional


class RPiGPIOShim:
    """
    RPi.GPIO compatibility shim that redirects to simulator
    """
    
    # Constants
    BCM = "BCM"
    BOARD = "BOARD"
    IN = "IN"
    OUT = "OUT"
    HIGH = 1
    LOW = 0
    PUD_OFF = "PUD_OFF"
    PUD_UP = "PUD_UP"
    PUD_DOWN = "PUD_DOWN"
    RISING = "RISING"
    FALLING = "FALLING"
    BOTH = "BOTH"
    
    def __init__(self, simulator):
        self.simulator = simulator
        self.mode = None
        
    def setmode(self, mode):
        """Set pin numbering mode"""
        self.mode = mode
        
    def setup(self, pin, direction, pull_up_down=PUD_OFF):
        """Setup GPIO pin"""
        self.simulator.gpio.setup(pin, direction, pull_up_down)
        
    def output(self, pin, value):
        """Set GPIO output"""
        timestamp = self.simulator.clock.sim_time
        self.simulator.gpio.output(pin, value, timestamp)
        
    def input(self, pin):
        """Read GPIO input"""
        return self.simulator.gpio.input(pin)
        
    def cleanup(self):
        """Cleanup GPIO (no-op in simulation)"""
        pass
        
    def add_event_detect(self, pin, edge, callback=None):
        """Add edge detection"""
        self.simulator.gpio.add_event_detect(pin, edge, callback)
        
    def remove_event_detect(self, pin):
        """Remove edge detection"""
        self.simulator.gpio.remove_event_detect(pin)


class SimI2C:
    """
    I2C interface shim for simulation
    """
    
    def __init__(self, bus_id, simulator):
        self.bus_id = bus_id
        self.simulator = simulator
        self.i2c_controller = simulator.i2c
        
    def write_byte_data(self, address, register, value):
        """Write byte to I2C device register"""
        timestamp = self.simulator.clock.sim_time
        return self.i2c_controller.write_transaction(address, [register, value], timestamp)
        
    def read_byte_data(self, address, register):
        """Read byte from I2C device register"""
        timestamp = self.simulator.clock.sim_time
        # Write register address first
        self.i2c_controller.write_transaction(address, [register], timestamp)
        # Read data
        data = self.i2c_controller.read_transaction(address, 1, timestamp)
        return data[0] if data else 0
        
    def read_i2c_block_data(self, address, register, length):
        """Read block of data from I2C device"""
        timestamp = self.simulator.clock.sim_time
        # Write register address first
        self.i2c_controller.write_transaction(address, [register], timestamp)
        # Read data block
        return self.i2c_controller.read_transaction(address, length, timestamp) or []
        
    def scan(self):
        """Scan I2C bus for devices"""
        timestamp = self.simulator.clock.sim_time
        return self.i2c_controller.scan_bus(timestamp)


class PythonRunner:
    """
    Python code runner with simulation integration
    """
    
    def __init__(self, simulator):
        self.simulator = simulator
        self.execution_thread = None
        self.stop_execution = False
        
    def execute(self, code: str) -> bool:
        """
        Execute Python code with simulation shims
        
        Args:
            code: Python source code
            
        Returns:
            True if execution successful
        """
        # Create execution environment
        rpi_sim_module = self._create_rpi_shim_module()
        exec_globals = {
            '__name__': '__main__',
            '__builtins__': __builtins__,
            'time': self._create_time_shim(),
            'RPiSim': rpi_sim_module,
        }
        
        # Add I2C simulation
        exec_globals['sim_i2c'] = type('sim_i2c', (), {
            'I2C': lambda bus_id: SimI2C(bus_id, self.simulator)
        })()
        
        # Capture output
        output_buffer = io.StringIO()
        
        try:
            # Install custom import hook for RPiSim modules
            import sys
            original_modules = sys.modules.copy()
            
            # Add RPiSim modules to sys.modules
            sys.modules['RPiSim'] = rpi_sim_module
            sys.modules['RPiSim.GPIO'] = rpi_sim_module.GPIO
            
            with contextlib.redirect_stdout(output_buffer):
                with contextlib.redirect_stderr(output_buffer):
                    # Execute code in separate thread for timeout control
                    self.stop_execution = False
                    self.execution_thread = threading.Thread(
                        target=self._execute_code_thread,
                        args=(code, exec_globals)
                    )
                    self.execution_thread.start()
                    self.execution_thread.join(timeout=30)  # 30 second timeout
                    
                    if self.execution_thread.is_alive():
                        self.stop_execution = True
                        print("Code execution timed out")
                        return False
                        
            # Print captured output
            output = output_buffer.getvalue()
            if output:
                print(output)
                
            # Restore original modules
            sys.modules.clear()
            sys.modules.update(original_modules)
            
            return True
            
        except Exception as e:
            print(f"Code execution error: {e}")
            # Restore original modules on error too
            import sys
            sys.modules.clear()
            sys.modules.update(original_modules)
            return False
            
    def _execute_code_thread(self, code: str, exec_globals: Dict[str, Any]) -> None:
        """Execute code in thread with stop check"""
        try:
            exec(code, exec_globals)
        except Exception as e:
            if not self.stop_execution:
                print(f"Runtime error: {e}")
                
    def _create_time_shim(self):
        """Create time module shim that uses simulation time"""
        simulator = self.simulator
        stop_execution = self.stop_execution
        
        class TimeShim:
            def sleep(self, seconds):
                """Sleep using simulation time"""
                if stop_execution:
                    return
                    
                # For now, just use real time sleep for simplicity
                import time as real_time
                real_time.sleep(seconds)
                    
            def time(self):
                """Get current simulation time"""
                return simulator.clock.sim_time
                
            def strftime(self, fmt, t=None):
                """Format time string"""
                import time as real_time
                return real_time.strftime(fmt, t)
                
        return TimeShim()
        
    def _create_rpi_shim_module(self):
        """Create RPiSim module with GPIO shim"""
        class RPiSimModule:
            def __init__(self, simulator):
                self.GPIO = RPiGPIOShim(simulator)
                
        return RPiSimModule(self.simulator)