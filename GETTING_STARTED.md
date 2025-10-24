# Getting Started with PiStudio

## Installation

### Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)
- Git

### Quick Install

```bash
# Clone repository
git clone https://github.com/pistudio/pistudio.git
cd pistudio

# Run installation script
./install.sh
```

### Manual Installation

```bash
# Install Poetry if not available
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install PiStudio
poetry run pip install -e .
```

## First Steps

### 1. Create Your First Project

```bash
# Create a new Python project
pistudio init my-first-project --template python

# Navigate to project
cd my-first-project

# View project structure
ls -la
```

### 2. Add a Device

```bash
# Add an LED connected to GPIO18
pistudio add device --type led --name LED1 --pin 18

# Connect the LED in breadboard
pistudio connect --from GPIO18 --to LED1:anode
pistudio connect --from GND --to LED1:cathode
```

### 3. Run the Simulation

```bash
# Launch GUI
pistudio run

# Or run headless
pistudio run --headless
```

## Example Projects

### LED Blink

```python
#!/usr/bin/env python3
import RPiSim.GPIO as GPIO
import time

# Setup
GPIO.setmode(GPIO.BCM)
LED_PIN = 18
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    for i in range(10):
        GPIO.output(LED_PIN, GPIO.HIGH)
        print(f"LED ON - {i+1}")
        time.sleep(0.5)
        
        GPIO.output(LED_PIN, GPIO.LOW)
        print(f"LED OFF - {i+1}")
        time.sleep(0.5)
        
finally:
    GPIO.cleanup()
```

### I2C Sensor Reading

```python
#!/usr/bin/env python3
from sim_i2c import I2C
import time

# Initialize I2C
i2c = I2C(1)

# BME280 sensor at address 0x76
BME280_ADDR = 0x76

# Configure sensor
i2c.write_byte_data(BME280_ADDR, 0xF4, 0x27)  # Control register

# Read data
for i in range(10):
    data = i2c.read_i2c_block_data(BME280_ADDR, 0xF7, 6)
    print(f"Reading {i+1}: {data}")
    time.sleep(1)
```

## GUI Overview

### Main Interface

1. **Breadboard View**: Visual component placement and wiring
2. **Pin Inspector**: Real-time GPIO state monitoring
3. **Device Controls**: Interactive device parameter adjustment
4. **Code Console**: Integrated editor and execution environment
5. **Logic Analyzer**: Signal timing and protocol analysis

### Key Features

- **Drag-and-Drop Wiring**: Connect components visually
- **Real-Time Monitoring**: Watch pin states change live
- **Interactive Controls**: Adjust sensor values, move servos
- **Code Execution**: Run and debug code in simulation
- **Signal Analysis**: Examine timing and protocol details

## Command Line Interface

### Project Management

```bash
# Create new project
pistudio init <name> [--template python|c|node] [--board pi4|pi3b|zero2w]

# Add devices
pistudio add device --type <type> --name <name> [--pin <pin>] [--i2c <addr>]

# Connect pins
pistudio connect --from <source> --to <destination>
```

### Simulation Control

```bash
# Run with GUI
pistudio run

# Run headless
pistudio run --headless [--script <file>]

# Record trace
pistudio record --out trace.json [--duration <seconds>]

# Replay trace
pistudio replay trace.json [--assert-script <file>]
```

### Testing

```bash
# Run test suite
pistudio test [--suite <directory>]

# Run specific test
pytest tests/test_blink_led.py -v
```

## Device Library

### Sensors

- **DHT22**: Temperature/humidity sensor
- **BME280**: Environmental sensor (I2C)
- **HC-SR04**: Ultrasonic distance sensor
- **MPU6050**: 6-axis IMU (I2C)
- **DS18B20**: Temperature sensor (1-Wire)
- **LDR**: Light-dependent resistor
- **PIR**: Motion sensor

### Actuators

- **LED**: Single/RGB LEDs
- **Servo**: SG90-style servo motors
- **DC Motor**: With H-bridge control
- **Stepper**: Stepper motor with driver
- **Buzzer**: Piezo buzzer
- **Relay**: Switching relay

### Displays

- **LCD1602**: 16x2 character LCD (I2C)
- **SSD1306**: OLED display (I2C/SPI)
- **7-Segment**: LED segment display
- **NeoPixel**: Addressable RGB LEDs

### Communication

- **ESP-01**: WiFi module simulator
- **BLE**: Bluetooth Low Energy peripheral
- **GPS**: NMEA GPS receiver simulator

## Testing Framework

### Basic Assertions

```python
from testkit import PinAssertions, I2cAssertions

def test_led_blink():
    pins = PinAssertions(simulator.event_bus)
    
    # Assert LED toggles 10 times in 5 seconds
    pins.assert_pin_toggle(18, min_edges=10, within_ms=5000)
    
    # Assert specific pin states
    pins.assert_pin_high(18, within_ms=100)
    pins.assert_pin_low(18, within_ms=600)
```

### I2C Testing

```python
def test_i2c_communication():
    i2c = I2cAssertions(simulator.event_bus)
    
    # Assert write transaction
    i2c.assert_i2c_write(0x76, [0xF4, 0x27], within_ms=100)
    
    # Assert read transaction
    data = i2c.assert_i2c_read(0x76, 6, within_ms=100)
    assert len(data) == 6
```

## Configuration

### Project Configuration (pistudio.json)

```json
{
  "name": "My Project",
  "template": "python",
  "board": "pi4",
  "devices": [
    {
      "type": "led",
      "name": "LED1",
      "connection": {"pin": 18},
      "parameters": {"color": "red"}
    }
  ],
  "connections": [
    {
      "from_pin": "GPIO18",
      "to_pin": "LED1:anode",
      "wire_color": "red"
    }
  ],
  "environment": {
    "temperature": 25.0,
    "humidity": 50.0
  }
}
```

### Environment Variables

```bash
# Simulation timestep (microseconds)
export PISTUDIO_TIMESTEP=10

# Enable debug logging
export PISTUDIO_DEBUG=1

# Set default board type
export PISTUDIO_DEFAULT_BOARD=pi4
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Poetry environment is activated
2. **GUI Not Starting**: Check PyQt6 installation
3. **Device Not Found**: Verify device configuration and connections
4. **Timing Issues**: Adjust simulation timestep for accuracy vs. performance

### Debug Mode

```bash
# Enable verbose logging
PISTUDIO_DEBUG=1 pistudio run

# Check simulation events
pistudio run --headless --log-events
```

### Performance Tuning

```bash
# Reduce timestep for better performance
export PISTUDIO_TIMESTEP=100

# Limit signal history
export PISTUDIO_MAX_SAMPLES=1000
```

## Next Steps

1. **Explore Examples**: Check `examples/` directory for more projects
2. **Read Documentation**: See `docs/` for detailed API reference
3. **Join Community**: Visit GitHub discussions for help and ideas
4. **Contribute**: Submit issues and pull requests

## Resources

- **GitHub Repository**: https://github.com/pistudio/pistudio
- **Documentation**: https://pistudio.readthedocs.io
- **Examples**: https://github.com/pistudio/examples
- **Community**: https://github.com/pistudio/pistudio/discussions