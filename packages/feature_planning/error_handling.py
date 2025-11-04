"""
Comprehensive Error Handling and Recovery Module

This module provides centralized error handling, recovery strategies,
and user-friendly error messages for the Feature Planning System.
"""

import logging
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict

from .base import ValidationResult, WorkflowError, ValidationError, ConfigurationError


class FeaturePlanningError(Exception):
    """Base exception for feature planning system errors"""
    pass


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    VALIDATION = "validation"
    WORKFLOW = "workflow"
    FILE_SYSTEM = "file_system"
    CONFIGURATION = "configuration"
    INTEGRATION = "integration"
    USER_INPUT = "user_input"
    SYSTEM = "system"


@dataclass
class ErrorContext:
    """Context information for errors"""
    component: str
    operation: str
    feature_name: Optional[str] = None
    document_type: Optional[str] = None
    phase: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorRecord:
    """Complete error record with context and recovery info"""
    error_id: str
    timestamp: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    technical_details: str
    context: ErrorContext
    recovery_suggestions: List[str]
    auto_recovery_attempted: bool = False
    auto_recovery_successful: bool = False
    user_action_required: bool = True


class RecoveryStrategy:
    """Base class for recovery strategies"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def can_recover(self, error: ErrorRecord) -> bool:
        """Check if this strategy can handle the error"""
        raise NotImplementedError
    
    def attempt_recovery(self, error: ErrorRecord) -> bool:
        """Attempt to recover from the error"""
        raise NotImplementedError


class FileSystemRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for file system errors"""
    
    def __init__(self):
        super().__init__(
            "file_system_recovery",
            "Handles file system operation failures"
        )
    
    def can_recover(self, error: ErrorRecord) -> bool:
        return error.category == ErrorCategory.FILE_SYSTEM
    
    def attempt_recovery(self, error: ErrorRecord) -> bool:
        """Attempt to recover from file system errors"""
        try:
            context = error.context
            
            # Try to create missing directories
            if "directory" in error.message.lower() or "not found" in error.message.lower():
                if context.feature_name:
                    spec_dir = Path(f".kiro/specs/{context.feature_name}")
                    spec_dir.mkdir(parents=True, exist_ok=True)
                    return True
            
            # Try to restore from backup
            if "corrupted" in error.message.lower() or "invalid" in error.message.lower():
                return self._restore_from_backup(context)
            
            return False
        except Exception:
            return False
    
    def _restore_from_backup(self, context: ErrorContext) -> bool:
        """Attempt to restore from backup"""
        try:
            if not context.feature_name or not context.document_type:
                return False
            
            from .spec_manager import SpecManager
            spec_manager = SpecManager()
            
            # Get backup history
            backups = spec_manager.get_backup_history(
                context.feature_name, 
                context.document_type
            )
            
            if backups:
                # Restore from most recent backup
                latest_backup = backups[0]
                return spec_manager.restore_from_backup(
                    context.feature_name,
                    context.document_type,
                    latest_backup['filename']
                )
            
            return False
        except Exception:
            return False


class ValidationRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for validation errors"""
    
    def __init__(self):
        super().__init__(
            "validation_recovery",
            "Handles validation and compliance errors"
        )
    
    def can_recover(self, error: ErrorRecord) -> bool:
        return error.category == ErrorCategory.VALIDATION
    
    def attempt_recovery(self, error: ErrorRecord) -> bool:
        """Attempt to recover from validation errors"""
        try:
            # For validation errors, we typically can't auto-recover
            # but we can provide better suggestions
            context = error.context
            
            if "ears" in error.message.lower():
                error.recovery_suggestions.extend([
                    "Review EARS pattern requirements",
                    "Use pattern: WHEN [trigger], THE [system] SHALL [response]",
                    "Ensure only one EARS pattern per requirement"
                ])
            
            if "incose" in error.message.lower():
                error.recovery_suggestions.extend([
                    "Use active voice in requirements",
                    "Avoid vague terms like 'quickly' or 'adequate'",
                    "Make requirements measurable and specific"
                ])
            
            # Can't actually fix validation errors automatically
            return False
        except Exception:
            return False


class WorkflowRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for workflow errors"""
    
    def __init__(self):
        super().__init__(
            "workflow_recovery",
            "Handles workflow state and transition errors"
        )
    
    def can_recover(self, error: ErrorRecord) -> bool:
        return error.category == ErrorCategory.WORKFLOW
    
    def attempt_recovery(self, error: ErrorRecord) -> bool:
        """Attempt to recover from workflow errors"""
        try:
            context = error.context
            
            # Try to reset workflow state
            if "state" in error.message.lower() and context.feature_name:
                return self._reset_workflow_state(context.feature_name)
            
            # Try to restore previous phase
            if "transition" in error.message.lower() and context.feature_name:
                return self._restore_previous_phase(context.feature_name)
            
            return False
        except Exception:
            return False
    
    def _reset_workflow_state(self, feature_name: str) -> bool:
        """Reset workflow state to requirements phase"""
        try:
            from .workflow_controller import WorkflowController
            
            workflow = WorkflowController(feature_name)
            workflow.current_phase = workflow.WorkflowPhase.REQUIREMENTS
            workflow.approval_status = {}
            workflow.phase_history = []
            workflow._save_workflow_state()
            
            return True
        except Exception:
            return False
    
    def _restore_previous_phase(self, feature_name: str) -> bool:
        """Restore to previous workflow phase"""
        try:
            from .workflow_controller import WorkflowController
            
            workflow = WorkflowController(feature_name)
            if workflow.phase_history:
                workflow.current_phase = workflow.phase_history[-1]
                workflow.phase_history = workflow.phase_history[:-1]
                workflow._save_workflow_state()
                return True
            
            return False
        except Exception:
            return False


class ConfigurationRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for configuration errors"""
    
    def __init__(self):
        super().__init__(
            "configuration_recovery",
            "Handles configuration and system setup errors"
        )
    
    def can_recover(self, error: ErrorRecord) -> bool:
        return error.category == ErrorCategory.CONFIGURATION
    
    def attempt_recovery(self, error: ErrorRecord) -> bool:
        """Attempt to recover from configuration errors"""
        try:
            # Try to reinitialize system
            if "not initialized" in error.message.lower():
                from .system_config import initialize_system
                return initialize_system()
            
            # Try to reset configuration
            if "configuration" in error.message.lower():
                from .system_config import SystemInitializer
                initializer = SystemInitializer()
                return initializer.reset_configuration()
            
            return False
        except Exception:
            return False


class ErrorHandler:
    """Central error handler with recovery capabilities"""
    
    def __init__(self):
        self.recovery_strategies: List[RecoveryStrategy] = [
            FileSystemRecoveryStrategy(),
            ValidationRecoveryStrategy(),
            WorkflowRecoveryStrategy(),
            ConfigurationRecoveryStrategy(),
        ]
        self.error_log: List[ErrorRecord] = []
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup error logging"""
        logger = logging.getLogger("feature_planning.errors")
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(".kiro/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_dir / "feature_planning_errors.log")
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        auto_recover: bool = True
    ) -> ErrorRecord:
        """Handle an error with context and recovery attempts"""
        
        # Create error record
        error_record = ErrorRecord(
            error_id=self._generate_error_id(),
            timestamp=datetime.now().isoformat(),
            category=category,
            severity=severity,
            message=str(error),
            technical_details=traceback.format_exc(),
            context=context,
            recovery_suggestions=self._get_base_suggestions(category, error),
            auto_recovery_attempted=False,
            auto_recovery_successful=False,
            user_action_required=True
        )
        
        # Log the error
        self.logger.error(
            f"Error in {context.component}.{context.operation}: {error}",
            extra={'error_record': asdict(error_record)}
        )
        
        # Attempt automatic recovery if enabled
        if auto_recover:
            error_record.auto_recovery_attempted = True
            error_record.auto_recovery_successful = self._attempt_recovery(error_record)
            
            if error_record.auto_recovery_successful:
                error_record.user_action_required = False
                self.logger.info(f"Auto-recovery successful for error {error_record.error_id}")
        
        # Add to error log
        self.error_log.append(error_record)
        
        return error_record
    
    def _attempt_recovery(self, error_record: ErrorRecord) -> bool:
        """Attempt recovery using available strategies"""
        for strategy in self.recovery_strategies:
            if strategy.can_recover(error_record):
                try:
                    if strategy.attempt_recovery(error_record):
                        self.logger.info(
                            f"Recovery successful using strategy: {strategy.name}"
                        )
                        return True
                except Exception as e:
                    self.logger.warning(
                        f"Recovery strategy {strategy.name} failed: {e}"
                    )
        
        return False
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"FP_ERR_{timestamp}"
    
    def _get_base_suggestions(self, category: ErrorCategory, error: Exception) -> List[str]:
        """Get base recovery suggestions based on error category"""
        suggestions = []
        
        if category == ErrorCategory.VALIDATION:
            suggestions.extend([
                "Review the input data for compliance with requirements",
                "Check documentation for proper format and syntax",
                "Validate against EARS patterns and INCOSE rules"
            ])
        
        elif category == ErrorCategory.WORKFLOW:
            suggestions.extend([
                "Check current workflow phase and required approvals",
                "Ensure all previous phases are properly completed",
                "Review workflow state and transition rules"
            ])
        
        elif category == ErrorCategory.FILE_SYSTEM:
            suggestions.extend([
                "Check file and directory permissions",
                "Ensure sufficient disk space is available",
                "Verify file paths and directory structure"
            ])
        
        elif category == ErrorCategory.CONFIGURATION:
            suggestions.extend([
                "Run system initialization: feature-planning init",
                "Check configuration file validity",
                "Reset configuration to defaults if needed"
            ])
        
        elif category == ErrorCategory.INTEGRATION:
            suggestions.extend([
                "Check Kiro tool availability and permissions",
                "Verify integration configuration settings",
                "Test individual tool operations"
            ])
        
        return suggestions
    
    def get_user_friendly_message(self, error_record: ErrorRecord) -> str:
        """Generate user-friendly error message"""
        severity_emoji = {
            ErrorSeverity.LOW: "ℹ️",
            ErrorSeverity.MEDIUM: "⚠️",
            ErrorSeverity.HIGH: "❌",
            ErrorSeverity.CRITICAL: "🚨"
        }
        
        emoji = severity_emoji.get(error_record.severity, "❌")
        
        message = f"{emoji} {error_record.category.value.title()} Error\n"
        message += f"Operation: {error_record.context.operation}\n"
        message += f"Component: {error_record.context.component}\n"
        
        if error_record.context.feature_name:
            message += f"Feature: {error_record.context.feature_name}\n"
        
        message += f"\nProblem: {error_record.message}\n"
        
        if error_record.auto_recovery_successful:
            message += "\n✅ Automatic recovery was successful. You can continue.\n"
        elif error_record.auto_recovery_attempted:
            message += "\n❌ Automatic recovery failed. Manual intervention required.\n"
        
        if error_record.recovery_suggestions:
            message += "\nSuggested Actions:\n"
            for i, suggestion in enumerate(error_record.recovery_suggestions, 1):
                message += f"  {i}. {suggestion}\n"
        
        return message
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors"""
        if not self.error_log:
            return {"total_errors": 0, "by_category": {}, "by_severity": {}}
        
        by_category = {}
        by_severity = {}
        
        for error in self.error_log:
            # Count by category
            cat = error.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
            
            # Count by severity
            sev = error.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return {
            "total_errors": len(self.error_log),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": [
                {
                    "id": err.error_id,
                    "timestamp": err.timestamp,
                    "category": err.category.value,
                    "severity": err.severity.value,
                    "message": err.message,
                    "auto_recovered": err.auto_recovery_successful
                }
                for err in self.error_log[-10:]  # Last 10 errors
            ]
        }
    
    def clear_error_log(self) -> None:
        """Clear the error log"""
        self.error_log.clear()
        self.logger.info("Error log cleared")


# Global error handler instance
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(
    error: Exception,
    component: str,
    operation: str,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    feature_name: Optional[str] = None,
    document_type: Optional[str] = None,
    phase: Optional[str] = None,
    auto_recover: bool = True
) -> ErrorRecord:
    """Convenience function to handle errors"""
    context = ErrorContext(
        component=component,
        operation=operation,
        feature_name=feature_name,
        document_type=document_type,
        phase=phase
    )
    
    return get_error_handler().handle_error(
        error, context, category, severity, auto_recover
    )


def get_user_friendly_error(error_record: ErrorRecord) -> str:
    """Get user-friendly error message"""
    return get_error_handler().get_user_friendly_message(error_record)


def get_error_summary() -> Dict[str, Any]:
    """Get error summary"""
    return get_error_handler().get_error_summary()


# Decorator for automatic error handling
def with_error_handling(
    component: str,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    auto_recover: bool = True
):
    """Decorator to automatically handle errors in functions"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_record = handle_error(
                    e,
                    component=component,
                    operation=func.__name__,
                    category=category,
                    severity=severity,
                    auto_recover=auto_recover
                )
                
                # Re-raise if not auto-recovered
                if not error_record.auto_recovery_successful:
                    raise FeaturePlanningError(
                        get_user_friendly_error(error_record)
                    ) from e
                
                # Return None or appropriate default for successful recovery
                return None
        
        return wrapper
    return decorator