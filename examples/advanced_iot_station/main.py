#!/usr/bin/env python3
"""
Advanced IoT Weather Station

Demonstrates advanced PiStudio features:
- Multiple sensors (BME280, MPU6050, GPS)
- LCD display with real-time data
- NeoPixel status indicators
- Servo-controlled weather vane
- Data logging and analysis
- Environmental response system
"""

import RPiSim.GPIO as GPIO
from sim_i2c import I2C
import time
import json
import math
from datetime import datetime

# Configuration
BME280_ADDR = 0x76
MPU6050_ADDR = 0x68
LCD_ADDR = 0x27

# Pin assignments
NEOPIXEL_PIN = 18
SERVO_PIN = 19
BUZZER_PIN = 20
STATUS_LED_PIN = 21

# Thresholds
TEMP_HIGH_THRESHOLD = 30.0
TEMP_LOW_THRESHOLD = 5.0
HUMIDITY_HIGH_THRESHOLD = 80.0
WIND_SPEED_THRESHOLD = 20.0  # km/h

class WeatherStation:
    """Advanced IoT Weather Station"""
    
    def __init__(self):
        self.setup_gpio()
        self.setup_i2c()
        self.setup_sensors()
        
        # Data storage
        self.sensor_data = []
        self.alerts_active = []
        
        # Display state
        self.display_mode = 0
        self.last_display_update = 0
        
        print("🌤️  Advanced IoT Weather Station Initialized")
        
    def setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        
        # Output pins
        GPIO.setup(NEOPIXEL_PIN, GPIO.OUT)
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)
        GPIO.setup(STATUS_LED_PIN, GPIO.OUT)
        
        # PWM for servo
        self.servo_pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz
        self.servo_pwm.start(0)
        
        print("✅ GPIO initialized")
        
    def setup_i2c(self):
        """Initialize I2C bus"""
        self.i2c = I2C(1)
        
        # Scan for devices
        devices = self.i2c.scan()
        print(f"🔍 I2C devices found: {[hex(addr) for addr in devices]}")
        
    def setup_sensors(self):
        """Initialize sensors"""
        try:
            # BME280 Environmental Sensor
            self.i2c.write_byte_data(BME280_ADDR, 0xF2, 0x01)  # Humidity oversampling
            self.i2c.write_byte_data(BME280_ADDR, 0xF4, 0x27)  # Temp/Press oversampling
            self.i2c.write_byte_data(BME280_ADDR, 0xF5, 0x00)  # Config
            print("✅ BME280 initialized")
            
            # MPU6050 IMU
            self.i2c.write_byte_data(MPU6050_ADDR, 0x6B, 0x00)  # Wake up
            self.i2c.write_byte_data(MPU6050_ADDR, 0x1C, 0x00)  # Accel config
            self.i2c.write_byte_data(MPU6050_ADDR, 0x1B, 0x00)  # Gyro config
            print("✅ MPU6050 initialized")
            
            # LCD Display
            self.lcd_init()
            print("✅ LCD initialized")
            
        except Exception as e:
            print(f"❌ Sensor initialization error: {e}")
            
    def lcd_init(self):
        """Initialize LCD display"""
        try:
            # Clear display
            self.i2c.write_byte_data(LCD_ADDR, 0x00, 0x01)
            time.sleep(0.01)
            
            # Display on, cursor off
            self.i2c.write_byte_data(LCD_ADDR, 0x00, 0x0C)
            time.sleep(0.01)
            
            # Entry mode
            self.i2c.write_byte_data(LCD_ADDR, 0x00, 0x06)
            time.sleep(0.01)
            
        except Exception as e:
            print(f"LCD init error: {e}")
            
    def read_bme280(self):
        """Read BME280 environmental data"""
        try:
            # Read raw data
            data = self.i2c.read_i2c_block_data(BME280_ADDR, 0xF7, 8)
            
            # Parse data (simplified conversion)
            pressure_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
            temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
            humidity_raw = (data[6] << 8) | data[7]
            
            # Convert to physical values (simplified)
            temperature = (temp_raw / 5120.0) - 40.0
            pressure = pressure_raw / 256.0
            humidity = humidity_raw / 512.0
            
            return {
                "temperature": round(temperature, 1),
                "pressure": round(pressure, 1),
                "humidity": round(humidity, 1)
            }
            
        except Exception as e:
            print(f"BME280 read error: {e}")
            return None
            
    def read_mpu6050(self):
        """Read MPU6050 motion data"""
        try:
            # Read accelerometer data
            accel_data = self.i2c.read_i2c_block_data(MPU6050_ADDR, 0x3B, 6)
            
            # Convert to signed 16-bit values
            accel_x = self.bytes_to_int16(accel_data[0], accel_data[1]) / 16384.0
            accel_y = self.bytes_to_int16(accel_data[2], accel_data[3]) / 16384.0
            accel_z = self.bytes_to_int16(accel_data[4], accel_data[5]) / 16384.0
            
            # Calculate tilt angles
            roll = math.atan2(accel_y, accel_z) * 180 / math.pi
            pitch = math.atan2(-accel_x, math.sqrt(accel_y**2 + accel_z**2)) * 180 / math.pi
            
            # Estimate wind speed from vibration (simplified)
            vibration = math.sqrt(accel_x**2 + accel_y**2 + accel_z**2) - 1.0
            wind_speed = max(0, vibration * 50)  # Rough conversion
            
            return {
                "roll": round(roll, 1),
                "pitch": round(pitch, 1),
                "wind_speed": round(wind_speed, 1),
                "vibration": round(vibration, 3)
            }
            
        except Exception as e:
            print(f"MPU6050 read error: {e}")
            return None
            
    def bytes_to_int16(self, high_byte, low_byte):
        """Convert two bytes to signed 16-bit integer"""
        value = (high_byte << 8) | low_byte
        if value >= 32768:
            value -= 65536
        return value
        
    def update_neopixel(self, color_mode):
        """Update NeoPixel status indicator"""
        # Simplified NeoPixel control
        # In real implementation, this would send WS2812 protocol
        
        colors = {
            "green": "Normal conditions",
            "yellow": "Caution - monitoring",
            "red": "Alert conditions",
            "blue": "System status",
            "purple": "Data logging"
        }
        
        if color_mode in colors:
            # Simulate NeoPixel update
            GPIO.output(NEOPIXEL_PIN, GPIO.HIGH)
            time.sleep(0.001)  # Brief pulse
            GPIO.output(NEOPIXEL_PIN, GPIO.LOW)
            
    def set_servo_angle(self, angle):
        """Set servo angle for weather vane"""
        # Convert angle to duty cycle (0-180° -> 2.5-12.5%)
        duty_cycle = 2.5 + (angle / 180.0) * 10.0
        self.servo_pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.1)
        self.servo_pwm.ChangeDutyCycle(0)  # Stop PWM signal
        
    def update_lcd(self, line1, line2):
        """Update LCD display"""
        try:
            # Clear display
            self.i2c.write_byte_data(LCD_ADDR, 0x00, 0x01)
            time.sleep(0.01)
            
            # Write line 1
            for char in line1[:16]:  # Limit to 16 characters
                self.i2c.write_byte_data(LCD_ADDR, 0x40, ord(char))
                
            # Move to line 2
            self.i2c.write_byte_data(LCD_ADDR, 0x00, 0xC0)
            
            # Write line 2
            for char in line2[:16]:
                self.i2c.write_byte_data(LCD_ADDR, 0x40, ord(char))
                
        except Exception as e:
            print(f"LCD update error: {e}")
            
    def check_alerts(self, env_data, motion_data):
        """Check for alert conditions"""
        alerts = []
        
        if env_data:
            temp = env_data["temperature"]
            humidity = env_data["humidity"]
            
            if temp > TEMP_HIGH_THRESHOLD:
                alerts.append(f"High temp: {temp}°C")
            elif temp < TEMP_LOW_THRESHOLD:
                alerts.append(f"Low temp: {temp}°C")
                
            if humidity > HUMIDITY_HIGH_THRESHOLD:
                alerts.append(f"High humidity: {humidity}%")
                
        if motion_data:
            wind_speed = motion_data["wind_speed"]
            
            if wind_speed > WIND_SPEED_THRESHOLD:
                alerts.append(f"High wind: {wind_speed} km/h")
                
        return alerts
        
    def sound_alert(self, duration=0.5):
        """Sound buzzer alert"""
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        
    def log_data(self, timestamp, env_data, motion_data):
        """Log sensor data"""
        log_entry = {
            "timestamp": timestamp,
            "environmental": env_data,
            "motion": motion_data
        }
        
        self.sensor_data.append(log_entry)
        
        # Keep only last 100 entries
        if len(self.sensor_data) > 100:
            self.sensor_data.pop(0)
            
    def get_display_text(self, env_data, motion_data):
        """Get text for LCD display based on mode"""
        if self.display_mode == 0:  # Temperature & Humidity
            if env_data:
                line1 = f"Temp: {env_data['temperature']}C"
                line2 = f"Hum:  {env_data['humidity']}%"
            else:
                line1 = "Temp: --.-C"
                line2 = "Hum:  --%"
                
        elif self.display_mode == 1:  # Pressure & Wind
            if env_data and motion_data:
                line1 = f"Press:{env_data['pressure']:.0f}hPa"
                line2 = f"Wind: {motion_data['wind_speed']:.1f}km/h"
            else:
                line1 = "Press: ----hPa"
                line2 = "Wind: --.-km/h"
                
        elif self.display_mode == 2:  # Tilt & Status
            if motion_data:
                line1 = f"Roll: {motion_data['roll']:.1f}°"
                line2 = f"Pitch:{motion_data['pitch']:.1f}°"
            else:
                line1 = "Roll: --.-°"
                line2 = "Pitch:--.-°"
                
        else:  # System info
            line1 = "Weather Station"
            line2 = f"Logs: {len(self.sensor_data)}"
            
        return line1, line2
        
    def run(self):
        """Main execution loop"""
        print("🚀 Starting weather station monitoring...")
        
        try:
            cycle_count = 0
            
            while True:
                start_time = time.time()
                timestamp = datetime.now().isoformat()
                
                # Read sensors
                env_data = self.read_bme280()
                motion_data = self.read_mpu6050()
                
                # Check for alerts
                alerts = self.check_alerts(env_data, motion_data)
                
                # Update status LED
                GPIO.output(STATUS_LED_PIN, GPIO.HIGH if cycle_count % 2 == 0 else GPIO.LOW)
                
                # Update NeoPixel based on conditions
                if alerts:
                    self.update_neopixel("red")
                    if "High wind" in str(alerts):
                        self.sound_alert(0.2)
                elif env_data and env_data["temperature"] > 25:
                    self.update_neopixel("yellow")
                else:
                    self.update_neopixel("green")
                    
                # Update servo based on wind direction (simulated)
                if motion_data:
                    wind_direction = (cycle_count * 10) % 360  # Simulate changing wind
                    servo_angle = (wind_direction / 360.0) * 180
                    self.set_servo_angle(servo_angle)
                    
                # Update display (cycle through modes every 10 seconds)
                if time.time() - self.last_display_update > 5:
                    self.display_mode = (self.display_mode + 1) % 4
                    self.last_display_update = time.time()
                    
                line1, line2 = self.get_display_text(env_data, motion_data)
                self.update_lcd(line1, line2)
                
                # Log data
                self.log_data(timestamp, env_data, motion_data)
                
                # Print status
                if env_data and motion_data:
                    print(f"📊 {timestamp[:19]} | "
                          f"T:{env_data['temperature']:5.1f}°C | "
                          f"H:{env_data['humidity']:5.1f}% | "
                          f"P:{env_data['pressure']:7.1f}hPa | "
                          f"W:{motion_data['wind_speed']:5.1f}km/h | "
                          f"Alerts:{len(alerts)}")
                          
                    if alerts:
                        for alert in alerts:
                            print(f"⚠️  {alert}")
                            
                # Data analysis every 30 cycles
                if cycle_count % 30 == 0 and len(self.sensor_data) > 10:
                    self.analyze_trends()
                    
                cycle_count += 1
                
                # Maintain 2-second cycle time
                elapsed = time.time() - start_time
                if elapsed < 2.0:
                    time.sleep(2.0 - elapsed)
                    
        except KeyboardInterrupt:
            print("\\n🛑 Stopping weather station...")
            
        finally:
            self.cleanup()
            
    def analyze_trends(self):
        """Analyze sensor data trends"""
        if len(self.sensor_data) < 10:
            return
            
        # Get recent temperature data
        recent_temps = []
        for entry in self.sensor_data[-10:]:
            if entry["environmental"]:
                recent_temps.append(entry["environmental"]["temperature"])
                
        if len(recent_temps) >= 5:
            # Calculate trend
            avg_early = sum(recent_temps[:len(recent_temps)//2]) / (len(recent_temps)//2)
            avg_late = sum(recent_temps[len(recent_temps)//2:]) / (len(recent_temps) - len(recent_temps)//2)
            
            trend = avg_late - avg_early
            
            if abs(trend) > 1.0:  # Significant change
                direction = "rising" if trend > 0 else "falling"
                print(f"📈 Temperature trend: {direction} ({trend:+.1f}°C)")
                
                # Update NeoPixel to indicate trend
                self.update_neopixel("blue")
                
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Stop PWM
            self.servo_pwm.stop()
            
            # Turn off all outputs
            GPIO.output(STATUS_LED_PIN, GPIO.LOW)
            GPIO.output(BUZZER_PIN, GPIO.LOW)
            GPIO.output(NEOPIXEL_PIN, GPIO.LOW)
            
            # Clear LCD
            self.update_lcd("System", "Shutdown")
            time.sleep(1)
            
            # Cleanup GPIO
            GPIO.cleanup()
            
            # Save final data log
            if self.sensor_data:
                with open("weather_log.json", "w") as f:
                    json.dump(self.sensor_data, f, indent=2)
                print(f"💾 Saved {len(self.sensor_data)} data points to weather_log.json")
                
            print("✅ Cleanup complete")
            
        except Exception as e:
            print(f"❌ Cleanup error: {e}")


def main():
    """Main function"""
    print("🌤️  Advanced IoT Weather Station")
    print("=" * 50)
    print("Features:")
    print("• BME280 environmental sensor (I2C)")
    print("• MPU6050 motion sensor for wind detection")
    print("• LCD display with rotating information")
    print("• NeoPixel status indicators")
    print("• Servo-controlled weather vane")
    print("• Alert system with buzzer")
    print("• Data logging and trend analysis")
    print("• Real-time environmental monitoring")
    print()
    
    station = WeatherStation()
    station.run()


if __name__ == "__main__":
    main()