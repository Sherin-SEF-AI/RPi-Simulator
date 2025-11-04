"""
System Configuration and Initialization Module

This module provides system-wide configuration management and initialization
procedures for the Feature Planning System.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from .base import ConfigurationError


@dataclass
class SystemConfiguration:
    """System configuration settings"""
    
    # Directory settings
    specs_directory: str = ".kiro/specs"
    templates_directory: str = ".kiro/templates/feature_planning"
    backup_directory: str = ".kiro/backups"
    
    # EARS Engine settings
    ears_strict_mode: bool = True
    ears_auto_format: bool = True
    
    # INCOSE validation settings
    incose_strict_mode: bool = True
    incose_auto_suggestions: bool = True
    
    # Workflow settings
    auto_backup: bool = True
    max_backups_per_document: int = 10
    require_explicit_approval: bool = True
    
    # Task execution settings
    auto_task_progression: bool = False
    max_task_execution_attempts: int = 2
    
    # Integration settings
    use_kiro_tools: bool = True
    kiro_file_operations: bool = True
    kiro_user_input: bool = True
    kiro_task_status: bool = True
    
    # Logging and debugging
    debug_mode: bool = False
    log_level: str = "INFO"
    log_file: Optional[str] = None


class SystemInitializer:
    """Handles system initialization and setup procedures"""
    
    def __init__(self, config: Optional[SystemConfiguration] = None):
        self.config = config or SystemConfiguration()
        self.config_file = Path(".kiro/settings/feature_planning.json")
    
    def initialize_system(self) -> bool:
        """Initialize the complete feature planning system"""
        try:
            # Create necessary directories
            self._create_directories()
            
            # Initialize configuration
            self._initialize_configuration()
            
            # Create default templates
            self._create_default_templates()
            
            # Validate system setup
            self._validate_system_setup()
            
            return True
        except Exception as e:
            print(f"System initialization failed: {e}")
            return False
    
    def _create_directories(self) -> None:
        """Create necessary directory structure"""
        directories = [
            self.config.specs_directory,
            self.config.templates_directory,
            self.config.backup_directory,
            ".kiro/settings",
            ".kiro/logs"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _initialize_configuration(self) -> None:
        """Initialize system configuration file"""
        # Create config file if it doesn't exist
        if not self.config_file.exists():
            self.save_configuration(self.config)
        else:
            # Load existing configuration and merge with defaults
            existing_config = self.load_configuration()
            if existing_config:
                # Update with any new default settings
                config_dict = asdict(self.config)
                existing_dict = asdict(existing_config)
                
                # Add any new settings that don't exist
                for key, value in config_dict.items():
                    if key not in existing_dict:
                        existing_dict[key] = value
                
                # Save updated configuration
                updated_config = SystemConfiguration(**existing_dict)
                self.save_configuration(updated_config)
                self.config = updated_config
    
    def _create_default_templates(self) -> None:
        """Create default document templates"""
        templates_dir = Path(self.config.templates_directory)
        
        # Requirements template
        requirements_template = """# Requirements Document

## Introduction

This specification defines [brief description of the feature/system].

## Glossary

- **System_Name**: [Definition of the main system]
- **Component_Name**: [Definition of key components]

## Requirements

### Requirement 1

**User Story:** As a [role], I want [feature], so that [benefit]

#### Acceptance Criteria

1. WHEN [trigger event], THE System_Name SHALL [system response]
2. WHILE [ongoing condition], THE System_Name SHALL [continuous behavior]
3. IF [undesired condition], THEN THE System_Name SHALL [corrective action]
4. WHERE [optional feature is enabled], THE System_Name SHALL [optional behavior]
5. THE System_Name SHALL [ubiquitous requirement]

### Requirement 2

**User Story:** As a [role], I want [feature], so that [benefit]

#### Acceptance Criteria

1. [Additional EARS-compliant requirements...]
"""

        # Design template
        design_template = """# Design Document

## Overview

[High-level description of the system architecture and purpose]

## Architecture

```mermaid
graph TB
    A[Main Component] --> B[Sub Component 1]
    A --> C[Sub Component 2]
    B --> D[Interface Layer]
    C --> D
```

## Components and Interfaces

### Main Component
- **Purpose**: [Component purpose]
- **Responsibilities**: [Key responsibilities]
- **Interfaces**: [External interfaces]

### Sub Components
[Detailed component specifications]

## Data Models

### Entity Model
```python
@dataclass
class EntityModel:
    id: str
    name: str
    properties: Dict[str, Any]
```

## Error Handling

### Error Categories
- **Validation Errors**: [How validation errors are handled]
- **System Errors**: [How system errors are handled]
- **User Errors**: [How user errors are handled]

### Recovery Strategies
[Error recovery and fallback mechanisms]

## Testing Strategy

### Unit Testing
- [Unit testing approach]

### Integration Testing
- [Integration testing approach]

### Validation Testing
- [Validation testing approach]
"""

        # Tasks template
        tasks_template = """# Implementation Plan

- [ ] 1. Set up core infrastructure
  - Create base classes and interfaces
  - Implement configuration management
  - Set up error handling framework
  - _Requirements: 1.1, 1.2_

- [ ] 2. Implement core functionality
- [ ] 2.1 Build main component
  - Implement core logic and algorithms
  - Create data processing pipeline
  - _Requirements: 1.3, 2.1_

- [ ] 2.2 Add validation and error handling
  - Implement input validation
  - Add comprehensive error handling
  - _Requirements: 1.4, 2.2_

- [ ]* 2.3 Write unit tests
  - Create test cases for core functionality
  - Add edge case testing
  - _Requirements: 1.3, 2.1_

- [ ] 3. Integration and finalization
- [ ] 3.1 Integrate components
  - Connect all system components
  - Implement interface contracts
  - _Requirements: 2.3, 2.4_

- [ ] 3.2 Final validation and testing
  - Run integration tests
  - Validate against all requirements
  - _Requirements: All requirements_
"""

        # Write template files
        templates = {
            "requirements_template.md": requirements_template,
            "design_template.md": design_template,
            "tasks_template.md": tasks_template
        }
        
        for filename, content in templates.items():
            template_file = templates_dir / filename
            if not template_file.exists():
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def _validate_system_setup(self) -> None:
        """Validate that system is properly set up"""
        # Check directories exist
        required_dirs = [
            self.config.specs_directory,
            self.config.templates_directory,
            ".kiro/settings"
        ]
        
        for directory in required_dirs:
            if not Path(directory).exists():
                raise ConfigurationError(f"Required directory not found: {directory}")
        
        # Check configuration file exists
        if not self.config_file.exists():
            raise ConfigurationError("Configuration file not found")
        
        # Check templates exist
        templates_dir = Path(self.config.templates_directory)
        required_templates = [
            "requirements_template.md",
            "design_template.md", 
            "tasks_template.md"
        ]
        
        for template in required_templates:
            if not (templates_dir / template).exists():
                raise ConfigurationError(f"Required template not found: {template}")
    
    def save_configuration(self, config: SystemConfiguration) -> bool:
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2)
            
            return True
        except Exception as e:
            print(f"Failed to save configuration: {e}")
            return False
    
    def load_configuration(self) -> Optional[SystemConfiguration]:
        """Load configuration from file"""
        try:
            if not self.config_file.exists():
                return None
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return SystemConfiguration(**config_data)
        except Exception as e:
            print(f"Failed to load configuration: {e}")
            return None
    
    def reset_configuration(self) -> bool:
        """Reset configuration to defaults"""
        try:
            default_config = SystemConfiguration()
            return self.save_configuration(default_config)
        except Exception as e:
            print(f"Failed to reset configuration: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and health check"""
        status = {
            "initialized": False,
            "configuration_valid": False,
            "directories_exist": False,
            "templates_exist": False,
            "errors": []
        }
        
        try:
            # Check if system is initialized
            if self.config_file.exists():
                status["initialized"] = True
            else:
                status["errors"].append("System not initialized - configuration file missing")
            
            # Check configuration validity
            config = self.load_configuration()
            if config:
                status["configuration_valid"] = True
            else:
                status["errors"].append("Configuration file invalid or corrupted")
            
            # Check directories
            required_dirs = [
                self.config.specs_directory,
                self.config.templates_directory,
                ".kiro/settings"
            ]
            
            missing_dirs = []
            for directory in required_dirs:
                if not Path(directory).exists():
                    missing_dirs.append(directory)
            
            if not missing_dirs:
                status["directories_exist"] = True
            else:
                status["errors"].append(f"Missing directories: {', '.join(missing_dirs)}")
            
            # Check templates
            templates_dir = Path(self.config.templates_directory)
            required_templates = [
                "requirements_template.md",
                "design_template.md",
                "tasks_template.md"
            ]
            
            missing_templates = []
            for template in required_templates:
                if not (templates_dir / template).exists():
                    missing_templates.append(template)
            
            if not missing_templates:
                status["templates_exist"] = True
            else:
                status["errors"].append(f"Missing templates: {', '.join(missing_templates)}")
            
            # Overall health
            status["healthy"] = (
                status["initialized"] and 
                status["configuration_valid"] and 
                status["directories_exist"] and 
                status["templates_exist"]
            )
            
        except Exception as e:
            status["errors"].append(f"System status check failed: {e}")
        
        return status


class FeaturePlanningSystem:
    """Main system class that coordinates all components"""
    
    def __init__(self, config: Optional[SystemConfiguration] = None):
        self.initializer = SystemInitializer(config)
        self.config = self.initializer.config
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the complete system"""
        if self.initializer.initialize_system():
            self._initialized = True
            return True
        return False
    
    def is_initialized(self) -> bool:
        """Check if system is initialized"""
        return self._initialized
    
    def get_configuration(self) -> SystemConfiguration:
        """Get current system configuration"""
        return self.config
    
    def update_configuration(self, **kwargs) -> bool:
        """Update system configuration"""
        try:
            config_dict = asdict(self.config)
            config_dict.update(kwargs)
            
            new_config = SystemConfiguration(**config_dict)
            if self.initializer.save_configuration(new_config):
                self.config = new_config
                return True
            return False
        except Exception:
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        status = self.initializer.get_system_status()
        
        return {
            "version": "1.0.0",
            "initialized": self._initialized,
            "configuration": asdict(self.config),
            "status": status,
            "directories": {
                "specs": self.config.specs_directory,
                "templates": self.config.templates_directory,
                "backups": self.config.backup_directory
            }
        }


# Global system instance
_system_instance = None


def get_system() -> FeaturePlanningSystem:
    """Get the global system instance"""
    global _system_instance
    if _system_instance is None:
        _system_instance = FeaturePlanningSystem()
    return _system_instance


def initialize_system(config: Optional[SystemConfiguration] = None) -> bool:
    """Initialize the global system instance"""
    system = get_system()
    if config:
        system.config = config
        system.initializer.config = config
    return system.initialize()


def is_system_initialized() -> bool:
    """Check if the global system is initialized"""
    return get_system().is_initialized()


def get_system_configuration() -> SystemConfiguration:
    """Get the current system configuration"""
    return get_system().get_configuration()