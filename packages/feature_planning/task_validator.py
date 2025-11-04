"""
Task Validator for implementation validation and feedback.

This module provides validation and feedback systems for task execution,
ensuring implementations meet requirements and quality standards.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseValidator, TaskStatus, ValidationResult, WorkflowError
from .config import get_config


class TaskValidator(BaseValidator):
    """
    Validates task implementations against requirements and provides feedback.

    Ensures task completions meet specified requirements and quality standards
    with comprehensive feedback and suggestion systems.
    """

    def __init__(self, feature_name: str):
        """Initialize Task Validator for specific feature."""
        self.config = get_config()
        self.feature_name = feature_name
        self.validation_history: List[Dict[str, Any]] = []
        self.validation_state_file = Path(
            f".kiro/specs/{feature_name}/validation_state.json"
        )

    def validate(self, content: str) -> ValidationResult:
        """
        Validate task implementation content.

        Args:
            content: Implementation content to validate

        Returns:
            Validation result with issues and suggestions
        """
        try:
            issues = []
            suggestions = []

            # Basic content validation
            if not content or not content.strip():
                issues.append("No implementation content provided")
                suggestions.append("Provide implementation code or documentation")
                return ValidationResult(False, issues, suggestions)

            # Validate content structure
            structure_issues, structure_suggestions = self._validate_content_structure(content)
            issues.extend(structure_issues)
            suggestions.extend(structure_suggestions)

            # Validate code quality (if content appears to be code)
            if self._is_code_content(content):
                quality_issues, quality_suggestions = self._validate_code_quality(content)
                issues.extend(quality_issues)
                suggestions.extend(quality_suggestions)

            return ValidationResult(len(issues) == 0, issues, suggestions)

        except Exception as e:
            return ValidationResult(False, [f"Validation failed: {e}"], 
                                  ["Check implementation and try again"])

    def get_suggestions(self, content: str) -> List[str]:
        """
        Get improvement suggestions for implementation content.

        Args:
            content: Implementation content

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        try:
            # Analyze content for improvement opportunities
            if self._is_code_content(content):
                suggestions.extend(self._get_code_suggestions(content))
            
            suggestions.extend(self._get_general_suggestions(content))

            return suggestions

        except Exception:
            return ["Review implementation for potential improvements"]

    def validate_task_implementation(self, task_id: str, implementation: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete task implementation against requirements.

        Args:
            task_id: ID of task being validated
            implementation: Implementation details including code, tests, documentation

        Returns:
            Comprehensive validation result
        """
        try:
            issues = []
            suggestions = []

            # Load task context for validation
            task_context = self._load_task_context(task_id)
            if not task_context:
                issues.append(f"Task context not found for task: {task_id}")
                suggestions.append("Ensure task exists in implementation plan")
                return ValidationResult(False, issues, suggestions)

            # Validate against task requirements
            req_issues, req_suggestions = self._validate_against_requirements(
                task_context, implementation
            )
            issues.extend(req_issues)
            suggestions.extend(req_suggestions)

            # Validate implementation completeness
            completeness_issues, completeness_suggestions = self._validate_completeness(
                task_context, implementation
            )
            issues.extend(completeness_issues)
            suggestions.extend(completeness_suggestions)

            # Validate integration aspects
            integration_issues, integration_suggestions = self._validate_integration(
                task_context, implementation
            )
            issues.extend(integration_issues)
            suggestions.extend(integration_suggestions)

            # Record validation
            self._record_validation(task_id, implementation, issues, suggestions)

            return ValidationResult(len(issues) == 0, issues, suggestions)

        except Exception as e:
            return ValidationResult(False, [f"Task validation failed: {e}"], 
                                  ["Review task implementation and context"])

    def check_completion_status(self, task_id: str, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check task completion status and provide detailed feedback.

        Args:
            task_id: ID of task to check
            implementation: Implementation details

        Returns:
            Completion status with detailed feedback
        """
        try:
            # Validate implementation
            validation_result = self.validate_task_implementation(task_id, implementation)
            
            # Determine completion status
            if validation_result.is_valid:
                status = TaskStatus.COMPLETED
                completion_percentage = 100
            else:
                # Calculate partial completion based on issues
                total_checks = len(validation_result.issues) + len(validation_result.suggestions)
                if total_checks == 0:
                    completion_percentage = 50  # Some progress but unclear
                else:
                    # More issues = lower completion percentage
                    completion_percentage = max(10, 100 - (len(validation_result.issues) * 20))
                
                status = TaskStatus.IN_PROGRESS

            # Build completion report
            completion_report = {
                "task_id": task_id,
                "status": status.value,
                "completion_percentage": completion_percentage,
                "is_valid": validation_result.is_valid,
                "issues": validation_result.issues,
                "suggestions": validation_result.suggestions,
                "next_steps": self._get_next_steps(validation_result),
                "validation_timestamp": datetime.now().isoformat(),
            }

            return completion_report

        except Exception as e:
            return {
                "task_id": task_id,
                "status": TaskStatus.BLOCKED.value,
                "completion_percentage": 0,
                "is_valid": False,
                "issues": [f"Completion check failed: {e}"],
                "suggestions": ["Review task implementation and try again"],
                "next_steps": ["Fix implementation issues"],
                "validation_timestamp": datetime.now().isoformat(),
            }

    def track_task_status(self, task_id: str, status: TaskStatus, notes: str = "") -> bool:
        """
        Track task status changes with history.

        Args:
            task_id: ID of task
            status: New task status
            notes: Optional notes about status change

        Returns:
            True if tracking successful
        """
        try:
            # Load current tracking state
            tracking_state = self._load_tracking_state()
            
            # Update task status
            if "task_statuses" not in tracking_state:
                tracking_state["task_statuses"] = {}
            
            # Record status change
            status_entry = {
                "status": status.value,
                "timestamp": datetime.now().isoformat(),
                "notes": notes,
            }
            
            if task_id not in tracking_state["task_statuses"]:
                tracking_state["task_statuses"][task_id] = []
            
            tracking_state["task_statuses"][task_id].append(status_entry)
            
            # Save tracking state
            self._save_tracking_state(tracking_state)
            
            return True

        except Exception as e:
            print(f"Error tracking task status: {e}")
            return False

    def provide_feedback(self, task_id: str, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide comprehensive feedback on task implementation.

        Args:
            task_id: ID of task
            implementation: Implementation details

        Returns:
            Detailed feedback with actionable recommendations
        """
        try:
            # Get validation results
            validation_result = self.validate_task_implementation(task_id, implementation)
            
            # Get completion status
            completion_status = self.check_completion_status(task_id, implementation)
            
            # Build comprehensive feedback
            feedback = {
                "task_id": task_id,
                "overall_assessment": self._get_overall_assessment(validation_result),
                "strengths": self._identify_strengths(implementation),
                "areas_for_improvement": validation_result.issues,
                "specific_suggestions": validation_result.suggestions,
                "completion_status": completion_status,
                "recommended_actions": self._get_recommended_actions(validation_result),
                "quality_score": self._calculate_quality_score(validation_result),
                "feedback_timestamp": datetime.now().isoformat(),
            }
            
            return feedback

        except Exception as e:
            return {
                "task_id": task_id,
                "overall_assessment": "Unable to assess implementation",
                "error": str(e),
                "feedback_timestamp": datetime.now().isoformat(),
            }

    def _validate_content_structure(self, content: str) -> Tuple[List[str], List[str]]:
        """Validate basic content structure."""
        issues = []
        suggestions = []

        # Check minimum content length
        if len(content.strip()) < 10:
            issues.append("Implementation content is too brief")
            suggestions.append("Provide more detailed implementation")

        # Check for basic structure elements
        if self._is_code_content(content):
            if not re.search(r'def |class |function |import |from ', content):
                issues.append("Code content lacks basic structure elements")
                suggestions.append("Include proper function/class definitions")

        return issues, suggestions

    def _validate_code_quality(self, content: str) -> Tuple[List[str], List[str]]:
        """Validate code quality aspects."""
        issues = []
        suggestions = []

        # Check for basic Python syntax patterns
        if content.strip().endswith('.py') or 'def ' in content or 'class ' in content:
            # Check indentation consistency
            lines = content.split('\n')
            indentation_levels = []
            for line in lines:
                if line.strip():
                    leading_spaces = len(line) - len(line.lstrip())
                    indentation_levels.append(leading_spaces)
            
            if indentation_levels and max(indentation_levels) > 0:
                # Check for consistent indentation (multiples of 4)
                inconsistent_indents = [level for level in indentation_levels if level % 4 != 0 and level > 0]
                if inconsistent_indents:
                    issues.append("Inconsistent indentation detected")
                    suggestions.append("Use consistent 4-space indentation")

            # Check for docstrings in functions/classes
            if 'def ' in content and '"""' not in content and "'''" not in content:
                suggestions.append("Consider adding docstrings to functions and classes")

        return issues, suggestions

    def _is_code_content(self, content: str) -> bool:
        """Check if content appears to be code."""
        code_indicators = [
            'def ', 'class ', 'import ', 'from ', 'if __name__',
            'function ', 'const ', 'let ', 'var ', 'public class',
            '#include', 'using namespace', 'package '
        ]
        
        return any(indicator in content for indicator in code_indicators)

    def _get_code_suggestions(self, content: str) -> List[str]:
        """Get code-specific improvement suggestions."""
        suggestions = []

        # Check for common improvements
        if 'print(' in content:
            suggestions.append("Consider using logging instead of print statements for production code")

        if 'TODO' in content or 'FIXME' in content:
            suggestions.append("Address TODO and FIXME comments before completion")

        if len(content.split('\n')) > 100:
            suggestions.append("Consider breaking large files into smaller, focused modules")

        return suggestions

    def _get_general_suggestions(self, content: str) -> List[str]:
        """Get general improvement suggestions."""
        suggestions = []

        # Check documentation
        if len(content) > 200 and 'README' not in content and '# ' not in content:
            suggestions.append("Consider adding documentation or comments")

        # Check for error handling
        if 'try:' not in content and 'except' not in content and len(content) > 100:
            suggestions.append("Consider adding error handling for robustness")

        return suggestions

    def _load_task_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task context from execution framework."""
        try:
            # This would integrate with TaskExecutor to get task context
            # For now, return basic context structure
            return {
                "task_id": task_id,
                "requirements": [{"id": "1.1", "acceptance_criteria": ["Test criteria"]}],
                "scope": {"deliverables": ["Implementation"]},
                "validation_criteria": {},
            }
        except Exception:
            return None

    def _validate_against_requirements(self, task_context: Dict[str, Any], 
                                     implementation: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate implementation against task requirements."""
        issues = []
        suggestions = []

        # Check if implementation addresses task requirements
        requirements = task_context.get("requirements", [])
        if requirements and not implementation.get("addresses_requirements"):
            issues.append("Implementation does not clearly address task requirements")
            suggestions.append("Ensure implementation satisfies all specified requirements")

        return issues, suggestions

    def _validate_completeness(self, task_context: Dict[str, Any], 
                             implementation: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate implementation completeness."""
        issues = []
        suggestions = []

        # Check for required deliverables
        scope = task_context.get("scope", {})
        deliverables = scope.get("deliverables", [])
        
        provided_deliverables = implementation.get("deliverables", [])
        missing_deliverables = [d for d in deliverables if d not in provided_deliverables]
        
        if missing_deliverables:
            issues.append(f"Missing deliverables: {', '.join(missing_deliverables)}")
            suggestions.append("Provide all required deliverables for task completion")

        return issues, suggestions

    def _validate_integration(self, task_context: Dict[str, Any], 
                            implementation: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Validate integration aspects."""
        issues = []
        suggestions = []

        # Check integration considerations
        if not implementation.get("integration_tested"):
            suggestions.append("Test integration with existing codebase")

        if not implementation.get("follows_patterns"):
            suggestions.append("Ensure implementation follows established code patterns")

        return issues, suggestions

    def _record_validation(self, task_id: str, implementation: Dict[str, Any], 
                          issues: List[str], suggestions: List[str]) -> None:
        """Record validation results for history tracking."""
        try:
            validation_record = {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "issues_count": len(issues),
                "suggestions_count": len(suggestions),
                "is_valid": len(issues) == 0,
                "implementation_summary": str(implementation.get("summary", ""))[:200],
            }
            
            self.validation_history.append(validation_record)
            
            # Save to file
            self._save_validation_history()
            
        except Exception:
            pass  # Fail silently for history recording

    def _get_next_steps(self, validation_result: ValidationResult) -> List[str]:
        """Get recommended next steps based on validation results."""
        if validation_result.is_valid:
            return ["Task is complete and ready for review"]
        
        next_steps = []
        
        if validation_result.issues:
            next_steps.append("Address identified issues")
        
        if validation_result.suggestions:
            next_steps.append("Consider implementing suggested improvements")
        
        next_steps.append("Re-validate implementation after changes")
        
        return next_steps

    def _get_overall_assessment(self, validation_result: ValidationResult) -> str:
        """Get overall assessment of implementation quality."""
        if validation_result.is_valid:
            return "Implementation meets requirements and quality standards"
        
        issue_count = len(validation_result.issues)
        suggestion_count = len(validation_result.suggestions)
        
        if issue_count == 0 and suggestion_count > 0:
            return "Implementation is functional but has room for improvement"
        elif issue_count <= 2:
            return "Implementation has minor issues that should be addressed"
        else:
            return "Implementation has significant issues that must be resolved"

    def _identify_strengths(self, implementation: Dict[str, Any]) -> List[str]:
        """Identify strengths in the implementation."""
        strengths = []
        
        # Check for positive indicators
        if implementation.get("has_tests"):
            strengths.append("Includes test coverage")
        
        if implementation.get("has_documentation"):
            strengths.append("Well documented")
        
        if implementation.get("follows_standards"):
            strengths.append("Follows coding standards")
        
        if not strengths:
            strengths.append("Implementation addresses the core task requirements")
        
        return strengths

    def _get_recommended_actions(self, validation_result: ValidationResult) -> List[str]:
        """Get specific recommended actions."""
        actions = []
        
        # Prioritize critical issues
        critical_issues = [issue for issue in validation_result.issues if 'must' in issue.lower() or 'critical' in issue.lower()]
        if critical_issues:
            actions.append("Address critical issues immediately")
        
        # Add general actions
        if validation_result.issues:
            actions.append("Fix identified issues")
        
        if validation_result.suggestions:
            actions.append("Consider implementing suggestions for better quality")
        
        actions.append("Test implementation thoroughly")
        actions.append("Request code review if needed")
        
        return actions

    def _calculate_quality_score(self, validation_result: ValidationResult) -> int:
        """Calculate quality score (0-100) based on validation results."""
        if validation_result.is_valid:
            base_score = 90
        else:
            # Deduct points for issues
            issue_penalty = len(validation_result.issues) * 15
            base_score = max(10, 70 - issue_penalty)
        
        # Add points for having suggestions (shows thoroughness)
        if validation_result.suggestions:
            base_score = min(100, base_score + 5)
        
        return base_score

    def _load_tracking_state(self) -> Dict[str, Any]:
        """Load task tracking state from file."""
        try:
            tracking_file = Path(f".kiro/specs/{self.feature_name}/tracking_state.json")
            if tracking_file.exists():
                with open(tracking_file, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _save_tracking_state(self, state: Dict[str, Any]) -> None:
        """Save task tracking state to file."""
        try:
            tracking_file = Path(f".kiro/specs/{self.feature_name}/tracking_state.json")
            tracking_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(tracking_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass  # Fail silently for tracking

    def _save_validation_history(self) -> None:
        """Save validation history to file."""
        try:
            history_file = Path(f".kiro/specs/{self.feature_name}/validation_history.json")
            history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(history_file, "w") as f:
                json.dump(self.validation_history, f, indent=2)
        except Exception:
            pass  # Fail silently for history