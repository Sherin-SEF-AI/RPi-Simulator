"""
PiStudio Command Line Interface
"""

import click
import os
import sys
from pathlib import Path
from typing import Optional

from .project import Project
from .simulator import PiSimulator


@click.group()
@click.version_option()
def main():
    """PiStudio - Raspberry Pi Simulator for Embedded Development"""
    pass


@main.command()
@click.argument('project_name', required=False)
@click.option('--template', help='Project template (python, c, node)')
@click.option('--board', default='pi4', help='Board type (pi3b, pi4, zero2w)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive project wizard')
@click.option('--list-templates', is_flag=True, help='List available templates')
def init(project_name: Optional[str], template: Optional[str], board: str, 
         interactive: bool, list_templates: bool):
    """Create a new PiStudio project"""
    from .project_builder import ProjectBuilder
    
    builder = ProjectBuilder()
    
    if list_templates:
        templates = builder.list_templates()
        click.echo("Available Templates:")
        click.echo("=" * 50)
        
        for tmpl in templates:
            click.echo(f"📋 {tmpl['id']}")
            click.echo(f"   Name: {tmpl['name']}")
            click.echo(f"   Difficulty: {tmpl['difficulty']}")
            click.echo(f"   Description: {tmpl['description']}")
            click.echo(f"   Devices: {tmpl['device_count']}, Connections: {tmpl['connection_count']}")
            click.echo()
        return
    
    if interactive or not project_name:
        # Launch interactive wizard
        try:
            result = builder.interactive_wizard()
            if result["success"]:
                click.echo(f"✅ {result['message']}")
                project = result["project"]
                click.echo(f"📁 Project directory: {project.path}")
                
                # Show next steps
                click.echo("\n🚀 Next steps:")
                click.echo(f"  cd {project.config['name']}")
                click.echo("  pistudio run")
            else:
                click.echo(f"❌ {result['message']}", err=True)
                sys.exit(1)
        except KeyboardInterrupt:
            click.echo("\n👋 Project creation cancelled")
            sys.exit(0)
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            sys.exit(1)
    else:
        # Non-interactive mode
        try:
            if template:
                project = builder.create_from_template(template, project_name)
                click.echo(f"✅ Created project '{project_name}' from template '{template}'")
            else:
                project = Project.create(project_name, "python", board)
                click.echo(f"✅ Created project '{project_name}' with Python template")
                
            click.echo(f"🎯 Board: {board}")
            click.echo(f"📁 Project directory: {project.path}")
            
            # Show next steps
            click.echo("\n🚀 Next steps:")
            click.echo(f"  cd {project_name}")
            click.echo("  pistudio add device --type led --pin 18")
            click.echo("  pistudio run")
            
        except Exception as e:
            click.echo(f"❌ Error creating project: {e}", err=True)
            sys.exit(1)


@main.command()
@click.option('--type', required=True, help='Device type (led, bme280, servo, etc.)')
@click.option('--name', help='Device name (auto-generated if not provided)')
@click.option('--pin', type=int, help='GPIO pin number')
@click.option('--i2c', help='I2C address (e.g., 0x76)')
@click.option('--spi', help='SPI device (e.g., 0.0)')
def add(type: str, name: Optional[str], pin: Optional[int], 
        i2c: Optional[str], spi: Optional[str]):
    """Add a device to the current project"""
    try:
        project = Project.load_current()
        
        # Auto-generate name if not provided
        if not name:
            existing_count = len([d for d in project.devices if d.type == type])
            name = f"{type}{existing_count + 1}"
            
        # Parse connection parameters
        connection = {}
        if pin is not None:
            connection['pin'] = pin
        if i2c:
            connection['i2c'] = int(i2c, 16) if i2c.startswith('0x') else int(i2c)
        if spi:
            connection['spi'] = spi
            
        project.add_device(type, name, connection)
        project.save()
        
        click.echo(f"Added {type} device '{name}'")
        if connection:
            click.echo(f"Connection: {connection}")
            
    except Exception as e:
        click.echo(f"Error adding device: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--from', 'from_pin', required=True, help='Source pin (e.g., GPIO18)')
@click.option('--to', required=True, help='Destination (e.g., LED1:anode)')
def connect(from_pin: str, to: str):
    """Connect pins in the breadboard"""
    try:
        project = Project.load_current()
        project.add_connection(from_pin, to)
        project.save()
        
        click.echo(f"Connected {from_pin} to {to}")
        
    except Exception as e:
        click.echo(f"Error connecting pins: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--headless', is_flag=True, help='Run without GUI')
@click.option('--board', help='Override board type')
@click.option('--script', help='Python script to run')
def run(headless: bool, board: Optional[str], script: Optional[str]):
    """Run the simulation"""
    try:
        project = Project.load_current()
        
        if board:
            project.config['board'] = board
            
        simulator = PiSimulator(project.config)
        
        if headless:
            click.echo("Starting headless simulation...")
            simulator.run_headless(script)
        else:
            click.echo("Starting GUI simulation...")
            simulator.run_gui()
            
    except Exception as e:
        click.echo(f"Error running simulation: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--out', required=True, help='Output trace file')
@click.option('--duration', type=float, help='Recording duration in seconds')
def record(out: str, duration: Optional[float]):
    """Record simulation trace"""
    try:
        project = Project.load_current()
        simulator = PiSimulator(project.config)
        
        click.echo(f"Recording trace to {out}...")
        simulator.record_trace(out, duration)
        click.echo("Recording complete")
        
    except Exception as e:
        click.echo(f"Error recording: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('trace_file')
@click.option('--assert-script', help='Assertion script to run')
def replay(trace_file: str, assert_script: Optional[str]):
    """Replay simulation trace"""
    try:
        project = Project.load_current()
        simulator = PiSimulator(project.config)
        
        click.echo(f"Replaying trace from {trace_file}...")
        result = simulator.replay_trace(trace_file, assert_script)
        
        if result:
            click.echo("Replay successful")
        else:
            click.echo("Replay failed", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error replaying: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--suite', help='Test suite directory')
@click.option('--coverage', is_flag=True, help='Generate coverage report')
@click.option('--interactive', '-i', is_flag=True, help='Interactive test runner')
def test(suite: Optional[str], coverage: bool, interactive: bool):
    """Run test suite with advanced options"""
    try:
        if not suite:
            suite = "tests"
            
        if interactive:
            # Interactive test selection
            click.echo("🧪 Interactive Test Runner")
            click.echo("=" * 30)
            
            if os.path.exists(suite):
                test_files = []
                for root, dirs, files in os.walk(suite):
                    for file in files:
                        if file.startswith("test_") and file.endswith(".py"):
                            test_files.append(os.path.join(root, file))
                            
                if test_files:
                    click.echo("Available test files:")
                    for i, test_file in enumerate(test_files, 1):
                        click.echo(f"  {i}. {test_file}")
                    click.echo(f"  {len(test_files) + 1}. Run all tests")
                    
                    choice = click.prompt("Select tests to run", type=int)
                    
                    if 1 <= choice <= len(test_files):
                        suite = test_files[choice - 1]
                    elif choice == len(test_files) + 1:
                        suite = "tests"
                    else:
                        click.echo("Invalid selection")
                        return
                else:
                    click.echo("No test files found")
                    return
            else:
                click.echo(f"Test directory '{suite}' not found")
                return
                
        if not os.path.exists(suite):
            click.echo(f"❌ Test suite directory not found: {suite}", err=True)
            sys.exit(1)
            
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest", suite, "-v"]
        
        if coverage:
            cmd.extend(["--cov=pistudio", "--cov-report=html", "--cov-report=term"])
            
        # Run pytest
        import subprocess
        click.echo(f"🧪 Running tests: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        click.echo(result.stdout)
        if result.stderr:
            click.echo(result.stderr, err=True)
            
        if coverage and result.returncode == 0:
            click.echo("\n📊 Coverage report generated in htmlcov/")
            
        if result.returncode == 0:
            click.echo("✅ All tests passed!")
        else:
            click.echo("❌ Some tests failed")
            
        sys.exit(result.returncode)
        
    except Exception as e:
        click.echo(f"❌ Error running tests: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--format', 'output_format', default='table', 
              type=click.Choice(['table', 'json', 'yaml']),
              help='Output format')
def status():
    """Show project status and information"""
    try:
        project = Project.load_current()
        
        if output_format == 'json':
            import json
            status_data = {
                "name": project.config["name"],
                "board": project.config["board"],
                "devices": len(project.devices),
                "connections": len(project.connections),
                "template": project.config.get("template", "unknown")
            }
            click.echo(json.dumps(status_data, indent=2))
            
        elif output_format == 'yaml':
            import yaml
            status_data = {
                "name": project.config["name"],
                "board": project.config["board"],
                "devices": len(project.devices),
                "connections": len(project.connections),
                "template": project.config.get("template", "unknown")
            }
            click.echo(yaml.dump(status_data, default_flow_style=False))
            
        else:  # table format
            click.echo("📊 Project Status")
            click.echo("=" * 40)
            click.echo(f"Name:        {project.config['name']}")
            click.echo(f"Board:       {project.config['board']}")
            click.echo(f"Template:    {project.config.get('template', 'unknown')}")
            click.echo(f"Devices:     {len(project.devices)}")
            click.echo(f"Connections: {len(project.connections)}")
            
            if project.devices:
                click.echo("\n🔌 Devices:")
                for device in project.devices:
                    conn_str = ", ".join(f"{k}={v}" for k, v in device.connection.items())
                    click.echo(f"  • {device.name} ({device.type}) - {conn_str}")
                    
            if project.connections:
                click.echo("\n🔗 Connections:")
                for conn in project.connections:
                    click.echo(f"  • {conn.from_pin} → {conn.to_pin} ({conn.wire_color})")
                    
    except Exception as e:
        click.echo(f"❌ Error getting project status: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--device', help='Device name to configure')
@click.option('--parameter', help='Parameter name')
@click.option('--value', help='Parameter value')
@click.option('--list', 'list_params', is_flag=True, help='List device parameters')
def config(device: Optional[str], parameter: Optional[str], 
          value: Optional[str], list_params: bool):
    """Configure device parameters"""
    try:
        project = Project.load_current()
        
        if list_params:
            if device:
                # List parameters for specific device
                dev = project.get_device(device)
                if dev:
                    click.echo(f"⚙️  Parameters for {device}:")
                    for param_name, param_value in dev.parameters.items():
                        click.echo(f"  {param_name}: {param_value}")
                else:
                    click.echo(f"❌ Device '{device}' not found")
            else:
                # List all devices and their parameters
                click.echo("⚙️  Device Configuration:")
                for dev in project.devices:
                    click.echo(f"\n📱 {dev.name} ({dev.type}):")
                    for param_name, param_value in dev.parameters.items():
                        click.echo(f"  {param_name}: {param_value}")
        else:
            if device and parameter and value:
                # Set parameter value
                dev = project.get_device(device)
                if dev:
                    dev.parameters[parameter] = value
                    project.save()
                    click.echo(f"✅ Set {device}.{parameter} = {value}")
                else:
                    click.echo(f"❌ Device '{device}' not found")
            else:
                click.echo("❌ Please specify --device, --parameter, and --value")
                
    except Exception as e:
        click.echo(f"❌ Error configuring device: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--output', '-o', help='Output file for export')
@click.option('--format', 'export_format', default='zip',
              type=click.Choice(['zip', 'tar', 'folder']),
              help='Export format')
def export(output: Optional[str], export_format: str):
    """Export project for sharing"""
    try:
        project = Project.load_current()
        
        if not output:
            output = f"{project.config['name']}.{export_format}"
            
        click.echo(f"📦 Exporting project to {output}...")
        
        if export_format == 'zip':
            import zipfile
            with zipfile.ZipFile(output, 'w') as zf:
                for root, dirs, files in os.walk(project.path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, project.path)
                        zf.write(file_path, arc_path)
                        
        elif export_format == 'tar':
            import tarfile
            with tarfile.open(output, 'w:gz') as tf:
                tf.add(project.path, arcname=project.config['name'])
                
        elif export_format == 'folder':
            import shutil
            shutil.copytree(project.path, output)
            
        click.echo(f"✅ Project exported to {output}")
        
    except Exception as e:
        click.echo(f"❌ Error exporting project: {e}", err=True)
        sys.exit(1)


@main.group()
def plugin():
    """Plugin management commands"""
    pass


@plugin.command()
@click.argument('name')
@click.option('--type', 'plugin_type', default='sensor',
              type=click.Choice(['sensor', 'actuator', 'display', 'communication', 'generic']),
              help='Plugin type')
@click.option('--output', '-o', default='./plugins', help='Output directory')
@click.option('--author', default='PiStudio User', help='Plugin author')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
def create(name: str, plugin_type: str, output: str, author: str, interactive: bool):
    """Create a new device plugin"""
    try:
        from plugin_host.plugin_generator import PluginGenerator
        
        generator = PluginGenerator()
        
        if interactive:
            generator.interactive_generator()
        else:
            output_path = Path(output)
            options = {"author": author}
            
            success = generator.generate_device_plugin(name, plugin_type, output_path, options)
            
            if success:
                click.echo(f"✅ Plugin '{name}' created successfully!")
                plugin_dir = output_path / f"{generator._sanitize_name(name)}_plugin"
                click.echo(f"📁 Location: {plugin_dir}")
                
                click.echo("\n📋 Next steps:")
                click.echo("1. Customize the device implementation")
                click.echo("2. Test the plugin: pistudio plugin test <plugin_dir>")
                click.echo("3. Install the plugin: pistudio plugin install <plugin_dir>")
            else:
                click.echo(f"❌ Failed to create plugin '{name}'")
                sys.exit(1)
                
    except Exception as e:
        click.echo(f"❌ Error creating plugin: {e}", err=True)
        sys.exit(1)


@plugin.command()
@click.argument('plugin_path')
def install(plugin_path: str):
    """Install a plugin"""
    try:
        plugin_dir = Path(plugin_path)
        
        if not plugin_dir.exists():
            click.echo(f"❌ Plugin directory not found: {plugin_path}")
            sys.exit(1)
            
        manifest_file = plugin_dir / "plugin.json"
        if not manifest_file.exists():
            click.echo(f"❌ Plugin manifest not found: {manifest_file}")
            sys.exit(1)
            
        # Read plugin manifest
        with open(manifest_file) as f:
            manifest = json.load(f)
            
        plugin_name = manifest.get("name", "unknown")
        plugin_version = manifest.get("version", "1.0.0")
        
        # Install to plugins directory
        plugins_dir = Path.home() / ".pistudio" / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)
        
        target_dir = plugins_dir / plugin_dir.name
        
        if target_dir.exists():
            click.echo(f"⚠️  Plugin '{plugin_name}' already installed. Overwrite? [y/N]", nl=False)
            if not click.confirm(""):
                click.echo("Installation cancelled")
                return
            shutil.rmtree(target_dir)
            
        shutil.copytree(plugin_dir, target_dir)
        
        click.echo(f"✅ Plugin '{plugin_name}' v{plugin_version} installed successfully!")
        click.echo(f"📁 Installed to: {target_dir}")
        
    except Exception as e:
        click.echo(f"❌ Error installing plugin: {e}", err=True)
        sys.exit(1)


@plugin.command()
def list():
    """List installed plugins"""
    try:
        plugins_dir = Path.home() / ".pistudio" / "plugins"
        
        if not plugins_dir.exists():
            click.echo("No plugins installed")
            return
            
        plugins = []
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir():
                manifest_file = plugin_dir / "plugin.json"
                if manifest_file.exists():
                    with open(manifest_file) as f:
                        manifest = json.load(f)
                    plugins.append({
                        "name": manifest.get("name", plugin_dir.name),
                        "version": manifest.get("version", "unknown"),
                        "type": manifest.get("type", "unknown"),
                        "description": manifest.get("description", ""),
                        "path": plugin_dir
                    })
                    
        if not plugins:
            click.echo("No plugins installed")
            return
            
        click.echo("📦 Installed Plugins:")
        click.echo("=" * 50)
        
        for plugin in plugins:
            click.echo(f"🔌 {plugin['name']} v{plugin['version']}")
            click.echo(f"   Type: {plugin['type']}")
            click.echo(f"   Description: {plugin['description']}")
            click.echo(f"   Path: {plugin['path']}")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Error listing plugins: {e}", err=True)
        sys.exit(1)


@plugin.command()
@click.argument('plugin_name')
def remove(plugin_name: str):
    """Remove an installed plugin"""
    try:
        plugins_dir = Path.home() / ".pistudio" / "plugins"
        
        # Find plugin by name
        plugin_dir = None
        for dir_path in plugins_dir.iterdir():
            if dir_path.is_dir():
                manifest_file = dir_path / "plugin.json"
                if manifest_file.exists():
                    with open(manifest_file) as f:
                        manifest = json.load(f)
                    if manifest.get("name") == plugin_name:
                        plugin_dir = dir_path
                        break
                        
        if not plugin_dir:
            click.echo(f"❌ Plugin '{plugin_name}' not found")
            sys.exit(1)
            
        click.echo(f"⚠️  Remove plugin '{plugin_name}'? [y/N]", nl=False)
        if click.confirm(""):
            shutil.rmtree(plugin_dir)
            click.echo(f"✅ Plugin '{plugin_name}' removed successfully")
        else:
            click.echo("Removal cancelled")
            
    except Exception as e:
        click.echo(f"❌ Error removing plugin: {e}", err=True)
        sys.exit(1)


@main.group()
def cloud():
    """IoT cloud integration commands"""
    pass


@cloud.command()
@click.option('--platform', type=click.Choice(['azure', 'aws', 'google']),
              required=True, help='Cloud platform')
@click.option('--device-id', required=True, help='Device identifier')
@click.option('--connection-string', help='Connection string (Azure)')
@click.option('--endpoint', help='IoT endpoint (AWS)')
@click.option('--project-id', help='Project ID (Google Cloud)')
def connect(platform: str, device_id: str, connection_string: Optional[str],
           endpoint: Optional[str], project_id: Optional[str]):
    """Connect to IoT cloud platform"""
    try:
        from iot_integration.cloud_connectors import (
            AzureIoTConnector, AWSIoTConnector, GoogleCloudIoTConnector
        )
        
        if platform == 'azure':
            if not connection_string:
                click.echo("❌ Azure requires --connection-string")
                sys.exit(1)
            connector = AzureIoTConnector(device_id, connection_string)
            
        elif platform == 'aws':
            if not endpoint:
                click.echo("❌ AWS requires --endpoint")
                sys.exit(1)
            connector = AWSIoTConnector(device_id, endpoint)
            
        elif platform == 'google':
            if not project_id:
                click.echo("❌ Google Cloud requires --project-id")
                sys.exit(1)
            connector = GoogleCloudIoTConnector(device_id, project_id, "us-central1", "my-registry")
            
        # Test connection
        click.echo(f"🔗 Connecting to {platform.title()} IoT...")
        
        if connector.connect():
            click.echo(f"✅ Connected to {platform.title()} IoT successfully!")
            
            # Send test telemetry
            test_data = {
                "temperature": 25.5,
                "humidity": 60.0,
                "timestamp": time.time()
            }
            
            if connector.send_telemetry(test_data):
                click.echo("📊 Test telemetry sent successfully")
            
            connector.disconnect()
        else:
            click.echo(f"❌ Failed to connect to {platform.title()} IoT")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error connecting to cloud: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--enable', help='Enable interface (i2c, spi, uart, camera, ssh)')
@click.option('--disable', help='Disable interface')
@click.option('--list', 'list_interfaces', is_flag=True, help='List interface status')
def interface(enable: Optional[str], disable: Optional[str], list_interfaces: bool):
    """Manage hardware interfaces (like raspi-config)"""
    try:
        from runner.os_emulation import PiOSEmulator
        
        project = Project.load_current()
        emulator = PiOSEmulator(project.path)
        
        if list_interfaces:
            click.echo("🔧 Hardware Interface Status:")
            click.echo("=" * 30)
            
            interfaces = {
                "I2C": "Enabled",
                "SPI": "Enabled", 
                "UART": "Enabled",
                "Camera": "Disabled",
                "SSH": "Enabled"
            }
            
            for interface, status in interfaces.items():
                status_icon = "✅" if status == "Enabled" else "❌"
                click.echo(f"{status_icon} {interface}: {status}")
                
        elif enable:
            if emulator.enable_interface(enable):
                click.echo(f"✅ {enable.upper()} interface enabled")
            else:
                click.echo(f"❌ Failed to enable {enable.upper()} interface")
                
        elif disable:
            click.echo(f"⚠️  Disabling {disable.upper()} interface not implemented")
            
        else:
            click.echo("Use --enable, --disable, or --list")
            
    except Exception as e:
        click.echo(f"❌ Error managing interfaces: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()