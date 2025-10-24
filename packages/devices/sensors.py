"""
Sensor Device Implementations
"""

import math
import random
from typing import Optional, Tuple, List
from peripherals import I2cDevice
from .base import VirtualDevice, DeviceParameter


class DHT22(VirtualDevice):
    """DHT22 Temperature and Humidity Sensor"""
    
    def __init__(self, name: str = "DHT22", data_pin: int = 4):
        super().__init__(name, "sensor")
        self.data_pin = data_pin
        
        # Sensor parameters
        self.parameters = {
            "temperature": DeviceParameter("Temperature", 25.0, -40, 80, "°C"),
            "humidity": DeviceParameter("Humidity", 50.0, 0, 100, "%RH"),
            "noise_level": DeviceParameter("Noise Level", 0.1, 0, 5.0, ""),
            "response_time": DeviceParameter("Response Time", 2.0, 0.5, 10.0, "s")
        }
        
        # Internal state
        self.last_reading_time = 0.0
        self.reading_valid = True
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update sensor readings with noise and response time"""
        self.last_update = sim_time
        
        # Add noise to readings
        noise = self.get_parameter("noise_level")
        if noise > 0:
            temp_noise = random.gauss(0, noise)
            humid_noise = random.gauss(0, noise)
            
            current_temp = self.get_parameter("temperature") + temp_noise
            current_humid = self.get_parameter("humidity") + humid_noise
            
            # Clamp to valid ranges
            current_temp = max(-40, min(80, current_temp))
            current_humid = max(0, min(100, current_humid))
            
            self.set_parameter("temperature", current_temp)
            self.set_parameter("humidity", current_humid)
            
    def read_data(self, sim_time: float) -> Optional[Tuple[float, float]]:
        """
        Read temperature and humidity
        
        Returns:
            (temperature, humidity) or None if reading failed
        """
        # Check minimum time between readings (2 seconds for DHT22)
        if sim_time - self.last_reading_time < 2.0:
            return None
            
        self.last_reading_time = sim_time
        
        # Inject faults
        if self._should_inject_fault():
            if self.fault_type == "timeout":
                return None
            elif self.fault_type == "bad_checksum":
                return None
                
        return (self.get_parameter("temperature"), self.get_parameter("humidity"))
        
    def reset(self) -> None:
        """Reset sensor state"""
        self.last_reading_time = 0.0
        self.reading_valid = True


class BME280(I2cDevice, VirtualDevice):
    """BME280 Environmental Sensor (I2C)"""
    
    def __init__(self, address: int = 0x76, name: str = "BME280"):
        I2cDevice.__init__(self, address, name)
        VirtualDevice.__init__(self, name, "sensor")
        
        # Sensor parameters
        self.parameters = {
            "temperature": DeviceParameter("Temperature", 25.0, -40, 85, "°C"),
            "pressure": DeviceParameter("Pressure", 1013.25, 300, 1100, "hPa"),
            "humidity": DeviceParameter("Humidity", 50.0, 0, 100, "%RH"),
            "altitude": DeviceParameter("Altitude", 0.0, -500, 9000, "m")
        }
        
        # BME280 registers
        self.registers = {
            0xD0: 0x60,  # Chip ID
            0xE0: 0x00,  # Reset register
            0xF2: 0x01,  # ctrl_hum
            0xF4: 0x27,  # ctrl_meas
            0xF5: 0x00,  # config
        }
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update environmental readings"""
        self.last_update = sim_time
        
        # Calculate pressure from altitude
        altitude = self.get_parameter("altitude")
        sea_level_pressure = 1013.25
        pressure = sea_level_pressure * math.pow(1 - (0.0065 * altitude) / 288.15, 5.255)
        self.set_parameter("pressure", pressure)        

    def write(self, data: List[int]) -> bool:
        """Handle I2C write (register access)"""
        if len(data) >= 2:
            reg_addr = data[0]
            reg_value = data[1]
            self.registers[reg_addr] = reg_value
        return True
        
    def read(self, length: int) -> List[int]:
        """Handle I2C read (sensor data)"""
        # Return temperature, pressure, humidity data
        temp = int((self.get_parameter("temperature") + 40) * 100)  # Scaled
        pressure = int(self.get_parameter("pressure") * 100)
        humidity = int(self.get_parameter("humidity") * 100)
        
        # Pack into bytes (simplified)
        data = []
        data.extend([(pressure >> 8) & 0xFF, pressure & 0xFF])
        data.extend([(temp >> 8) & 0xFF, temp & 0xFF])
        data.extend([(humidity >> 8) & 0xFF, humidity & 0xFF])
        
        return data[:length]
        
    def reset(self) -> None:
        """Reset sensor"""
        self.registers[0xE0] = 0xB6  # Reset command


class HCSR04(VirtualDevice):
    """HC-SR04 Ultrasonic Distance Sensor"""
    
    def __init__(self, name: str = "HC-SR04", trigger_pin: int = 23, echo_pin: int = 24):
        super().__init__(name, "sensor")
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        
        # Sensor parameters
        self.parameters = {
            "distance": DeviceParameter("Distance", 10.0, 2, 400, "cm"),
            "noise_level": DeviceParameter("Noise", 0.5, 0, 5.0, "cm"),
            "temperature": DeviceParameter("Temperature", 20.0, -10, 50, "°C")
        }
        
        # Measurement state
        self.measuring = False
        self.trigger_time = 0.0
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update distance measurement"""
        self.last_update = sim_time
        
        # Add noise to distance reading
        noise = self.get_parameter("noise_level")
        if noise > 0:
            distance_noise = random.gauss(0, noise)
            current_distance = self.get_parameter("distance") + distance_noise
            current_distance = max(2, min(400, current_distance))  # Clamp to sensor range
            self.set_parameter("distance", current_distance)
            
    def trigger_measurement(self, sim_time: float) -> float:
        """
        Trigger distance measurement
        
        Returns:
            Echo pulse duration in seconds
        """
        distance_cm = self.get_parameter("distance")
        temperature = self.get_parameter("temperature")
        
        # Calculate speed of sound based on temperature
        sound_speed = 331.3 + (0.606 * temperature)  # m/s
        
        # Calculate round-trip time
        distance_m = distance_cm / 100.0
        echo_duration = (2 * distance_m) / sound_speed
        
        # Inject faults
        if self._should_inject_fault():
            if self.fault_type == "no_echo":
                return 0.0  # No echo received
            elif self.fault_type == "false_echo":
                return random.uniform(0.001, 0.02)  # Random false reading
                
        return echo_duration
        
    def reset(self) -> None:
        """Reset sensor state"""
        self.measuring = False
        self.trigger_time = 0.0


class MPU6050(I2cDevice, VirtualDevice):
    """MPU6050 6-axis IMU (Accelerometer + Gyroscope)"""
    
    def __init__(self, address: int = 0x68, name: str = "MPU6050"):
        I2cDevice.__init__(self, address, name)
        VirtualDevice.__init__(self, name, "sensor")
        
        # Sensor parameters
        self.parameters = {
            "accel_x": DeviceParameter("Accel X", 0.0, -16, 16, "g"),
            "accel_y": DeviceParameter("Accel Y", 0.0, -16, 16, "g"),
            "accel_z": DeviceParameter("Accel Z", 1.0, -16, 16, "g"),  # Gravity
            "gyro_x": DeviceParameter("Gyro X", 0.0, -250, 250, "°/s"),
            "gyro_y": DeviceParameter("Gyro Y", 0.0, -250, 250, "°/s"),
            "gyro_z": DeviceParameter("Gyro Z", 0.0, -250, 250, "°/s"),
            "temperature": DeviceParameter("Temperature", 25.0, -40, 85, "°C")
        }
        
        # MPU6050 registers
        self.registers = {
            0x75: 0x68,  # WHO_AM_I
            0x6B: 0x40,  # PWR_MGMT_1 (sleep mode)
        }
        
    def update(self, sim_time: float, dt: float) -> None:
        """Update IMU readings with realistic motion"""
        self.last_update = sim_time
        
        # Add small random variations to simulate vibration/noise
        for param_name in ["accel_x", "accel_y", "gyro_x", "gyro_y", "gyro_z"]:
            current = self.get_parameter(param_name)
            noise = random.gauss(0, 0.01)  # Small noise
            self.set_parameter(param_name, current + noise)
            
    def write(self, data: List[int]) -> bool:
        """Handle I2C register writes"""
        if len(data) >= 2:
            reg_addr = data[0]
            reg_value = data[1]
            self.registers[reg_addr] = reg_value
        return True
        
    def read(self, length: int) -> List[int]:
        """Handle I2C register reads"""
        # Return accelerometer, temperature, gyroscope data
        accel_x = int(self.get_parameter("accel_x") * 2048)  # Scale for ±16g
        accel_y = int(self.get_parameter("accel_y") * 2048)
        accel_z = int(self.get_parameter("accel_z") * 2048)
        
        temp = int((self.get_parameter("temperature") + 40) * 340)  # MPU6050 scaling
        
        gyro_x = int(self.get_parameter("gyro_x") * 131)  # Scale for ±250°/s
        gyro_y = int(self.get_parameter("gyro_y") * 131)
        gyro_z = int(self.get_parameter("gyro_z") * 131)
        
        # Pack into bytes (big-endian, 16-bit values)
        data = []
        for value in [accel_x, accel_y, accel_z, temp, gyro_x, gyro_y, gyro_z]:
            data.extend([(value >> 8) & 0xFF, value & 0xFF])
            
        return data[:length]
        
    def reset(self) -> None:
        """Reset IMU"""
        self.registers[0x6B] = 0x40  # Sleep mode