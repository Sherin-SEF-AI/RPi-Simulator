# PiStudio Architecture

## Overview

PiStudio is a comprehensive Raspberry Pi simulator built with a modular, event-driven architecture. It provides accurate hardware simulation, timing-precise GPIO operations, and a complete development environment for embedded projects.

## Core Components

### 1. Simulation Core (`packages/sim_core/`)

**Purpose**: Provides the fundamental simulation engine with deterministic timing.

**Key Classes**:
- `SimClock`: Deterministic simulation clock with configurable timestep (1µs-1ms)
- `EventBus`: Pub/sub messaging system for component communication
- `Signal`: Digital/analog signal representation with edge detection
- `Scheduler`: Priority queue for future event scheduling

**Features**:
- Fixed-timestep simulation for reproducible results
- Event recording/replay for testing
- Microsecond-precision timing
- Memory-efficient signal storage

### 2. Board Definitions (`packages/board_pi/`)

**Purpose**: Hardware specifications for different Raspberry Pi models.

**Key Classes**:
- `PiBoard`: Base class for Pi models
- `Pi3B`, `Pi4B`, `PiZero2W`: Specific board implementations
- `GpioPin`: Individual pin with mode, pull-up/down, alternative functions

**Features**:
- Accurate pin mappings (BCM/Board numbering)
- Alternative function definitions (I2C, SPI, PWM, etc.)
- Power/ground pin identification
- Pin state management

### 3. Peripheral Controllers (`packages/peripherals/`)

**Purpose**: Bus controllers with protocol-accurate timing.

**Components**:
- `GpioController`: Digital I/O with edge detection
- `I2cController`: Multi-device I2C bus with clock stretching
- `SpiController`: SPI with configurable modes and speeds
- `UartController`: Serial communication with error injection
- `PwmController`: Hardware PWM with frequency/duty control

**Features**:
- Real protocol timing simulation
- Bus contention and error modeling
- Event generation for logic analysis
- Device registration and management

### 4. Virtual Devices (`packages/devices/`)

**Purpose**: Simulated sensors, actuators, and displays.

**Device Categories**:
- **Sensors**: DHT22, BME280, HC-SR04, MPU6050, etc.
- **Actuators**: LEDs, servos, motors
- **Displays**: LCD, OLED, 7-segment
- **Communication**: ESP modules, BLE simulators

**Features**:
- Realistic behavior with noise/drift
- Configurable parameters via UI
- Fault injection capabilities
- Environment interaction

### 5. Code Runner (`packages/runner/`)

**Purpose**: Sandboxed execution environment for user code.

**Components**:
- `PythonRunner`: Python execution with RPi.GPIO shim
- `CodeRunner`: Multi-language coordinator
- Compatibility shims for popular libraries

**Features**:
- RPi.GPIO API compatibility
- Simulation time integration
- Memory/CPU limits
- Output capture and redirection

### 6. Desktop GUI (`apps/desktop/`)

**Purpose**: PyQt6-based visual interface.

**Components**:
- `MainWindow`: Primary application window
- `BreadboardWidget`: Visual breadboard with drag-and-drop
- `PinInspectorWidget`: Real-time GPIO monitoring
- `DevicePanelWidget`: Device control interfaces
- `ConsoleWidget`: Code editor and execution

**Features**:
- Dark theme optimized for development
- Real-time signal visualization
- Interactive device controls
- Integrated code editor

### 7. Headless Server (`apps/server/`)

**Purpose**: FastAPI-based headless simulation server.

**APIs**:
- REST endpoints for simulation control
- WebSocket for real-time updates
- JSON-RPC for device interactions

**Features**:
- CI/CD integration
- Remote simulation control
- Batch processing capabilities

### 8. Test Framework (`packages/testkit/`)

**Purpose**: Automated testing and validation.

**Components**:
- `PinAssertions`: GPIO state validation
- `I2cAssertions`: Bus transaction verification
- `TimingAssertions`: Event sequence checking
- `TraceRecorder`: Simulation recording/replay

**Features**:
- PyTest integration
- Golden trace comparison
- Timing tolerance handling
- Automated regression testing

## Data Flow

```
User Code → Code Runner → Peripheral Controllers → Virtual Devices
    ↓              ↓              ↓                    ↓
Event Bus ← Simulation Core ← Signal Processing ← Device Updates
    ↓
GUI/API Updates
```

## Event System

All components communicate through a central event bus:

1. **GPIO Events**: Pin state changes, edges, PWM updates
2. **Bus Events**: I2C/SPI/UART transactions
3. **Device Events**: Sensor readings, actuator movements
4. **System Events**: Simulation start/stop/reset

## Timing Model

- **Deterministic Clock**: Fixed timestep ensures reproducible results
- **Event Scheduling**: Future events queued by priority
- **Signal Sampling**: Configurable sample rates for different signals
- **Protocol Timing**: Accurate bus timing based on specifications

## Plugin Architecture

Extensible plugin system for custom devices:

1. **Device Plugins**: Custom sensors/actuators
2. **Protocol Plugins**: New bus types
3. **Tool Plugins**: Analysis and debugging tools
4. **UI Plugins**: Custom control panels

## Performance Optimizations

- **Lazy Evaluation**: Only compute active signals
- **Event Batching**: Group related events
- **Memory Management**: Configurable history limits
- **Cython Hotpaths**: Critical loops in compiled code

## Security Model

- **Sandboxed Execution**: User code runs in restricted environment
- **Resource Limits**: CPU/memory constraints
- **File System Isolation**: Virtual overlay for user files
- **Network Restrictions**: Configurable network access

## Cross-Platform Support

- **Linux**: Primary development platform
- **macOS**: Full feature support
- **Windows**: Core functionality (GUI may have limitations)

## Configuration Management

- **Project Files**: JSON-based project configuration
- **Device Parameters**: Runtime-configurable device settings
- **Environment Variables**: Simulation environment control
- **User Preferences**: GUI layout and behavior settings

## Extension Points

1. **Custom Devices**: Implement `VirtualDevice` base class
2. **New Protocols**: Extend peripheral controllers
3. **Analysis Tools**: Add to logic analyzer framework
4. **Export Formats**: Custom trace/report generators

This architecture provides a solid foundation for accurate Raspberry Pi simulation while maintaining extensibility and performance.