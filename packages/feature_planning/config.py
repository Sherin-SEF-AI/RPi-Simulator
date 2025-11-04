"""
Configuration management for EARS patterns and INCOSE rules.

This module provides centralized configuration for validation rules,
patterns, and system behavior.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Pattern, Optional
import re
from pathlib import Path
import json
from .base import ConfigurationError


@dataclass
class EARSPatternConfig:
    """Configuration for EARS pattern recognition."""
    name: str
    pattern: str
    description: str
    examples: List[str] = field(default_factory=list)
    compiled_pattern: Pattern = field(init=False)
    
    def __post_init__(self):
        """Compile regex pattern after initialization."""
        self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE)


@dataclass
class INCOSERuleConfig:
    """Configuration for INCOSE quality rules."""
    name: str
    description: str
    check_function: str  # Name of the checking function
    severity: str  # "error", "warning", "info"
    suggestion_template: str
    examples: List[str] = field(default_factory=list)


class FeaturePlanningConfig:
    """Central configuration for the Feature Planning System."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration with default or custom settings."""
        self.config_path = config_path
        self._ears_patterns: Dict[str, EARSPatternConfig] = {}
        self._incose_rules: Dict[str, INCOSERuleConfig] = {}
        self._system_settings: Dict[str, any] = {}
        
        self._load_default_config()
        if config_path and config_path.exists():
            self._load_custom_config(config_path)
    
    def _load_default_config(self):
        """Load default EARS patterns and INCOSE rules."""
        # EARS Patterns
        self._ears_patterns = {
            "ubiquitous": EARSPatternConfig(
                name="Ubiquitous",
                pattern=r"^THE\s+(\w+)\s+SHALL\s+(.+)$",
                description="System behavior that is always active",
                examples=[
                    "THE System SHALL validate user input",
                    "THE Database SHALL maintain data integrity"
                ]
            ),
            "event_driven": EARSPatternConfig(
                name="Event-driven",
                pattern=r"^WHEN\s+(.+),\s+THE\s+(\w+)\s+SHALL\s+(.+)$",
                description="System response to specific events",
                examples=[
                    "WHEN user clicks submit, THE System SHALL validate the form",
                    "WHEN timeout occurs, THE Connection SHALL retry automatically"
                ]
            ),
            "state_driven": EARSPatternConfig(
                name="State-driven",
                pattern=r"^WHILE\s+(.+),\s+THE\s+(\w+)\s+SHALL\s+(.+)$",
                description="System behavior during specific states",
                examples=[
                    "WHILE system is offline, THE Cache SHALL store pending requests",
                    "WHILE user is authenticated, THE System SHALL allow access"
                ]
            ),
            "unwanted_event": EARSPatternConfig(
                name="Unwanted event",
                pattern=r"^IF\s+(.+),\s+THEN\s+THE\s+(\w+)\s+SHALL\s+(.+)$",
                description="System response to unwanted conditions",
                examples=[
                    "IF connection fails, THEN THE System SHALL display error message",
                    "IF invalid data detected, THEN THE Validator SHALL reject input"
                ]
            ),
            "optional_feature": EARSPatternConfig(
                name="Optional feature",
                pattern=r"^WHERE\s+(.+),\s+THE\s+(\w+)\s+SHALL\s+(.+)$",
                description="System behavior for optional features",
                examples=[
                    "WHERE advanced mode is enabled, THE Interface SHALL show debug options",
                    "WHERE premium subscription active, THE System SHALL unlock features"
                ]
            ),
            "complex": EARSPatternConfig(
                name="Complex",
                pattern=r"^(?:WHERE\s+(.+?),?\s+)?(?:WHILE\s+(.+?),?\s+)?(?:(?:WHEN|IF)\s+(.+?),?\s+)?(?:THEN\s+)?THE\s+(\w+)\s+SHALL\s+(.+)$",
                description="Complex requirements with multiple conditions",
                examples=[
                    "WHERE debug mode enabled, WHILE system running, WHEN error occurs, THE Logger SHALL record detailed trace",
                    "WHILE user authenticated, IF session expires, THEN THE System SHALL redirect to login"
                ]
            )
        }
        
        # INCOSE Quality Rules
        self._incose_rules = {
            "active_voice": INCOSERuleConfig(
                name="Active Voice",
                description="Requirements must use active voice",
                check_function="check_active_voice",
                severity="error",
                suggestion_template="Use active voice: specify who performs the action",
                examples=["Good: The system SHALL validate input", "Bad: Input SHALL be validated"]
            ),
            "no_vague_terms": INCOSERuleConfig(
                name="No Vague Terms",
                description="Avoid vague or subjective terms",
                check_function="check_vague_terms",
                severity="warning",
                suggestion_template="Replace vague term '{term}' with specific, measurable criteria",
                examples=["Avoid: quickly, adequate, user-friendly", "Use: within 2 seconds, 99.9% accuracy"]
            ),
            "no_escape_clauses": INCOSERuleConfig(
                name="No Escape Clauses",
                description="Avoid escape clauses that weaken requirements",
                check_function="check_escape_clauses",
                severity="error",
                suggestion_template="Remove escape clause '{clause}' and specify exact conditions",
                examples=["Avoid: where possible, if feasible", "Use: specific conditions and constraints"]
            ),
            "no_negatives": INCOSERuleConfig(
                name="No Negative Statements",
                description="Avoid negative requirements (SHALL NOT)",
                check_function="check_negative_statements",
                severity="warning",
                suggestion_template="Rewrite as positive requirement specifying what the system SHALL do",
                examples=["Avoid: System SHALL NOT crash", "Use: System SHALL maintain 99.9% uptime"]
            ),
            "single_thought": INCOSERuleConfig(
                name="Single Thought",
                description="Each requirement should express one thought",
                check_function="check_single_thought",
                severity="error",
                suggestion_template="Split into separate requirements - detected multiple 'AND' clauses",
                examples=["Split: System SHALL validate AND store data", "Into: Two separate requirements"]
            ),
            "measurable": INCOSERuleConfig(
                name="Measurable Criteria",
                description="Requirements must be measurable and testable",
                check_function="check_measurability",
                severity="warning",
                suggestion_template="Add measurable criteria: specify quantities, timeframes, or success conditions",
                examples=["Vague: fast response", "Measurable: response within 200ms"]
            )
        }
        
        # System Settings
        self._system_settings = {
            "max_requirement_length": 500,
            "max_acceptance_criteria": 10,
            "require_glossary": True,
            "auto_backup": True,
            "validation_strictness": "standard",  # "strict", "standard", "lenient"
            "default_spec_directory": ".kiro/specs",
            "supported_languages": ["python", "markdown"],
            "task_hierarchy_levels": 2
        }
    
    def _load_custom_config(self, config_path: Path):
        """Load custom configuration from file."""
        try:
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
            
            # Update system settings
            if "system_settings" in custom_config:
                self._system_settings.update(custom_config["system_settings"])
            
            # Add custom EARS patterns
            if "custom_ears_patterns" in custom_config:
                for name, pattern_data in custom_config["custom_ears_patterns"].items():
                    self._ears_patterns[name] = EARSPatternConfig(**pattern_data)
            
            # Add custom INCOSE rules
            if "custom_incose_rules" in custom_config:
                for name, rule_data in custom_config["custom_incose_rules"].items():
                    self._incose_rules[name] = INCOSERuleConfig(**rule_data)
                    
        except Exception as e:
            raise ConfigurationError(f"Failed to load custom config: {e}")
    
    def get_ears_patterns(self) -> Dict[str, EARSPatternConfig]:
        """Get all EARS pattern configurations."""
        return self._ears_patterns.copy()
    
    def get_incose_rules(self) -> Dict[str, INCOSERuleConfig]:
        """Get all INCOSE rule configurations."""
        return self._incose_rules.copy()
    
    def get_setting(self, key: str, default=None):
        """Get system setting value."""
        return self._system_settings.get(key, default)
    
    def update_setting(self, key: str, value):
        """Update system setting."""
        self._system_settings[key] = value
    
    def save_config(self, output_path: Path):
        """Save current configuration to file."""
        config_data = {
            "system_settings": self._system_settings,
            "custom_ears_patterns": {
                name: {
                    "name": pattern.name,
                    "pattern": pattern.pattern,
                    "description": pattern.description,
                    "examples": pattern.examples
                }
                for name, pattern in self._ears_patterns.items()
            },
            "custom_incose_rules": {
                name: {
                    "name": rule.name,
                    "description": rule.description,
                    "check_function": rule.check_function,
                    "severity": rule.severity,
                    "suggestion_template": rule.suggestion_template,
                    "examples": rule.examples
                }
                for name, rule in self._incose_rules.items()
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2)


# Global configuration instance
_config_instance = None

def get_config() -> FeaturePlanningConfig:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = FeaturePlanningConfig()
    return _config_instance

def set_config(config: FeaturePlanningConfig):
    """Set the global configuration instance."""
    global _config_instance
    _config_instance = config