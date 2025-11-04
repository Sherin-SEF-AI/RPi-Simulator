# Project Structure

## Root Directory Layout
```
RPi-Simulator/
├── packages/           # Core simulation packages (modular architecture)
├── apps/              # User interface applications
├── examples/          # Sample projects and tutorials
├── tests/            # Test suite
├── docs/             # Documentation
├── templates/        # Project templates (python, c, node)
├── .kiro/            # Kiro IDE configuration and steering
├── .github/          # GitHub workflows and templates
└── pyproject.toml    # Poetry configuration and dependencies
```

## Package Organization (`packages/`)
Each package is a self-contained module with clear responsibilities:

- **`sim_core/`**: Event system, timing, signals, scheduler (simulation engine)
- **`board_pi/`**: Hardware definitions for Pi models and GPIO pins
- **`peripherals/`**: Protocol controllers (GPIO, I2C, SPI, UART, PWM)
- **`devices/`**: Virtual device library (sensors, actuators, displays)
- **`runner/`**: Code execution environment with language support
- **`pistudio/`**: Main application logic, CLI, and project management
- **`logic_tools/`**: Logic analyzer and protocol decoder
- **`physics_engine/`**: 3D physics simulation for realistic behavior
- **`testkit/`**: Testing framework and assertions
- **`plugin_host/`**: Plugin system and extensibility

## Application Structure (`apps/`)
- **`desktop/`**: PyQt6 GUI application with widgets and main window
- **`server/`**: FastAPI headless server for remote/CI usage

## Project Configuration
- **`pistudio.json`**: Project configuration file defining devices, connections, environment
- **`main.py`**: Primary user code entry point
- **`src/`**: Source code directory (optional, for organized projects)
- **`tests/`**: Project-specific tests (optional)

## Naming Conventions
- **Packages**: Snake_case (e.g., `sim_core`, `board_pi`)
- **Classes**: PascalCase (e.g., `PiSimulator`, `GpioController`)
- **Functions/Variables**: Snake_case (e.g., `setup_gpio`, `pin_state`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_FREQUENCY`)
- **Files**: Snake_case with descriptive names (e.g., `logic_analyzer.py`)

## Import Structure
- Each package has `__init__.py` with explicit `__all__` exports
- Relative imports within packages, absolute imports between packages
- Main classes/functions exposed at package level for clean API

## Configuration Files
- **`pyproject.toml`**: Poetry dependencies, build config, tool settings
- **`Makefile`**: Development workflow commands
- **`.gitignore`**: Standard Python ignores plus simulation artifacts
- **`install.sh`**: Quick installation script

## Example Project Structure
```
my-iot-project/
├── pistudio.json      # Device and connection configuration
├── main.py           # Primary application code
├── src/              # Additional source files (optional)
│   ├── sensors.py
│   └── display.py
└── tests/            # Project tests (optional)
    └── test_main.py
```

## Development Guidelines
- Keep packages focused and loosely coupled
- Use dependency injection for testability
- Follow event-driven patterns for component communication
- Maintain clear separation between simulation core and UI
- Write comprehensive tests for all public APIs