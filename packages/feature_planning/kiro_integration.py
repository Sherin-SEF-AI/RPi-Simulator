"""
Kiro Infrastructure Integration Module

This module provides the integration layer between the Feature Planning System
and Kiro's infrastructure, including file system tools, user input mechanisms,
and task status management.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import WorkflowError
from .spec_manager import SpecManager
from .workflow_controller import WorkflowController


@dataclass
class KiroToolResult:
    """Result from a Kiro tool operation"""

    success: bool
    data: Any = None
    error: Optional[str] = None


class KiroFileSystemAdapter:
    """Adapter for Kiro's file system operations"""

    def __init__(self) -> None:
        self._file_operations: List[Dict[str, Any]] = []

    def write_file(self, path: str, content: str) -> KiroToolResult:
        """Write content to a file using Kiro's fsWrite tool"""
        try:
            # In actual Kiro environment, this would call the fsWrite tool
            # For now, we'll simulate the operation
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self._file_operations.append(
                {"operation": "write", "path": path, "success": True}
            )

            return KiroToolResult(success=True, data={"path": path})
        except Exception as e:
            return KiroToolResult(success=False, error=str(e))

    def read_file(self, path: str) -> KiroToolResult:
        """Read file content using Kiro's readFile tool"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            return KiroToolResult(success=True, data=content)
        except Exception as e:
            return KiroToolResult(success=False, error=str(e))

    def append_file(self, path: str, content: str) -> KiroToolResult:
        """Append content to a file using Kiro's fsAppend tool"""
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)

            self._file_operations.append(
                {"operation": "append", "path": path, "success": True}
            )

            return KiroToolResult(success=True, data={"path": path})
        except Exception as e:
            return KiroToolResult(success=False, error=str(e))

    def file_exists(self, path: str) -> bool:
        """Check if a file exists"""
        return Path(path).exists()

    def get_operations_log(self) -> List[Dict[str, Any]]:
        """Get log of file operations performed"""
        return self._file_operations.copy()


class KiroUserInputAdapter:
    """Adapter for Kiro's user input mechanisms"""

    def __init__(self) -> None:
        self._input_history: List[Dict[str, Any]] = []

    def request_approval(
        self, question: str, reason: str, options: Optional[List[str]] = None
    ) -> KiroToolResult:
        """Request user approval using Kiro's userInput tool"""
        try:
            # In actual Kiro environment, this would call the userInput tool
            # For now, we'll simulate the operation
            input_request = {
                "question": question,
                "reason": reason,
                "options": options,
                "timestamp": None,  # Would be set by actual Kiro tool
            }

            self._input_history.append(input_request)

            # Simulate user approval for testing
            return KiroToolResult(
                success=True, data={"approved": True, "response": "yes"}
            )
        except Exception as e:
            return KiroToolResult(success=False, error=str(e))

    def get_input_history(self) -> List[Dict[str, Any]]:
        """Get history of user input requests"""
        return self._input_history.copy()


class KiroTaskStatusAdapter:
    """Adapter for Kiro's task status management"""

    def __init__(self) -> None:
        self._status_updates: List[Dict[str, Any]] = []

    def update_task_status(
        self, task_file_path: str, task: str, status: str
    ) -> KiroToolResult:
        """Update task status using Kiro's taskStatus tool"""
        try:
            # In actual Kiro environment, this would call the taskStatus tool
            # For now, we'll simulate the operation
            status_update = {
                "task_file_path": task_file_path,
                "task": task,
                "status": status,
                "timestamp": None,  # Would be set by actual Kiro tool
            }

            self._status_updates.append(status_update)

            return KiroToolResult(success=True, data=status_update)
        except Exception as e:
            return KiroToolResult(success=False, error=str(e))

    def get_status_updates(self) -> List[Dict[str, Any]]:
        """Get history of task status updates"""
        return self._status_updates.copy()


class KiroIntegrationManager:
    """Main integration manager for Kiro infrastructure"""

    def __init__(self) -> None:
        self.file_system = KiroFileSystemAdapter()
        self.user_input = KiroUserInputAdapter()
        self.task_status = KiroTaskStatusAdapter()
        self._spec_manager: Optional[SpecManager] = None
        self._workflow_controller: Optional[WorkflowController] = None

    def initialize_spec_manager(self, feature_name: str) -> SpecManager:
        """Initialize spec manager with Kiro file system integration"""
        if not self._spec_manager:
            # SpecManager expects a Path, not a string
            base_path = Path(f".kiro/specs/{feature_name}")
            self._spec_manager = SpecManager(base_path)
            # Inject Kiro file system adapter
            self._spec_manager._file_adapter = self.file_system  # type: ignore
        return self._spec_manager

    def initialize_workflow_controller(self, feature_name: str) -> WorkflowController:
        """Initialize workflow controller with Kiro integration"""
        if not self._workflow_controller:
            # WorkflowController expects a feature_name string, not SpecManager
            self._workflow_controller = WorkflowController(feature_name)
            # Inject Kiro adapters
            self._workflow_controller._user_input_adapter = self.user_input  # type: ignore
            self._workflow_controller._task_status_adapter = self.task_status  # type: ignore
        return self._workflow_controller

    def create_feature_spec(
        self, feature_name: str, feature_idea: str
    ) -> KiroToolResult:
        """Create a new feature specification using Kiro infrastructure"""
        try:
            # Initialize components with Kiro integration
            spec_manager = self.initialize_spec_manager(feature_name)
            workflow_controller = self.initialize_workflow_controller(feature_name)

            # Create the spec and start the workflow
            spec_created = spec_manager.create(feature_name)
            workflow_created = workflow_controller.create(
                feature_name, feature_idea=feature_idea
            )

            return KiroToolResult(
                success=spec_created and workflow_created,
                data={
                    "feature_name": feature_name,
                    "workflow_started": workflow_created,
                    "current_phase": "requirements",
                },
            )
        except Exception as e:
            return KiroToolResult(success=False, error=str(e))

    def execute_task(self, feature_name: str, task_id: str) -> KiroToolResult:
        """Execute a specific task using Kiro infrastructure"""
        try:
            # Load existing spec
            spec_manager = self.initialize_spec_manager(feature_name)

            # Update task status to in_progress
            task_file_path = f".kiro/specs/{feature_name}/tasks.md"
            self.task_status.update_task_status(task_file_path, task_id, "in_progress")

            # Execute task (this would integrate with actual task execution logic)
            # For now, we'll simulate successful execution

            # Update task status to completed
            self.task_status.update_task_status(task_file_path, task_id, "completed")

            return KiroToolResult(
                success=True, data={"task_id": task_id, "status": "completed"}
            )
        except Exception as e:
            return KiroToolResult(success=False, error=str(e))

    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of Kiro integration components"""
        return {
            "file_system": {
                "operations_count": len(self.file_system.get_operations_log()),
                "last_operations": (
                    self.file_system.get_operations_log()[-5:]
                    if self.file_system.get_operations_log()
                    else []
                ),
            },
            "user_input": {
                "requests_count": len(self.user_input.get_input_history()),
                "last_requests": (
                    self.user_input.get_input_history()[-3:]
                    if self.user_input.get_input_history()
                    else []
                ),
            },
            "task_status": {
                "updates_count": len(self.task_status.get_status_updates()),
                "last_updates": (
                    self.task_status.get_status_updates()[-5:]
                    if self.task_status.get_status_updates()
                    else []
                ),
            },
        }


# Global integration manager instance
_integration_manager = None


def get_kiro_integration() -> KiroIntegrationManager:
    """Get the global Kiro integration manager instance"""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = KiroIntegrationManager()
    return _integration_manager


def initialize_kiro_integration() -> KiroIntegrationManager:
    """Initialize Kiro integration and return the manager"""
    return get_kiro_integration()
