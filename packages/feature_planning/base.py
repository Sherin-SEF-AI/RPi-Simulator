"""
Base interfaces and abstract classes for the Feature Planning System.

This module defines the core abstractions that all components must implement
to ensure consistent behavior and enable dependency injection.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path


class EARSPattern(Enum):
    """EARS requirement patterns."""
    UBIQUITOUS = "ubiquitous"
    EVENT_DRIVEN = "event_driven"
    STATE_DRIVEN = "state_driven"
    UNWANTED_EVENT = "unwanted_event"
    OPTIONAL_FEATURE = "optional_feature"
    COMPLEX = "complex"


class ValidationStatus(Enum):
    """Validation status for requirements and documents."""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"
    WARNING = "warning"


class WorkflowPhase(Enum):
    """Workflow phases in the feature planning process."""
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    TASKS = "tasks"
    EXECUTION = "execution"


class TaskStatus(Enum):
    """Task execution status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class ValidationResult:
    """Result of validation operations."""
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    pattern: Optional[EARSPattern] = None


@dataclass
class QualityIssue:
    """INCOSE quality rule violation."""
    rule: str
    description: str
    suggestion: str
    severity: str  # "error", "warning", "info"


@dataclass
class Requirement:
    """Structured requirement with EARS compliance."""
    id: str
    user_story: str
    acceptance_criteria: List[str]
    ears_pattern: Optional[EARSPattern]
    referenced_terms: List[str]
    validation_status: ValidationStatus


@dataclass
class Task:
    """Implementation task with dependencies and traceability."""
    id: str
    title: str
    description: str
    requirements_refs: List[str]
    dependencies: List[str]
    is_optional: bool
    status: TaskStatus
    sub_tasks: List['Task']


class BaseValidator(ABC):
    """Abstract base class for all validation components."""
    
    @abstractmethod
    def validate(self, content: str) -> ValidationResult:
        """Validate content and return results."""
        pass
    
    @abstractmethod
    def get_suggestions(self, content: str) -> List[str]:
        """Get improvement suggestions for content."""
        pass


class BaseGenerator(ABC):
    """Abstract base class for document generators."""
    
    @abstractmethod
    def generate(self, input_data: Any) -> str:
        """Generate document content from input data."""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data before generation."""
        pass


class BaseManager(ABC):
    """Abstract base class for document and workflow managers."""
    
    @abstractmethod
    def create(self, name: str, **kwargs) -> bool:
        """Create new managed entity."""
        pass
    
    @abstractmethod
    def load(self, name: str) -> Optional[Any]:
        """Load existing managed entity."""
        pass
    
    @abstractmethod
    def update(self, name: str, content: Any) -> bool:
        """Update managed entity."""
        pass
    
    @abstractmethod
    def delete(self, name: str) -> bool:
        """Delete managed entity."""
        pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class WorkflowError(Exception):
    """Raised when workflow operations fail."""
    pass