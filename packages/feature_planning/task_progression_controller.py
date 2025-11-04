"""
Task Progression Controller for user review and manual progression control.

This module manages task completion review mechanisms and ensures manual
progression control without automatic task advancement.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseManager, TaskStatus, ValidationResult, WorkflowError
from .config import get_config
from .task_validator import TaskValidator


class TaskProgressionController(BaseManager):
    """
    Controls task progression with user review and manual advancement.

    Ensures tasks are properly reviewed before progression and prevents
    automatic advancement to maintain user control over the workflow.
    """

    def __init__(self, feature_name: str):
        """Initialize Task Progression Controller for specific feature."""
        self.config = get_config()
        self.feature_name = feature_name
        self.task_validator = TaskValidator(feature_name)
        self.progression_state_file = Path(
            f".kiro/specs/{feature_name}/progression_state.json"
        )
        self.review_history: List[Dict[str, Any]] = []

    def create(self, name: str, **kwargs) -> bool:
        """
        Create new task progression control context.

        Args:
            name: Feature name
            **kwargs: Additional progression parameters

        Returns:
            True if creation successful
        """
        try:
            self.feature_name = name
            self.progression_state_file = Path(f".kiro/specs/{name}/progression_state.json")
            
            # Initialize progression state
            progression_state = {
                "feature_name": name,
                "current_task_id": None,
                "completed_tasks": [],
                "pending_reviews": [],
                "auto_progression_disabled": True,  # Always disabled for manual control
                "created_at": datetime.now().isoformat(),
            }
            
            self._save_progression_state(progression_state)
            return True
        except Exception as e:
            print(f"Error creating progression control: {e}")
            return False

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load existing progression control state.

        Args:
            name: Feature name

        Returns:
            Progression state data or None if not found
        """
        try:
            self.feature_name = name
            self.progression_state_file = Path(f".kiro/specs/{name}/progression_state.json")
            
            if self.progression_state_file.exists():
                with open(self.progression_state_file, "r") as f:
                    return json.load(f)
            return None
        except Exception:
            return None

    def update(self, name: str, content: Any) -> bool:
        """
        Update progression control state.

        Args:
            name: Feature name
            content: New progression state

        Returns:
            True if update successful
        """
        try:
            if isinstance(content, dict):
                self._save_progression_state(content)
                return True
            return False
        except Exception:
            return False

    def delete(self, name: str) -> bool:
        """
        Delete progression control state.

        Args:
            name: Feature name

        Returns:
            True if deletion successful
        """
        try:
            progression_file = Path(f".kiro/specs/{name}/progression_state.json")
            if progression_file.exists():
                progression_file.unlink()
            return True
        except Exception:
            return False

    def request_task_review(self, task_id: str, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request user review for completed task.

        Args:
            task_id: ID of task to review
            implementation: Implementation details for review

        Returns:
            Review request with status and feedback
        """
        try:
            # Validate task implementation
            validation_result = self.task_validator.validate_task_implementation(task_id, implementation)
            
            # Get comprehensive feedback
            feedback = self.task_validator.provide_feedback(task_id, implementation)
            
            # Create review request
            review_request = {
                "task_id": task_id,
                "request_timestamp": datetime.now().isoformat(),
                "validation_result": {
                    "is_valid": validation_result.is_valid,
                    "issues": validation_result.issues,
                    "suggestions": validation_result.suggestions,
                },
                "feedback": feedback,
                "implementation_summary": self._create_implementation_summary(implementation),
                "review_status": "pending",
                "requires_user_approval": True,
            }
            
            # Add to pending reviews
            progression_state = self.load(self.feature_name) or {}
            if "pending_reviews" not in progression_state:
                progression_state["pending_reviews"] = []
            
            progression_state["pending_reviews"].append(review_request)
            self.update(self.feature_name, progression_state)
            
            # Record in review history
            self.review_history.append(review_request)
            
            return review_request

        except Exception as e:
            return {
                "task_id": task_id,
                "error": str(e),
                "review_status": "failed",
                "request_timestamp": datetime.now().isoformat(),
            }

    def process_user_review(self, task_id: str, review_decision: str, user_feedback: str = "") -> Dict[str, Any]:
        """
        Process user review decision for task completion.

        Args:
            task_id: ID of task being reviewed
            review_decision: User decision ("approved", "rejected", "needs_revision")
            user_feedback: Optional user feedback

        Returns:
            Review processing result
        """
        try:
            progression_state = self.load(self.feature_name) or {}
            
            # Find pending review
            pending_reviews = progression_state.get("pending_reviews", [])
            review_index = None
            target_review = None
            
            for i, review in enumerate(pending_reviews):
                if review.get("task_id") == task_id:
                    review_index = i
                    target_review = review
                    break
            
            if not target_review:
                return {
                    "success": False,
                    "error": f"No pending review found for task: {task_id}",
                }
            
            # Process review decision
            review_result = self._process_review_decision(
                target_review, review_decision, user_feedback
            )
            
            # Update progression state based on decision
            if review_decision.lower() == "approved":
                # Mark task as completed
                completed_tasks = progression_state.get("completed_tasks", [])
                if task_id not in completed_tasks:
                    completed_tasks.append(task_id)
                    progression_state["completed_tasks"] = completed_tasks
                
                # Update task status
                self.task_validator.track_task_status(
                    task_id, TaskStatus.COMPLETED, "Approved by user review"
                )
                
                # Remove from pending reviews
                pending_reviews.pop(review_index)
                
            elif review_decision.lower() == "rejected":
                # Mark task as needing rework
                self.task_validator.track_task_status(
                    task_id, TaskStatus.IN_PROGRESS, f"Rejected: {user_feedback}"
                )
                
                # Remove from pending reviews
                pending_reviews.pop(review_index)
                
            elif review_decision.lower() == "needs_revision":
                # Keep in pending but mark for revision
                target_review["review_status"] = "needs_revision"
                target_review["revision_feedback"] = user_feedback
                target_review["revision_requested_at"] = datetime.now().isoformat()
                
                # Update task status
                self.task_validator.track_task_status(
                    task_id, TaskStatus.IN_PROGRESS, f"Needs revision: {user_feedback}"
                )
            
            # Update progression state
            progression_state["pending_reviews"] = pending_reviews
            progression_state["last_review_processed"] = datetime.now().isoformat()
            self.update(self.feature_name, progression_state)
            
            return review_result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process review: {e}",
                "task_id": task_id,
            }

    def get_progression_status(self) -> Dict[str, Any]:
        """
        Get current progression status and next steps.

        Returns:
            Comprehensive progression status report
        """
        try:
            progression_state = self.load(self.feature_name) or {}
            
            # Get task statistics
            completed_tasks = progression_state.get("completed_tasks", [])
            pending_reviews = progression_state.get("pending_reviews", [])
            current_task = progression_state.get("current_task_id")
            
            # Calculate progress metrics
            total_tasks = self._get_total_task_count()
            completion_percentage = (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
            
            # Determine next steps
            next_steps = self._determine_next_steps(progression_state)
            
            # Build status report
            status_report = {
                "feature_name": self.feature_name,
                "current_task_id": current_task,
                "completed_tasks_count": len(completed_tasks),
                "total_tasks_count": total_tasks,
                "completion_percentage": round(completion_percentage, 1),
                "pending_reviews_count": len(pending_reviews),
                "pending_reviews": pending_reviews,
                "next_steps": next_steps,
                "auto_progression_enabled": False,  # Always disabled
                "last_activity": progression_state.get("last_review_processed"),
                "status_timestamp": datetime.now().isoformat(),
            }
            
            return status_report

        except Exception as e:
            return {
                "feature_name": self.feature_name,
                "error": f"Failed to get progression status: {e}",
                "status_timestamp": datetime.now().isoformat(),
            }

    def prevent_auto_progression(self) -> bool:
        """
        Ensure automatic task progression is disabled.

        Returns:
            True if auto-progression is successfully disabled
        """
        try:
            progression_state = self.load(self.feature_name) or {}
            progression_state["auto_progression_disabled"] = True
            progression_state["auto_progression_policy"] = "manual_only"
            progression_state["policy_updated_at"] = datetime.now().isoformat()
            
            self.update(self.feature_name, progression_state)
            return True
        except Exception:
            return False

    def get_next_task_recommendation(self) -> Optional[Dict[str, Any]]:
        """
        Get recommendation for next task to work on (without auto-starting).

        Returns:
            Next task recommendation or None if no tasks available
        """
        try:
            progression_state = self.load(self.feature_name) or {}
            completed_tasks = progression_state.get("completed_tasks", [])
            
            # Get all tasks from specification
            all_tasks = self._load_all_tasks()
            
            # Find next uncompleted task
            for task in all_tasks:
                task_id = task.get("id")
                if task_id not in completed_tasks:
                    # Check dependencies
                    dependencies = task.get("dependencies", [])
                    dependencies_met = all(dep in completed_tasks for dep in dependencies)
                    
                    if dependencies_met:
                        return {
                            "recommended_task": task,
                            "reason": "Next task with satisfied dependencies",
                            "dependencies_status": "satisfied",
                            "is_optional": task.get("is_optional", False),
                        }
            
            # No tasks with satisfied dependencies found
            return None

        except Exception as e:
            return {
                "error": f"Failed to get task recommendation: {e}",
            }

    def create_task_report(self, task_id: str) -> Dict[str, Any]:
        """
        Create comprehensive task completion report.

        Args:
            task_id: ID of task to report on

        Returns:
            Detailed task report
        """
        try:
            # Get task status history
            tracking_state = self.task_validator._load_tracking_state()
            task_history = tracking_state.get("task_statuses", {}).get(task_id, [])
            
            # Get validation history
            validation_history = [
                record for record in self.task_validator.validation_history
                if record.get("task_id") == task_id
            ]
            
            # Get review history
            review_history = [
                review for review in self.review_history
                if review.get("task_id") == task_id
            ]
            
            # Build comprehensive report
            report = {
                "task_id": task_id,
                "status_history": task_history,
                "validation_history": validation_history,
                "review_history": review_history,
                "current_status": self._get_current_task_status(task_id),
                "time_spent": self._calculate_time_spent(task_history),
                "validation_attempts": len(validation_history),
                "review_cycles": len(review_history),
                "report_generated_at": datetime.now().isoformat(),
            }
            
            return report

        except Exception as e:
            return {
                "task_id": task_id,
                "error": f"Failed to create task report: {e}",
                "report_generated_at": datetime.now().isoformat(),
            }

    def _process_review_decision(self, review: Dict[str, Any], decision: str, 
                               feedback: str) -> Dict[str, Any]:
        """Process user review decision and create result."""
        result = {
            "task_id": review.get("task_id"),
            "decision": decision,
            "user_feedback": feedback,
            "processed_at": datetime.now().isoformat(),
            "success": True,
        }
        
        if decision.lower() == "approved":
            result["message"] = "Task approved and marked as completed"
            result["next_action"] = "Task is complete, ready for next task"
            
        elif decision.lower() == "rejected":
            result["message"] = "Task rejected, requires rework"
            result["next_action"] = "Rework task implementation based on feedback"
            
        elif decision.lower() == "needs_revision":
            result["message"] = "Task needs revision based on feedback"
            result["next_action"] = "Address feedback and resubmit for review"
            
        else:
            result["success"] = False
            result["error"] = f"Invalid review decision: {decision}"
        
        return result

    def _create_implementation_summary(self, implementation: Dict[str, Any]) -> str:
        """Create summary of implementation for review."""
        summary_parts = []
        
        if implementation.get("code_files"):
            summary_parts.append(f"Code files: {len(implementation['code_files'])}")
        
        if implementation.get("tests_included"):
            summary_parts.append("Includes tests")
        
        if implementation.get("documentation"):
            summary_parts.append("Includes documentation")
        
        if implementation.get("description"):
            summary_parts.append(f"Description: {implementation['description'][:100]}...")
        
        return "; ".join(summary_parts) if summary_parts else "Implementation provided"

    def _determine_next_steps(self, progression_state: Dict[str, Any]) -> List[str]:
        """Determine recommended next steps based on current state."""
        next_steps = []
        
        pending_reviews = progression_state.get("pending_reviews", [])
        if pending_reviews:
            next_steps.append(f"Review {len(pending_reviews)} pending task(s)")
        
        # Check for next available task
        next_task = self.get_next_task_recommendation()
        if next_task and not next_task.get("error"):
            task_title = next_task["recommended_task"].get("title", "Unknown task")
            next_steps.append(f"Consider working on: {task_title}")
        
        if not next_steps:
            next_steps.append("All tasks completed or no tasks available")
        
        return next_steps

    def _get_total_task_count(self) -> int:
        """Get total number of tasks in the implementation plan."""
        try:
            all_tasks = self._load_all_tasks()
            return len(all_tasks)
        except Exception:
            return 0

    def _load_all_tasks(self) -> List[Dict[str, Any]]:
        """Load all tasks from the specification."""
        try:
            # This would integrate with TaskExecutor to load tasks
            # For now, return sample tasks for testing
            return [
                {"id": "1", "title": "Task 1", "dependencies": [], "is_optional": False},
                {"id": "2.1", "title": "Task 2.1", "dependencies": ["1"], "is_optional": False},
                {"id": "2.2", "title": "Task 2.2", "dependencies": ["1"], "is_optional": True},
            ]
        except Exception:
            return []

    def _get_current_task_status(self, task_id: str) -> str:
        """Get current status of specific task."""
        try:
            tracking_state = self.task_validator._load_tracking_state()
            task_history = tracking_state.get("task_statuses", {}).get(task_id, [])
            
            if task_history:
                return task_history[-1].get("status", "unknown")
            return "not_started"
        except Exception:
            return "unknown"

    def _calculate_time_spent(self, task_history: List[Dict[str, Any]]) -> str:
        """Calculate time spent on task based on status history."""
        try:
            if len(task_history) < 2:
                return "Unknown"
            
            start_time = datetime.fromisoformat(task_history[0]["timestamp"])
            end_time = datetime.fromisoformat(task_history[-1]["timestamp"])
            
            duration = end_time - start_time
            
            if duration.days > 0:
                return f"{duration.days} days, {duration.seconds // 3600} hours"
            elif duration.seconds > 3600:
                return f"{duration.seconds // 3600} hours, {(duration.seconds % 3600) // 60} minutes"
            else:
                return f"{duration.seconds // 60} minutes"
                
        except Exception:
            return "Unknown"

    def _save_progression_state(self, state: Dict[str, Any]) -> None:
        """Save progression state to file."""
        try:
            # Ensure directory exists
            self.progression_state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.progression_state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            raise WorkflowError(f"Failed to save progression state: {e}")