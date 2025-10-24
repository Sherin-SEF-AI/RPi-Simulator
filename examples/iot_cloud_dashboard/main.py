#!/usr/bin/env python3
"""
IoT Cloud Dashboard Example

Demonstrates advanced PiStudio capabilities:
- Multiple cloud platform integration (Azure, AWS, Google Cloud)
- Real-time sensor data streaming
- Remote device control via cloud commands
- Data visualization and analytics
- Edge computing with local processing
- Fault tolerance and offline operation
"""

import RPiSim.GPIO as GPIO
from sim_i2c import I2C
import time
import json
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Import cloud connectors (would be available in full implementation)
try:
    from iot_integration.cloud_connectors import (
        AzureIoTConnector, AWSIoTConnector, GoogleCloudIoTConnector, IoTCloudManager
    )
    CLOUD_AVAILABLE = True
except ImportError:
    CLOUD_AVAILABLE = False
    print("⚠️  Cloud integration not available - running in simulation mode")

# Configuration
DEVICE_ID = "pistudio-iot-demo-001"
AZURE_CONNECTION_STRING = "HostName=demo-hub.azure-devices.net;DeviceId=pistudio-demo;SharedAccessKey=demo-key"
AWS_ENDPOINT = "demo-endpoint.iot.us-west-2.amazonaws.com"
GOOGLE_PROJECT_ID = "pistudio-demo-project"

# Sensor addresses
BME280_ADDR = 0x76
MPU6050_ADDR = 0x68
ADS1115_ADDR = 0x48  # ADC for analog sensors

# Pin assignments
STATUS_LED_PIN = 18
ALERT_LED_PIN = 19
BUZZER_PIN = 20
RELAY_PIN = 21

# Data collection settings
TELEMETRY_INTERVAL = 30  # seconds
FAST_TELEMETRY_INTERVAL = 5  # seconds for alerts
MAX_OFFLINE_BUFFER = 1000  # messages


class EdgeDataProcessor:
    """Local edge computing for data processing and analytics"""
    
    def __init__(self):
        self.data_buffer: List[Dict[str, Any]] = []
        self.analytics_results = {}
        self.alert_thresholds = {
            "temperature": {"min": 0, "max": 40},
            "humidity": {"min": 20, "max": 80},
            "pressure": {"min": 950, "max": 1050},
            "vibration": {"max": 2.0}
        }
        
    def process_sensor_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sensor data locally"""
        processed = data.copy()
        
        # Add derived metrics
        if "temperature" in data and "humidity" in data:
            # Calculate heat index
            processed["heat_index"] = self._calculate_heat_index(
                data["temperature"], data["humidity"]
            )
            
            # Calculate dew point
            processed["dew_point"] = self._calculate_dew_point(
                data["temperature"], data["humidity"]
            )
            
        # Detect anomalies
        anomalies = self._detect_anomalies(data)
        if anomalies:
            processed["anomalies"] = anomalies
            
        # Store for trend analysis
        self.data_buffer.append(processed)
        if len(self.data_buffer) > 100:  # Keep last 100 readings
            self.data_buffer.pop(0)
            
        # Update analytics
        self._update_analytics()
        
        return processed
        
    def _calculate_heat_index(self, temp_c: float, humidity: float) -> float:
        """Calculate heat index"""
        temp_f = temp_c * 9/5 + 32
        
        if temp_f < 80:
            return temp_c
            
        # Simplified heat index calculation
        hi = (0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (humidity * 0.094)))
        
        if hi > 79:
            # More complex calculation for higher temperatures
            hi = (-42.379 + 2.04901523 * temp_f + 10.14333127 * humidity
                  - 0.22475541 * temp_f * humidity - 0.00683783 * temp_f**2
                  - 0.05481717 * humidity**2 + 0.00122874 * temp_f**2 * humidity
                  + 0.00085282 * temp_f * humidity**2 - 0.00000199 * temp_f**2 * humidity**2)
                  
        return (hi - 32) * 5/9  # Convert back to Celsius
        
    def _calculate_dew_point(self, temp_c: float, humidity: float) -> float:
        """Calculate dew point"""
        a = 17.27
        b = 237.7
        
        alpha = ((a * temp_c) / (b + temp_c)) + math.log(humidity / 100.0)
        dew_point = (b * alpha) / (a - alpha)
        
        return round(dew_point, 1)
        
    def _detect_anomalies(self, data: Dict[str, Any]) -> List[str]:
        """Detect data anomalies"""
        anomalies = []
        
        for param, thresholds in self.alert_thresholds.items():
            if param in data:
                value = data[param]
                
                if "min" in thresholds and value < thresholds["min"]:
                    anomalies.append(f"{param}_low")
                    
                if "max" in thresholds and value > thresholds["max"]:
                    anomalies.append(f"{param}_high")
                    
        return anomalies
        
    def _update_analytics(self) -> None:
        """Update analytics from recent data"""
        if len(self.data_buffer) < 10:
            return
            
        recent_data = self.data_buffer[-10:]  # Last 10 readings
        
        # Calculate trends
        for param in ["temperature", "humidity", "pressure"]:
            values = [d.get(param, 0) for d in recent_data if param in d]
            if len(values) >= 5:
                # Simple linear trend
                trend = (values[-1] - values[0]) / len(values)
                self.analytics_results[f"{param}_trend"] = trend
                
        # Calculate averages
        for param in ["temperature", "humidity", "pressure"]:
            values = [d.get(param, 0) for d in recent_data if param in d]
            if values:
                self.analytics_results[f"{param}_avg"] = sum(values) / len(values)
                self.analytics_results[f"{param}_min"] = min(values)
                self.analytics_results[f"{param}_max"] = max(values)


class IoTCloudDashboard:
    """Main IoT Cloud Dashboard application"""
    
    def __init__(self):
        self.setup_hardware()
        self.setup_cloud_connections()
        
        # Data processing
        self.edge_processor = EdgeDataProcessor()
        
        # Threading
        self.running = False
        self.telemetry_thread = None
        self.command_thread = None
        
        # Data queues
        self.telemetry_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.offline_buffer = queue.Queue(maxsize=MAX_OFFLINE_BUFFER)
        
        # State
        self.device_state = {
            "online": False,
            "last_telemetry": None,
            "alert_active": False,
            "relay_state": False
        }
        
        print("🌐 IoT Cloud Dashboard initialized")
        
    def setup_hardware(self):
        """Initialize hardware components"""
        GPIO.setmode(GPIO.BCM)
        
        # Output pins
        GPIO.setup(STATUS_LED_PIN, GPIO.OUT)
        GPIO.setup(ALERT_LED_PIN, GPIO.OUT)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)
        GPIO.setup(RELAY_PIN, GPIO.OUT)
        
        # Initialize I2C
        self.i2c = I2C(1)
        
        # Initialize sensors
        try:
            # BME280 Environmental Sensor
            self.i2c.write_byte_data(BME280_ADDR, 0xF2, 0x01)
            self.i2c.write_byte_data(BME280_ADDR, 0xF4, 0x27)
            self.i2c.write_byte_data(BME280_ADDR, 0xF5, 0x00)
            print("✅ BME280 initialized")
            
            # MPU6050 IMU
            self.i2c.write_byte_data(MPU6050_ADDR, 0x6B, 0x00)
            print("✅ MPU6050 initialized")
            
            # ADS1115 ADC (simulated)
            print("✅ ADS1115 ADC initialized")
            
        except Exception as e:
            print(f"⚠️  Sensor initialization warning: {e}")
            
    def setup_cloud_connections(self):
        """Setup cloud platform connections"""
        if not CLOUD_AVAILABLE:
            self.cloud_manager = None
            return
            
        self.cloud_manager = IoTCloudManager()
        
        # Add cloud connectors
        azure_connector = AzureIoTConnector(DEVICE_ID, AZURE_CONNECTION_STRING)
        aws_connector = AWSIoTConnector(DEVICE_ID, AWS_ENDPOINT)
        google_connector = GoogleCloudIoTConnector(
            DEVICE_ID, GOOGLE_PROJECT_ID, "us-central1", "iot-registry"
        )
        
        self.cloud_manager.add_connector("azure", azure_connector)
        self.cloud_manager.add_connector("aws", aws_connector)
        self.cloud_manager.add_connector("google", google_connector)
        
        # Set Azure as primary
        self.cloud_manager.set_active_connector("azure")
        
        # Add callbacks
        azure_connector.add_callback("connected", self._on_cloud_connected)
        azure_connector.add_callback("disconnected", self._on_cloud_disconnected)
        
    def start(self):
        """Start the IoT dashboard"""
        self.running = True
        
        # Connect to cloud platforms
        if self.cloud_manager:
            print("🔗 Connecting to cloud platforms...")
            results = self.cloud_manager.connect_all()
            
            for platform, success in results.items():
                status = "✅" if success else "❌"
                print(f"{status} {platform.title()}: {'Connected' if success else 'Failed'}")
                
        # Start background threads
        self.telemetry_thread = threading.Thread(target=self._telemetry_loop, daemon=True)
        self.command_thread = threading.Thread(target=self._command_loop, daemon=True)
        
        self.telemetry_thread.start()
        self.command_thread.start()
        
        print("🚀 IoT Cloud Dashboard started")
        
        # Main loop
        try:
            self._main_loop()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the IoT dashboard"""
        self.running = False
        
        # Disconnect from cloud
        if self.cloud_manager:
            for connector in self.cloud_manager.connectors.values():
                if connector.connected:
                    connector.disconnect()
                    
        # Cleanup GPIO
        GPIO.cleanup()
        
        print("✅ IoT Cloud Dashboard stopped")
        
    def _main_loop(self):
        """Main application loop"""
        last_status_update = 0
        
        while self.running:
            current_time = time.time()
            
            # Update status LED (heartbeat)
            if current_time - last_status_update > 1.0:
                self._update_status_led()
                last_status_update = current_time
                
            # Process any pending cloud commands
            self._process_cloud_commands()
            
            # Check for alerts
            self._check_alerts()
            
            time.sleep(0.1)
            
    def _telemetry_loop(self):
        """Background telemetry collection and transmission"""
        last_telemetry = 0
        
        while self.running:
            current_time = time.time()
            
            # Determine telemetry interval
            interval = FAST_TELEMETRY_INTERVAL if self.device_state["alert_active"] else TELEMETRY_INTERVAL
            
            if current_time - last_telemetry >= interval:
                try:
                    # Collect sensor data
                    sensor_data = self._collect_sensor_data()
                    
                    if sensor_data:
                        # Process data locally
                        processed_data = self.edge_processor.process_sensor_data(sensor_data)
                        
                        # Add device metadata
                        telemetry = {
                            "deviceId": DEVICE_ID,
                            "timestamp": datetime.utcnow().isoformat(),
                            "sensors": processed_data,
                            "device_state": self.device_state.copy(),
                            "analytics": self.edge_processor.analytics_results.copy()
                        }
                        
                        # Send to cloud
                        self._send_telemetry(telemetry)
                        
                        self.device_state["last_telemetry"] = current_time
                        
                    last_telemetry = current_time
                    
                except Exception as e:
                    print(f"❌ Telemetry error: {e}")
                    
            time.sleep(1)
            
    def _command_loop(self):
        """Background cloud command processing"""
        while self.running:
            try:
                # Check for cloud-to-device messages
                if self.cloud_manager:
                    for name, connector in self.cloud_manager.connectors.items():
                        if connector.connected and hasattr(connector, 'receive_cloud_to_device_message'):
                            message = connector.receive_cloud_to_device_message()
                            if message:
                                self.command_queue.put(message)
                                
            except Exception as e:
                print(f"❌ Command processing error: {e}")
                
            time.sleep(5)  # Check every 5 seconds
            
    def _collect_sensor_data(self) -> Optional[Dict[str, Any]]:
        """Collect data from all sensors"""
        try:
            data = {}
            
            # BME280 Environmental data
            bme_data = self._read_bme280()
            if bme_data:
                data.update(bme_data)
                
            # MPU6050 Motion data
            motion_data = self._read_mpu6050()
            if motion_data:
                data.update(motion_data)
                
            # Analog sensors via ADS1115
            analog_data = self._read_analog_sensors()
            if analog_data:
                data.update(analog_data)
                
            # System metrics
            data["system"] = {
                "uptime": time.time() - self.device_state.get("start_time", time.time()),
                "memory_usage": 45.2,  # Simulated
                "cpu_usage": 12.5,     # Simulated
                "temperature": 42.1    # CPU temperature
            }
            
            return data
            
        except Exception as e:
            print(f"❌ Sensor collection error: {e}")
            return None
            
    def _read_bme280(self) -> Optional[Dict[str, Any]]:
        """Read BME280 environmental sensor"""
        try:
            data = self.i2c.read_i2c_block_data(BME280_ADDR, 0xF7, 8)
            
            # Parse raw data (simplified)
            pressure_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
            temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
            humidity_raw = (data[6] << 8) | data[7]
            
            # Convert to physical values
            temperature = (temp_raw / 5120.0) - 40.0
            pressure = pressure_raw / 256.0
            humidity = humidity_raw / 512.0
            
            return {
                "temperature": round(temperature, 2),
                "pressure": round(pressure, 2),
                "humidity": round(humidity, 2)
            }
            
        except Exception as e:
            print(f"BME280 read error: {e}")
            return None
            
    def _read_mpu6050(self) -> Optional[Dict[str, Any]]:
        """Read MPU6050 motion sensor"""
        try:
            # Read accelerometer
            accel_data = self.i2c.read_i2c_block_data(MPU6050_ADDR, 0x3B, 6)
            
            # Convert to signed values and scale
            accel_x = self._bytes_to_int16(accel_data[0], accel_data[1]) / 16384.0
            accel_y = self._bytes_to_int16(accel_data[2], accel_data[3]) / 16384.0
            accel_z = self._bytes_to_int16(accel_data[4], accel_data[5]) / 16384.0
            
            # Calculate vibration magnitude
            vibration = ((accel_x**2 + accel_y**2 + accel_z**2)**0.5) - 1.0
            
            return {
                "acceleration": {
                    "x": round(accel_x, 3),
                    "y": round(accel_y, 3),
                    "z": round(accel_z, 3)
                },
                "vibration": round(abs(vibration), 3)
            }
            
        except Exception as e:
            print(f"MPU6050 read error: {e}")
            return None
            
    def _read_analog_sensors(self) -> Optional[Dict[str, Any]]:
        """Read analog sensors via ADS1115 ADC"""
        try:
            # Simulate analog sensor readings
            import random
            
            return {
                "light_level": round(random.uniform(0, 100), 1),
                "soil_moisture": round(random.uniform(20, 80), 1),
                "gas_concentration": round(random.uniform(0, 500), 1)
            }
            
        except Exception as e:
            print(f"Analog sensor read error: {e}")
            return None
            
    def _bytes_to_int16(self, high: int, low: int) -> int:
        """Convert two bytes to signed 16-bit integer"""
        value = (high << 8) | low
        return value - 65536 if value >= 32768 else value
        
    def _send_telemetry(self, data: Dict[str, Any]) -> None:
        """Send telemetry to cloud platforms"""
        if not self.cloud_manager:
            print(f"📊 Telemetry (offline): {json.dumps(data, indent=2)}")
            return
            
        # Try to send to all connected platforms
        results = self.cloud_manager.send_to_all(data)
        
        success_count = sum(1 for success in results.values() if success)
        
        if success_count > 0:
            print(f"📊 Telemetry sent to {success_count}/{len(results)} platforms")
            self.device_state["online"] = True
            
            # Send any buffered offline data
            self._send_offline_buffer()
        else:
            print("📊 All cloud platforms offline - buffering data")
            self.device_state["online"] = False
            
            # Buffer for later transmission
            try:
                self.offline_buffer.put_nowait(data)
            except queue.Full:
                print("⚠️  Offline buffer full - dropping oldest data")
                try:
                    self.offline_buffer.get_nowait()
                    self.offline_buffer.put_nowait(data)
                except queue.Empty:
                    pass
                    
    def _send_offline_buffer(self) -> None:
        """Send buffered offline data"""
        sent_count = 0
        
        while not self.offline_buffer.empty() and sent_count < 10:  # Limit burst
            try:
                buffered_data = self.offline_buffer.get_nowait()
                if self.cloud_manager.send_to_active(buffered_data):
                    sent_count += 1
                else:
                    # Put back if send failed
                    self.offline_buffer.put_nowait(buffered_data)
                    break
            except queue.Empty:
                break
                
        if sent_count > 0:
            print(f"📤 Sent {sent_count} buffered messages")
            
    def _process_cloud_commands(self) -> None:
        """Process incoming cloud commands"""
        while not self.command_queue.empty():
            try:
                command = self.command_queue.get_nowait()
                self._execute_command(command)
            except queue.Empty:
                break
                
    def _execute_command(self, command: Dict[str, Any]) -> None:
        """Execute a cloud command"""
        try:
            cmd_type = command.get("command", "unknown")
            data = command.get("data", {})
            
            print(f"📥 Cloud command: {cmd_type}")
            
            if cmd_type == "update_config":
                self._update_configuration(data)
            elif cmd_type == "control_relay":
                self._control_relay(data.get("state", False))
            elif cmd_type == "set_alert_thresholds":
                self._update_alert_thresholds(data)
            elif cmd_type == "reboot":
                print("🔄 Reboot command received (simulated)")
            elif cmd_type == "diagnostics":
                self._run_diagnostics()
            else:
                print(f"❓ Unknown command: {cmd_type}")
                
        except Exception as e:
            print(f"❌ Command execution error: {e}")
            
    def _update_configuration(self, config: Dict[str, Any]) -> None:
        """Update device configuration"""
        print(f"⚙️  Configuration update: {config}")
        
        # Update telemetry intervals
        global TELEMETRY_INTERVAL, FAST_TELEMETRY_INTERVAL
        if "telemetry_interval" in config:
            TELEMETRY_INTERVAL = config["telemetry_interval"]
            
        if "fast_telemetry_interval" in config:
            FAST_TELEMETRY_INTERVAL = config["fast_telemetry_interval"]
            
    def _control_relay(self, state: bool) -> None:
        """Control relay output"""
        GPIO.output(RELAY_PIN, GPIO.HIGH if state else GPIO.LOW)
        self.device_state["relay_state"] = state
        print(f"🔌 Relay {'ON' if state else 'OFF'}")
        
    def _update_alert_thresholds(self, thresholds: Dict[str, Any]) -> None:
        """Update alert thresholds"""
        self.edge_processor.alert_thresholds.update(thresholds)
        print(f"⚠️  Alert thresholds updated: {thresholds}")
        
    def _run_diagnostics(self) -> None:
        """Run system diagnostics"""
        print("🔍 Running diagnostics...")
        
        diagnostics = {
            "sensors": {
                "bme280": self._read_bme280() is not None,
                "mpu6050": self._read_mpu6050() is not None,
                "ads1115": True  # Simulated
            },
            "connectivity": {
                "cloud_connected": self.device_state["online"],
                "offline_buffer_size": self.offline_buffer.qsize()
            },
            "system": {
                "gpio_functional": True,
                "i2c_functional": True,
                "memory_available": True
            }
        }
        
        # Send diagnostics as event
        if self.cloud_manager:
            self.cloud_manager.send_to_active({
                "event_type": "diagnostics_report",
                "timestamp": datetime.utcnow().isoformat(),
                "diagnostics": diagnostics
            })
            
    def _check_alerts(self) -> None:
        """Check for alert conditions"""
        if not self.device_state.get("last_telemetry"):
            return
            
        # Check if any anomalies were detected
        recent_anomalies = getattr(self.edge_processor, 'last_anomalies', [])
        
        alert_active = len(recent_anomalies) > 0
        
        if alert_active != self.device_state["alert_active"]:
            self.device_state["alert_active"] = alert_active
            
            if alert_active:
                print(f"🚨 ALERT: {', '.join(recent_anomalies)}")
                self._activate_alert()
                
                # Send alert event to cloud
                if self.cloud_manager:
                    alert_data = {
                        "event_type": "alert_triggered",
                        "timestamp": datetime.utcnow().isoformat(),
                        "anomalies": recent_anomalies,
                        "severity": "high" if len(recent_anomalies) > 2 else "medium"
                    }
                    
                    for connector in self.cloud_manager.connectors.values():
                        if connector.connected:
                            connector.send_event("alert", alert_data)
            else:
                print("✅ Alert condition cleared")
                self._deactivate_alert()
                
    def _activate_alert(self) -> None:
        """Activate alert indicators"""
        GPIO.output(ALERT_LED_PIN, GPIO.HIGH)
        
        # Sound buzzer briefly
        GPIO.output(BUZZER_PIN, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(BUZZER_PIN, GPIO.LOW)
        
    def _deactivate_alert(self) -> None:
        """Deactivate alert indicators"""
        GPIO.output(ALERT_LED_PIN, GPIO.LOW)
        
    def _update_status_led(self) -> None:
        """Update status LED based on system state"""
        if self.device_state["online"]:
            # Slow blink when online
            current_state = GPIO.input(STATUS_LED_PIN)
            GPIO.output(STATUS_LED_PIN, not current_state)
        else:
            # Fast blink when offline
            GPIO.output(STATUS_LED_PIN, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(STATUS_LED_PIN, GPIO.LOW)
            
    def _on_cloud_connected(self, data: Dict[str, Any]) -> None:
        """Handle cloud connection event"""
        print(f"☁️  Connected to {data.get('hub', 'cloud')}")
        self.device_state["online"] = True
        
    def _on_cloud_disconnected(self, data: Dict[str, Any]) -> None:
        """Handle cloud disconnection event"""
        print("☁️  Disconnected from cloud")
        self.device_state["online"] = False


def main():
    """Main function"""
    print("🌐 IoT Cloud Dashboard - Advanced PiStudio Example")
    print("=" * 60)
    print("Features:")
    print("• Multi-cloud integration (Azure, AWS, Google Cloud)")
    print("• Real-time sensor data streaming")
    print("• Edge computing and local analytics")
    print("• Remote device control via cloud commands")
    print("• Fault tolerance with offline buffering")
    print("• Anomaly detection and alerting")
    print("• System diagnostics and monitoring")
    print()
    
    # Initialize and start dashboard
    dashboard = IoTCloudDashboard()
    dashboard.device_state["start_time"] = time.time()
    
    try:
        dashboard.start()
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
    finally:
        dashboard.stop()


if __name__ == "__main__":
    main()