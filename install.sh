#!/bin/bash
# PiStudio Installation Script

set -e

echo "Installing PiStudio - Raspberry Pi Simulator"
echo "============================================="

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.11+ required, found $python_version"
    exit 1
fi

echo "✓ Python $python_version detected"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✓ Poetry available"

# Install dependencies
echo "Installing dependencies..."
poetry install

# Install in development mode
echo "Installing PiStudio..."
poetry run pip install -e .

# Create desktop entry (Linux only)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Creating desktop entry..."
    
    desktop_file="$HOME/.local/share/applications/pistudio.desktop"
    mkdir -p "$(dirname "$desktop_file")"
    
    cat > "$desktop_file" << EOF
[Desktop Entry]
Name=PiStudio
Comment=Raspberry Pi Simulator
Exec=$(poetry env info --path)/bin/python -m apps.desktop
Icon=computer
Terminal=false
Type=Application
Categories=Development;Electronics;
EOF
    
    echo "✓ Desktop entry created"
fi

echo ""
echo "Installation complete!"
echo ""
echo "Usage:"
echo "  pistudio init my-project          # Create new project"
echo "  pistudio run                      # Run GUI"
echo "  pistudio run --headless           # Run headless"
echo ""
echo "Examples:"
echo "  cd examples/blink_led && pistudio run"
echo ""
echo "Documentation: https://github.com/pistudio/pistudio"