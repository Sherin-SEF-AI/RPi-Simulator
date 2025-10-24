#!/usr/bin/env python3
"""
PiStudio Example: BME280 Environmental Logger

Demonstrates I2C communication with BME280 sensor for reading
temperature, pressure, and humidity data.
"""

import time
import sys
from sim_i2c import I2C

# BME280 I2C address
BME280_ADDR = 0x76

# BME280 registers
BME280_CHIP_ID = 0xD0
BME280_RESET = 0xE0
BME280_CTRL_HUM = 0xF2
BME280_CTRL_MEAS = 0xF4
BME280_CONFIG = 0xF5
BME280_PRESS_MSB = 0xF7

def read_bme280_data(i2c, address):
    """Read temperature, pressure, and humidity from BME280"""
    try:
        # Read chip ID to verify sensor
        chip_id = i2c.read_byte_data(address, BME280_CHIP_ID)
        if chip_id != 0x60:
            print(f"Warning: Unexpected chip ID: 0x{chip_id:02X}")
            
        # Configure sensor
        i2c.write_byte_data(address, BME280_CTRL_HUM, 0x01)   # Humidity oversampling x1
        i2c.write_byte_data(address, BME280_CTRL_MEAS, 0x27)  # Temp/Press oversampling x1, normal mode
        i2c.write_byte_data(address, BME280_CONFIG, 0x00)     # No filter, no SPI
        
        # Wait for measurement
        time.sleep(0.1)
        
        # Read raw data (simplified - real BME280 needs calibration)
        data = i2c.read_i2c_block_data(address, BME280_PRESS_MSB, 8)
        
        # Parse data (simplified conversion)
        pressure_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        humidity_raw = (data[6] << 8) | data[7]
        
        # Convert to human-readable values (simplified)
        temperature = (temp_raw / 5120.0) - 40.0  # Approximate conversion
        pressure = pressure_raw / 256.0           # Approximate conversion
        humidity = humidity_raw / 512.0           # Approximate conversion
        
        return temperature, pressure, humidity
        
    except Exception as e:
        print(f"Error reading BME280: {e}")
        return None, None, None

def main():
    """Main function"""
    print("PiStudio BME280 Environmental Logger")
    print(f"I2C Address: 0x{BME280_ADDR:02X}")
    print("-" * 40)
    
    try:
        # Initialize I2C
        i2c = I2C(1)  # I2C bus 1
        
        # Check if sensor is present
        devices = i2c.scan()
        if BME280_ADDR not in devices:
            print(f"BME280 not found at address 0x{BME280_ADDR:02X}")
            print(f"Available devices: {[hex(addr) for addr in devices]}")
            return
            
        print(f"BME280 found at address 0x{BME280_ADDR:02X}")
        print()
        
        # Log data for 30 seconds
        start_time = time.time()
        sample_count = 0
        
        print("Time\t\tTemp(°C)\tPress(hPa)\tHumid(%)")
        print("-" * 50)
        
        while time.time() - start_time < 30:
            temp, pressure, humidity = read_bme280_data(i2c, BME280_ADDR)
            
            if temp is not None:
                timestamp = time.strftime("%H:%M:%S")
                print(f"{timestamp}\t{temp:.1f}\t\t{pressure:.1f}\t\t{humidity:.1f}")
                sample_count += 1
            else:
                print("Failed to read sensor data")
                
            time.sleep(2)  # Sample every 2 seconds
            
        print(f"\nLogging complete. Collected {sample_count} samples.")
        
    except KeyboardInterrupt:
        print("\nLogging interrupted by user")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()