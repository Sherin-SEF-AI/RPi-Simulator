# Contributing to RPi Simulator

Thank you for your interest in contributing to RPi Simulator! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- Poetry for dependency management
- Git for version control
- Basic knowledge of Raspberry Pi and embedded systems

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/RPi-Simulator.git
   cd RPi-Simulator
   ```

2. **Install Dependencies**
   ```bash
   poetry install
   poetry run pre-commit install
   ```

3. **Run Tests**
   ```bash
   poetry run pytest
   ```

4. **Start Development Server**
   ```bash
   poetry run python -m apps.desktop  # GUI mode
   poetry run python -m apps.server   # Headless mode
   ```

## 🎯 How to Contribute

### Reporting Bugs
- Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md)
- Include detailed reproduction steps
- Provide system information and logs
- Add screenshots if applicable

### Suggesting Features
- Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.md)
- Explain the use case and benefits
- Consider implementation complexity
- Discuss alternatives

### Code Contributions

#### 1. Choose an Issue
- Look for issues labeled `good first issue` for beginners
- Check `help wanted` for areas needing assistance
- Comment on issues you'd like to work on

#### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

#### 3. Make Changes
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

#### 4. Test Your Changes
```bash
# Run full test suite
poetry run pytest

# Run specific tests
poetry run pytest tests/test_specific_module.py

# Check code formatting
poetry run black --check .
poetry run isort --check-only .
poetry run mypy packages/
```

#### 5. Submit Pull Request
- Use a descriptive title
- Reference related issues
- Provide detailed description of changes
- Include screenshots for UI changes

## 📝 Code Style Guidelines

### Python Code Style
- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 88)
- Use isort for import sorting
- Add type hints for all functions
- Write docstrings for public APIs

### Example Code Style
```python
from typing import Optional, List
import numpy as np

class DeviceSimulator:
    """Simulates hardware device behavior.
    
    Args:
        device_id: Unique identifier for the device
        config: Device configuration parameters
    """
    
    def __init__(self, device_id: str, config: Optional[dict] = None) -> None:
        self.device_id = device_id
        self.config = config or {}
        self._state: dict = {}
    
    def read_sensor(self, sensor_type: str) -> Optional[float]:
        """Read sensor value with error handling.
        
        Args:
            sensor_type: Type of sensor to read
            
        Returns:
            Sensor reading or None if error
        """
        try:
            return self._simulate_reading(sensor_type)
        except Exception as e:
            logger.error(f"Sensor read failed: {e}")
            return None
```

### Commit Message Format
```
type(scope): brief description

Detailed explanation of changes if needed.

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── unit/           # Unit tests for individual modules
├── integration/    # Integration tests for component interaction
├── e2e/           # End-to-end tests for complete workflows
└── fixtures/      # Test data and mock objects
```

### Writing Tests
- Use pytest framework
- Aim for >90% code coverage
- Test both success and failure cases
- Use descriptive test names
- Mock external dependencies

### Example Test
```python
import pytest
from unittest.mock import Mock, patch

from packages.devices.sensors import TemperatureSensor

class TestTemperatureSensor:
    def test_read_temperature_success(self):
        """Test successful temperature reading."""
        sensor = TemperatureSensor(pin=4)
        
        with patch('packages.devices.sensors.read_gpio') as mock_read:
            mock_read.return_value = 3.3
            
            temperature = sensor.read_temperature()
            
            assert temperature == pytest.approx(25.0, rel=0.1)
            mock_read.assert_called_once_with(4)
    
    def test_read_temperature_sensor_error(self):
        """Test temperature reading with sensor error."""
        sensor = TemperatureSensor(pin=4)
        
        with patch('packages.devices.sensors.read_gpio') as mock_read:
            mock_read.side_effect = RuntimeError("GPIO read failed")
            
            with pytest.raises(RuntimeError):
                sensor.read_temperature()
```

## 📚 Documentation

### Code Documentation
- Write clear docstrings for all public APIs
- Use Google-style docstrings
- Include examples in docstrings
- Document complex algorithms

### User Documentation
- Update README.md for new features
- Add examples to `examples/` directory
- Update API documentation
- Create tutorials for complex features

## 🏗️ Architecture Guidelines

### Package Structure
- Keep packages focused and cohesive
- Minimize dependencies between packages
- Use dependency injection for testability
- Follow SOLID principles

### Device Implementation
```python
from packages.devices.base import BaseDevice

class NewSensor(BaseDevice):
    """Implementation of a new sensor type."""
    
    DEVICE_TYPE = "new_sensor"
    SUPPORTED_PROTOCOLS = ["i2c", "spi"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialize_sensor()
    
    def read(self) -> dict:
        """Read sensor data."""
        return {"value": self._read_raw_value()}
```

### Event System
- Use the event system for component communication
- Emit events for state changes
- Handle events asynchronously when possible

## 🔍 Review Process

### Pull Request Review
1. **Automated Checks**: CI/CD pipeline must pass
2. **Code Review**: At least one maintainer review required
3. **Testing**: New features must include tests
4. **Documentation**: User-facing changes need documentation updates

### Review Criteria
- Code quality and style
- Test coverage and quality
- Performance impact
- Security considerations
- Backward compatibility
- Documentation completeness

## 🎉 Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes for significant contributions
- GitHub contributor graphs
- Special mentions in documentation

## 📞 Getting Help

- **Discord**: Join our [developer community](https://discord.gg/rpi-simulator)
- **Discussions**: Use [GitHub Discussions](https://github.com/Sherin-SEF-AI/RPi-Simulator/discussions)
- **Email**: Contact [Sherin Joseph Roy](mailto:connect@sherinjosephroy.link)

## 📄 License

By contributing to RPi Simulator, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make RPi Simulator better! 🚀