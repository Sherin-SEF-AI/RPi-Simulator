"""
Command Line Interface for Feature Planning System

Provides CLI commands for system initialization, configuration management,
and basic feature planning operations.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .system_config import (
    FeaturePlanningSystem,
    SystemConfiguration,
    initialize_system,
    get_system,
    is_system_initialized
)
from .kiro_integration import get_kiro_integration
from .base import FeaturePlanningError


def init_command(args: argparse.Namespace) -> int:
    """Initialize the feature planning system"""
    try:
        print("Initializing Feature Planning System...")
        
        # Create configuration from args if provided
        config = None
        if args.config_file:
            config_path = Path(args.config_file)
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                config = SystemConfiguration(**config_data)
                print(f"Using configuration from: {config_path}")
        
        # Initialize system
        if initialize_system(config):
            print("✓ System initialized successfully")
            
            # Show system status
            system = get_system()
            info = system.get_system_info()
            
            print(f"✓ Specs directory: {info['directories']['specs']}")
            print(f"✓ Templates directory: {info['directories']['templates']}")
            print(f"✓ Backups directory: {info['directories']['backups']}")
            
            return 0
        else:
            print("✗ System initialization failed")
            return 1
            
    except Exception as e:
        print(f"✗ Initialization error: {e}")
        return 1


def status_command(args: argparse.Namespace) -> int:
    """Show system status"""
    try:
        system = get_system()
        info = system.get_system_info()
        
        print("Feature Planning System Status")
        print("=" * 40)
        print(f"Version: {info['version']}")
        print(f"Initialized: {'✓' if info['initialized'] else '✗'}")
        
        status = info['status']
        print(f"Configuration Valid: {'✓' if status['configuration_valid'] else '✗'}")
        print(f"Directories Exist: {'✓' if status['directories_exist'] else '✗'}")
        print(f"Templates Exist: {'✓' if status['templates_exist'] else '✗'}")
        print(f"Overall Health: {'✓' if status['healthy'] else '✗'}")
        
        if status['errors']:
            print("\nErrors:")
            for error in status['errors']:
                print(f"  ✗ {error}")
        
        print("\nDirectories:")
        for name, path in info['directories'].items():
            exists = "✓" if Path(path).exists() else "✗"
            print(f"  {name}: {path} {exists}")
        
        if args.verbose:
            print("\nConfiguration:")
            config = info['configuration']
            for key, value in config.items():
                print(f"  {key}: {value}")
        
        return 0 if status['healthy'] else 1
        
    except Exception as e:
        print(f"✗ Status check error: {e}")
        return 1


def config_command(args: argparse.Namespace) -> int:
    """Manage system configuration"""
    try:
        system = get_system()
        
        if args.action == 'show':
            config = system.get_configuration()
            if args.format == 'json':
                print(json.dumps(config.__dict__, indent=2))
            else:
                print("Current Configuration:")
                print("=" * 30)
                for key, value in config.__dict__.items():
                    print(f"{key}: {value}")
        
        elif args.action == 'set':
            if not args.key or args.value is None:
                print("✗ Both --key and --value are required for 'set' action")
                return 1
            
            # Convert value to appropriate type
            value = args.value
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            
            if system.update_configuration(**{args.key: value}):
                print(f"✓ Configuration updated: {args.key} = {value}")
                return 0
            else:
                print(f"✗ Failed to update configuration: {args.key}")
                return 1
        
        elif args.action == 'reset':
            from .system_config import SystemInitializer
            initializer = SystemInitializer()
            if initializer.reset_configuration():
                print("✓ Configuration reset to defaults")
                return 0
            else:
                print("✗ Failed to reset configuration")
                return 1
        
        return 0
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return 1


def create_spec_command(args: argparse.Namespace) -> int:
    """Create a new feature specification"""
    try:
        if not is_system_initialized():
            print("✗ System not initialized. Run 'feature-planning init' first.")
            return 1
        
        feature_name = args.name
        feature_idea = args.idea or f"Feature specification for {feature_name}"
        
        print(f"Creating feature specification: {feature_name}")
        
        # Use Kiro integration if available
        kiro_integration = get_kiro_integration()
        result = kiro_integration.create_feature_spec(feature_name, feature_idea)
        
        if result.success:
            print(f"✓ Feature specification created successfully")
            print(f"  Feature: {feature_name}")
            print(f"  Directory: .kiro/specs/{feature_name}")
            print(f"  Current phase: {result.data.get('current_phase', 'requirements')}")
            return 0
        else:
            print(f"✗ Failed to create specification: {result.error}")
            return 1
            
    except Exception as e:
        print(f"✗ Specification creation error: {e}")
        return 1


def list_specs_command(args: argparse.Namespace) -> int:
    """List all feature specifications"""
    try:
        from .spec_manager import SpecManager
        
        spec_manager = SpecManager()
        specs = spec_manager.list_specifications()
        
        if not specs:
            print("No feature specifications found.")
            return 0
        
        print("Feature Specifications:")
        print("=" * 30)
        
        for spec_name in specs:
            spec_data = spec_manager.load(spec_name)
            if spec_data and 'metadata' in spec_data:
                metadata = spec_data['metadata']
                phase = metadata.get('current_phase', 'unknown')
                created = metadata.get('created_at', 'unknown')
                print(f"  {spec_name}")
                print(f"    Phase: {phase}")
                print(f"    Created: {created}")
            else:
                print(f"  {spec_name} (metadata unavailable)")
        
        return 0
        
    except Exception as e:
        print(f"✗ List specifications error: {e}")
        return 1


def execute_task_command(args: argparse.Namespace) -> int:
    """Execute a specific task"""
    try:
        if not is_system_initialized():
            print("✗ System not initialized. Run 'feature-planning init' first.")
            return 1
        
        feature_name = args.feature
        task_id = args.task
        
        print(f"Executing task: {task_id}")
        print(f"Feature: {feature_name}")
        
        # Use Kiro integration
        kiro_integration = get_kiro_integration()
        result = kiro_integration.execute_task(feature_name, task_id)
        
        if result.success:
            print(f"✓ Task executed successfully")
            print(f"  Status: {result.data.get('status', 'completed')}")
            return 0
        else:
            print(f"✗ Task execution failed: {result.error}")
            return 1
            
    except Exception as e:
        print(f"✗ Task execution error: {e}")
        return 1


def main() -> int:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Feature Planning System CLI",
        prog="feature-planning"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize the system')
    init_parser.add_argument(
        '--config-file', 
        help='Path to configuration file'
    )
    init_parser.set_defaults(func=init_command)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    status_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )
    status_parser.set_defaults(func=status_command)
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument(
        'action',
        choices=['show', 'set', 'reset'],
        help='Configuration action'
    )
    config_parser.add_argument(
        '--key',
        help='Configuration key (for set action)'
    )
    config_parser.add_argument(
        '--value',
        help='Configuration value (for set action)'
    )
    config_parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (for show action)'
    )
    config_parser.set_defaults(func=config_command)
    
    # Create spec command
    create_parser = subparsers.add_parser('create', help='Create new feature specification')
    create_parser.add_argument(
        'name',
        help='Feature name'
    )
    create_parser.add_argument(
        '--idea',
        help='Feature idea description'
    )
    create_parser.set_defaults(func=create_spec_command)
    
    # List specs command
    list_parser = subparsers.add_parser('list', help='List feature specifications')
    list_parser.set_defaults(func=list_specs_command)
    
    # Execute task command
    execute_parser = subparsers.add_parser('execute', help='Execute a task')
    execute_parser.add_argument(
        'feature',
        help='Feature name'
    )
    execute_parser.add_argument(
        'task',
        help='Task ID'
    )
    execute_parser.set_defaults(func=execute_task_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n✗ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())