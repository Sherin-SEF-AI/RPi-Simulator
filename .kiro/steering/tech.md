# Technology Stack

## Build System & Package Management
- **Poetry**: Primary dependency management and build system
- **Python 3.11+**: Minimum required version
- **PyProject.toml**: Modern Python packaging configuration

## Core Technologies
- **PyQt6**: Desktop GUI framework with dark/light theme support
- **FastAPI**: REST API and headless server implementation
- **NumPy**: Numerical computations and signal processing
- **Matplotlib/Plotly**: Data visualization and plotting
- **WebSockets**: Real-time communication for web interface
- **Pydantic**: Data validation and settings management

## Development Tools
- **Black**: Code formatting (88 character line length)
- **isort**: Import sorting (black profile)
- **MyPy**: Static type checking
- **pytest**: Testing framework with asyncio support
- **pre-commit**: Git hooks for code quality

## Common Commands

### Setup & Installation
```bash
# Install from source
poetry install
poetry run pre-commit install

# Quick install via script
./install.sh
```

### Development Workflow
```bash
# Run desktop GUI
make run-gui
# or: poetry run python -m apps.desktop

# Run headless server
make run-server
# or: poetry run python -m apps.server

# CLI interface
poetry run pistudio --help
```

### Testing & Quality
```bash
# Run tests
make test
# or: poetry run pytest tests/ -v

# Test with coverage
make test-coverage

# Code formatting
make format
# or: poetry run black . && poetry run isort .

# Linting
make lint
```

### Project Management
```bash
# Initialize new project
pistudio init <project-name> --template <template>

# Add devices
pistudio add <device-type> --gpio <pin> --name <name>

# Run simulation
pistudio run [--gui|--headless]
```

## Architecture Patterns
- **Event-driven architecture**: Central EventBus for component communication
- **Plugin system**: Extensible device and protocol plugins
- **Modular packages**: Each major component is a separate package
- **Dependency injection**: Configuration-driven component assembly
- **Sandboxed execution**: Safe user code execution with resource limits