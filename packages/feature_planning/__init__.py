"""
Structured Feature Planning System for Kiro

A comprehensive framework for transforming feature ideas into production-ready
implementations through systematic workflow using EARS methodology and INCOSE standards.
"""

from .config import FeaturePlanningConfig, get_config, set_config
from .design_generator import DesignGenerator
from .ears_engine import EARSEngine
from .requirements_validator import RequirementsValidator
from .spec_manager import SpecManager
from .task_planner import TaskPlanner
from .workflow_controller import WorkflowController
from .task_executor import TaskExecutor
from .task_validator import TaskValidator
from .task_progression_controller import TaskProgressionController
from .kiro_integration import (
    KiroIntegrationManager,
    KiroFileSystemAdapter,
    KiroUserInputAdapter,
    KiroTaskStatusAdapter,
    get_kiro_integration,
    initialize_kiro_integration,
)
from .system_config import (
    SystemConfiguration,
    SystemInitializer,
    FeaturePlanningSystem,
    get_system,
    initialize_system,
    is_system_initialized,
    get_system_configuration,
)
from .error_handling import (
    ErrorHandler,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    ErrorRecord,
    get_error_handler,
    handle_error,
    get_user_friendly_error,
    get_error_summary,
    with_error_handling,
)

__all__ = [
    "EARSEngine",
    "SpecManager",
    "RequirementsValidator",
    "DesignGenerator",
    "TaskPlanner",
    "WorkflowController",
    "TaskExecutor",
    "TaskValidator",
    "TaskProgressionController",
    "FeaturePlanningConfig",
    "get_config",
    "set_config",
    "KiroIntegrationManager",
    "KiroFileSystemAdapter",
    "KiroUserInputAdapter",
    "KiroTaskStatusAdapter",
    "get_kiro_integration",
    "initialize_kiro_integration",
    "SystemConfiguration",
    "SystemInitializer",
    "FeaturePlanningSystem",
    "get_system",
    "initialize_system",
    "is_system_initialized",
    "get_system_configuration",
    "ErrorHandler",
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorContext",
    "ErrorRecord",
    "get_error_handler",
    "handle_error",
    "get_user_friendly_error",
    "get_error_summary",
    "with_error_handling",
]

__version__ = "1.0.0"
