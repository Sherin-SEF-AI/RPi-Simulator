# Installation Guide

This guide covers different installation methods for RPi Simulator across various platforms.

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.11 or higher
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Graphics**: OpenGL 3.3 support for GUI mode

### Recommended Requirements
- **RAM**: 8GB or more
- **CPU**: Multi-core processor (4+ cores)
- **Graphics**: Dedicated GPU for complex simulations
- **Storage**: SSD for better performance

## 🚀 Quick Installation

### Using pip (Recommended)

```bash
# Install from PyPI
pip install rpi-simulator

# Verify installation
pistudio --version

# Create your first project
pistudio init my-first-project --template blink-led
cd my-first-project
pistudio run
```

### Using Poetry

```bash
# Create new project with Poetry
poetry new my-rpi-project
cd my-rpi-project

# Add RPi Simulator as dependency
poetry add rpi-simulator

# Run in virtual environment
poetry run pistudio init . --template sensors
poetry run pistudio run
```

## 🔧 Development Installation

### From Source

```bash
# Clone repository
git clone https://github.com/Sherin-SEF-AI/RPi-Simulator.git
cd RPi-Simulator

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Run desktop application
poetry run python -m apps.desktop

# Run headless server
poetry run python -m apps.server
```

### Docker Installation

```bash
# Pull Docker image
docker pull sherinsefai/rpi-simulator:latest

# Run headless mode
docker run -p 8000:8000 sherinsefai/rpi-simulator:latest

# Run with volume mounting for projects
docker run -p 8000:8000 -v $(pwd)/projects:/app/projects sherinsefai/rpi-simulator:latest

# Access web interface at http://localhost:8000
```

## 🖥️ Platform-Specific Instructions

### Windows

#### Using Windows Installer
1. Download `RPi-Simulator-Setup.exe` from [releases](https://github.com/Sherin-SEF-AI/RPi-Simulator/releases)
2. Run installer as administrator
3. Follow installation wizard
4. Launch from Start Menu or desktop shortcut

#### Using Chocolatey
```powershell
# Install Chocolatey (if not installed)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install RPi Simulator
choco install rpi-simulator
```

#### Using Scoop
```powershell
# Install Scoop (if not installed)
iwr -useb get.scoop.sh | iex

# Add bucket and install
scoop bucket add extras
scoop install rpi-simulator
```

### macOS

#### Using Homebrew
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add tap and install
brew tap sherin-sef-ai/rpi-simulator
brew install rpi-simulator

# Launch application
pistudio
```

#### Using MacPorts
```bash
# Install MacPorts (if not installed)
# Download from https://www.macports.org/install.php

# Install RPi Simulator
sudo port install rpi-simulator
```

### Linux

#### Ubuntu/Debian
```bash
# Add repository
curl -fsSL https://packages.sherinjosephroy.link/gpg | sudo apt-key add -
echo "deb https://packages.sherinjosephroy.link/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/rpi-simulator.list

# Update and install
sudo apt update
sudo apt install rpi-simulator

# Install dependencies for GUI mode
sudo apt install python3-pyqt6 python3-pyqt6.qtopengl
```

#### Fedora/CentOS/RHEL
```bash
# Add repository
sudo dnf config-manager --add-repo https://packages.sherinjosephroy.link/fedora/rpi-simulator.repo

# Install
sudo dnf install rpi-simulator

# Install GUI dependencies
sudo dnf install python3-qt6 python3-qt6-devel
```

#### Arch Linux
```bash
# Install from AUR
yay -S rpi-simulator

# Or using makepkg
git clone https://aur.archlinux.org/rpi-simulator.git
cd rpi-simulator
makepkg -si
```

#### Snap Package
```bash
# Install from Snap Store
sudo snap install rpi-simulator

# Run application
rpi-simulator
```

#### Flatpak
```bash
# Add Flathub repository
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install RPi Simulator
flatpak install flathub com.sherinjosephroy.RPiSimulator

# Run application
flatpak run com.sherinjosephroy.RPiSimulator
```

## 🐍 Python Environment Setup

### Using pyenv (Recommended)
```bash
# Install pyenv
curl https://pyenv.run | bash

# Install Python 3.11
pyenv install 3.11.6
pyenv global 3.11.6

# Install RPi Simulator
pip install rpi-simulator
```

### Using conda/mamba
```bash
# Create environment
conda create -n rpi-sim python=3.11
conda activate rpi-sim

# Install from conda-forge
conda install -c conda-forge rpi-simulator

# Or install via pip in conda environment
pip install rpi-simulator
```

### Using venv
```bash
# Create virtual environment
python3.11 -m venv rpi-simulator-env
source rpi-simulator-env/bin/activate  # Linux/macOS
# rpi-simulator-env\Scripts\activate  # Windows

# Install RPi Simulator
pip install rpi-simulator
```

## ⚙️ Configuration

### First-Time Setup
```bash
# Initialize configuration
pistudio config init

# Set default project directory
pistudio config set projects.default_path ~/rpi-projects

# Configure GUI preferences
pistudio config set gui.theme dark
pistudio config set gui.auto_save true

# Set up device library paths
pistudio config set devices.library_path ~/.pistudio/devices
```

### Environment Variables
```bash
# Optional environment variables
export PISTUDIO_HOME=~/.pistudio
export PISTUDIO_PROJECTS=~/rpi-projects
export PISTUDIO_LOG_LEVEL=INFO
export PISTUDIO_GUI_THEME=dark
```

## 🔍 Verification

### Test Installation
```bash
# Check version
pistudio --version

# Run self-test
pistudio test --quick

# Create and run test project
pistudio init test-project --template blink-led
cd test-project
pistudio run --headless --duration 10s
```

### GUI Test
```bash
# Launch GUI application
pistudio gui

# Check for any error messages in console
# Verify all menu items are accessible
# Test creating a new project
```

### API Test
```bash
# Start headless server
pistudio serve --port 8000 &

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/projects

# Stop server
pistudio stop
```

## 🚨 Troubleshooting

### Common Issues

#### Python Version Error
```bash
# Error: Python 3.11+ required
# Solution: Install correct Python version
pyenv install 3.11.6
pyenv global 3.11.6
```

#### GUI Not Starting
```bash
# Error: Qt platform plugin not found
# Solution: Install Qt dependencies
# Ubuntu/Debian:
sudo apt install python3-pyqt6 libqt6gui6

# macOS:
brew install qt6

# Windows: Usually included with pip installation
```

#### Permission Errors
```bash
# Error: Permission denied
# Solution: Use virtual environment or user installation
pip install --user rpi-simulator
```

#### Import Errors
```bash
# Error: Module not found
# Solution: Check Python path and virtual environment
python -c "import pistudio; print(pistudio.__version__)"
```

### Getting Help

- **Documentation**: [https://rpi-simulator.readthedocs.io](https://rpi-simulator.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/Sherin-SEF-AI/RPi-Simulator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Sherin-SEF-AI/RPi-Simulator/discussions)
- **Discord**: [Developer Community](https://discord.gg/rpi-simulator)
- **Email**: [connect@sherinjosephroy.link](mailto:connect@sherinjosephroy.link)

## 📦 Uninstallation

### pip Installation
```bash
pip uninstall rpi-simulator
```

### System Package
```bash
# Ubuntu/Debian
sudo apt remove rpi-simulator

# Fedora/CentOS
sudo dnf remove rpi-simulator

# macOS Homebrew
brew uninstall rpi-simulator
```

### Clean Removal
```bash
# Remove configuration and data
rm -rf ~/.pistudio
rm -rf ~/rpi-projects  # If using default location
```

---

**Next Steps**: After installation, check out the [Getting Started Guide](../GETTING_STARTED.md) to create your first project!