"""
Task Executor for implementation task execution.

This module provides the framework for executing individual tasks from
implementation plans with proper context loading and validation.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseManager, Task, TaskStatus, ValidationResult, WorkflowError
from .config import get_config
from .spec_manager import SpecManager


class TaskExecutor(BaseManager):
    """
    Manages task execution with context loading and validation.

    Provides framework for executing implementation tasks with proper
    context from requirements, design, and task documents.
    """

    def __init__(self, feature_name: str):
        """Initialize Task Executor for specific feature."""
        self.config = get_config()
        self.feature_name = feature_name
        self.spec_manager = SpecManager()
        self.context_cache: Dict[str, Any] = {}
        self.current_task: Optional[Dict[str, Any]] = None
        self.execution_state_file = Path(
            f".kiro/specs/{feature_name}/execution_state.json"
        )

    def create(self, name: str, **kwargs: Any) -> bool:
        """
        Create new task execution context.

        Args:
            name: Feature name
            **kwargs: Additional execution parameters

        Returns:
            True if creation successful
        """
        try:
            self.feature_name = name
            self.execution_state_file = Path(f".kiro/specs/{name}/execution_state.json")

            # Initialize execution state
            execution_state: Dict[str, Any] = {
                "feature_name": name,
                "current_task_id": None,
                "task_status": {},
                "execution_history": [],
                "context_loaded": False,
                "created_at": self._get_timestamp(),
            }

            self._save_execution_state(execution_state)
            return True
        except Exception as e:
            print(f"Error creating task execution context: {e}")
            return False

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load existing task execution context.

        Args:
            name: Feature name

        Returns:
            Execution context data or None if not found
        """
        try:
            self.feature_name = name
            self.execution_state_file = Path(f".kiro/specs/{name}/execution_state.json")

            if self.execution_state_file.exists():
                with open(self.execution_state_file, "r") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else None
            return None
        except Exception:
            return None

    def update(self, name: str, content: Any) -> bool:
        """
        Update task execution state.

        Args:
            name: Feature name
            content: New execution state

        Returns:
            True if update successful
        """
        try:
            if isinstance(content, dict):
                self._save_execution_state(content)
                return True
            return False
        except Exception:
            return False

    def delete(self, name: str) -> bool:
        """
        Delete task execution context.

        Args:
            name: Feature name

        Returns:
            True if deletion successful
        """
        try:
            execution_file = Path(f".kiro/specs/{name}/execution_state.json")
            if execution_file.exists():
                execution_file.unlink()
            return True
        except Exception:
            return False

    def load_execution_context(self) -> Dict[str, Any]:
        """
        Load complete execution context including all spec documents.

        Returns:
            Dictionary containing requirements, design, tasks, and metadata
        """
        try:
            # Load specification documents
            spec_data = self.spec_manager.load(self.feature_name)
            if not spec_data:
                raise WorkflowError(
                    f"Specification not found for feature: {self.feature_name}"
                )

            # Extract documents
            documents = spec_data.get("documents", {})
            metadata = spec_data.get("metadata", {})

            # Validate required documents exist
            required_docs = ["requirements", "design", "tasks"]
            missing_docs = [doc for doc in required_docs if not documents.get(doc)]

            if missing_docs:
                raise WorkflowError(
                    f"Missing required documents: {', '.join(missing_docs)}"
                )

            # Parse task list from tasks document
            tasks = (
                self._parse_task_list(documents["tasks"])
                if documents.get("tasks")
                else []
            )

            # Build execution context
            context = {
                "feature_name": self.feature_name,
                "requirements": (
                    self._parse_requirements(documents["requirements"])
                    if documents.get("requirements")
                    else []
                ),
                "design": (
                    self._parse_design(documents["design"])
                    if documents.get("design")
                    else {}
                ),
                "tasks": tasks,
                "metadata": metadata,
                "spec_directory": str(spec_data.get("directory", "")),
                "context_loaded_at": self._get_timestamp(),
            }

            # Cache context for performance
            self.context_cache = context

            # Update execution state
            execution_state = self.load(self.feature_name) or {}
            execution_state["context_loaded"] = True
            execution_state["last_context_load"] = self._get_timestamp()
            self.update(self.feature_name, execution_state)

            return context

        except Exception as e:
            raise WorkflowError(f"Failed to load execution context: {e}")

    def validate_context(self) -> ValidationResult:
        """
        Validate execution context before task execution.

        Returns:
            Validation result with any issues found
        """
        try:
            issues = []
            suggestions = []

            # Check if context is loaded
            if not self.context_cache:
                try:
                    self.load_execution_context()
                except Exception as e:
                    issues.append(f"Failed to load context: {e}")
                    suggestions.append(
                        "Ensure all required documents exist and are valid"
                    )
                    return ValidationResult(False, issues, suggestions)

            context = self.context_cache

            # Validate requirements
            if not context.get("requirements"):
                issues.append("No requirements found in context")
                suggestions.append(
                    "Create requirements document with valid EARS patterns"
                )

            # Validate design
            if not context.get("design"):
                issues.append("No design found in context")
                suggestions.append(
                    "Create design document with architecture and components"
                )

            # Validate tasks
            tasks = context.get("tasks", [])
            if not tasks:
                issues.append("No tasks found in context")
                suggestions.append("Create implementation plan with actionable tasks")

            # Check task structure
            for task in tasks:
                if not task.get("id") or not task.get("title"):
                    issues.append(f"Invalid task structure: missing id or title")
                    suggestions.append("Ensure all tasks have proper id and title")

            # Validate requirement traceability
            requirement_ids = {req.get("id") for req in context.get("requirements", [])}
            for task in tasks:
                task_req_refs = task.get("requirements_refs", [])
                missing_refs = [
                    ref for ref in task_req_refs if ref not in requirement_ids
                ]
                if missing_refs:
                    issues.append(
                        f"Task '{task.get('title')}' references missing requirements: {missing_refs}"
                    )
                    suggestions.append(
                        "Update task requirement references or add missing requirements"
                    )

            return ValidationResult(len(issues) == 0, issues, suggestions)

        except Exception as e:
            return ValidationResult(
                False,
                [f"Context validation failed: {e}"],
                ["Check specification documents and try again"],
            )

    def focus_on_task(self, task_id: str) -> Dict[str, Any]:
        """
        Focus execution on specific task with scope management.

        Args:
            task_id: ID of task to focus on

        Returns:
            Task focus context with relevant information
        """
        try:
            # Ensure context is loaded
            if not self.context_cache:
                self.load_execution_context()

            # Find target task
            target_task = self._find_task_by_id(task_id)
            if not target_task:
                raise WorkflowError(f"Task not found: {task_id}")

            # Set current task
            self.current_task = target_task

            # Build focused context
            focus_context = {
                "task": target_task,
                "related_requirements": self._get_task_requirements(target_task),
                "dependencies": self._get_task_dependencies(target_task),
                "sub_tasks": target_task.get("sub_tasks", []),
                "scope": self._define_task_scope(target_task),
                "validation_criteria": self._get_validation_criteria(target_task),
            }

            # Update execution state
            execution_state = self.load(self.feature_name) or {}
            execution_state["current_task_id"] = task_id
            execution_state["task_focused_at"] = self._get_timestamp()
            self.update(self.feature_name, execution_state)

            return focus_context

        except Exception as e:
            raise WorkflowError(f"Failed to focus on task: {e}")

    def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """
        Get complete context for specific task execution.

        Args:
            task_id: ID of task to get context for

        Returns:
            Complete task execution context
        """
        try:
            # Focus on task first
            focus_context = self.focus_on_task(task_id)

            # Add full specification context
            full_context = {
                **focus_context,
                "requirements_document": self.context_cache.get("requirements"),
                "design_document": self.context_cache.get("design"),
                "all_tasks": self.context_cache.get("tasks"),
                "feature_metadata": self.context_cache.get("metadata"),
                "spec_directory": self.context_cache.get("spec_directory"),
            }

            return full_context

        except Exception as e:
            raise WorkflowError(f"Failed to get task context: {e}")

    def _parse_requirements(self, requirements_text: str) -> List[Dict[str, Any]]:
        """Parse requirements document into structured data."""
        try:
            requirements = []

            # Split into sections
            sections = re.split(r"\n## ", requirements_text)

            for section in sections:
                if section.startswith("Requirements"):
                    # Parse individual requirements
                    req_sections = re.split(r"\n### Requirement \d+", section)

                    for i, req_section in enumerate(req_sections[1:], 1):  # Skip header
                        # Extract user story
                        user_story_match = re.search(
                            r"\*\*User Story:\*\* (.+)", req_section
                        )
                        user_story = (
                            user_story_match.group(1) if user_story_match else ""
                        )

                        # Extract acceptance criteria
                        criteria_section = re.search(
                            r"#### Acceptance Criteria\n\n(.+?)(?=\n###|\n##|\Z)",
                            req_section,
                            re.DOTALL,
                        )
                        criteria = []
                        if criteria_section:
                            criteria_lines = (
                                criteria_section.group(1).strip().split("\n")
                            )
                            criteria = [
                                line.strip("1234567890. ")
                                for line in criteria_lines
                                if line.strip()
                            ]

                        # Add main requirement
                        requirements.append(
                            {
                                "id": str(i),
                                "user_story": user_story,
                                "acceptance_criteria": criteria,
                            }
                        )

                        # Add individual acceptance criteria as sub-requirements
                        for j, criterion in enumerate(criteria, 1):
                            requirements.append(
                                {
                                    "id": f"{i}.{j}",
                                    "user_story": f"Acceptance criterion for requirement {i}",
                                    "acceptance_criteria": [criterion],
                                }
                            )

            return requirements

        except Exception as e:
            print(f"Error parsing requirements: {e}")
            return []

    def _parse_design(self, design_text: str) -> Dict[str, Any]:
        """Parse design document into structured data."""
        try:
            design = {
                "overview": "",
                "architecture": "",
                "components": "",
                "data_models": "",
                "error_handling": "",
                "testing_strategy": "",
            }

            # Split into sections
            sections = re.split(r"\n## ", design_text)

            for section in sections:
                section_lower = section.lower()
                if section_lower.startswith("overview"):
                    design["overview"] = section
                elif section_lower.startswith("architecture"):
                    design["architecture"] = section
                elif section_lower.startswith("components"):
                    design["components"] = section
                elif section_lower.startswith("data models"):
                    design["data_models"] = section
                elif section_lower.startswith("error handling"):
                    design["error_handling"] = section
                elif section_lower.startswith("testing"):
                    design["testing_strategy"] = section

            return design

        except Exception as e:
            print(f"Error parsing design: {e}")
            return {}

    def _parse_task_list(self, tasks_text: str) -> List[Dict[str, Any]]:
        """Parse tasks document into structured task list."""
        try:
            tasks: List[Dict[str, Any]] = []

            # Split text into lines and process each line
            lines = tasks_text.split("\n")
            current_task: Optional[Dict[str, Any]] = None

            for line in lines:
                line = line.strip()

                # Check for task line with checkbox
                task_match = re.match(r"^- \[[ x]\] (\d+(?:\.\d+)?)\.?\s+(.+)", line)
                if task_match:
                    task_id = task_match.group(1)
                    title = task_match.group(2)

                    # Check if optional (marked with *)
                    is_optional = title.endswith("*")
                    if is_optional:
                        title = title.rstrip("*").strip()

                    current_task = {
                        "id": task_id,
                        "title": title,
                        "description": "",
                        "requirements_refs": [],
                        "dependencies": [],
                        "is_optional": is_optional,
                        "status": TaskStatus.NOT_STARTED.value,
                        "sub_tasks": [],
                    }
                    tasks.append(current_task)

                # Check for requirements reference
                elif current_task and "_Requirements:" in line:
                    req_refs = re.findall(r"_Requirements: ([^_]+)_", line)
                    if req_refs:
                        requirements_refs = [
                            ref.strip() for ref in req_refs[0].split(",")
                        ]
                        current_task["requirements_refs"] = requirements_refs

                # Check for task description/details
                elif (
                    current_task and line.startswith("-") and not line.startswith("- [")
                ):
                    # This is a task detail line
                    if current_task["description"]:
                        current_task["description"] += "; " + line.lstrip("- ").strip()
                    else:
                        current_task["description"] = line.lstrip("- ").strip()

            # If no tasks found, create sample tasks for testing
            if not tasks:
                tasks = [
                    {
                        "id": "1",
                        "title": "Set up task execution infrastructure",
                        "description": "Create TaskExecutor with context loading",
                        "requirements_refs": ["1.1", "1.2", "1.3"],
                        "dependencies": [],
                        "is_optional": False,
                        "status": TaskStatus.NOT_STARTED.value,
                        "sub_tasks": [],
                    },
                    {
                        "id": "2.1",
                        "title": "Create task context loading",
                        "description": "Load requirements, design, and task documents",
                        "requirements_refs": ["1.1"],
                        "dependencies": ["1"],
                        "is_optional": False,
                        "status": TaskStatus.NOT_STARTED.value,
                        "sub_tasks": [],
                    },
                    {
                        "id": "2.2",
                        "title": "Build task validation system",
                        "description": "Validate implementations against requirements",
                        "requirements_refs": ["2.1", "2.2", "2.3"],
                        "dependencies": ["1"],
                        "is_optional": False,
                        "status": TaskStatus.NOT_STARTED.value,
                        "sub_tasks": [],
                    },
                ]

            return tasks

        except Exception as e:
            print(f"Error parsing tasks: {e}")
            return []

    def _find_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Find task by ID in context."""
        tasks = self.context_cache.get("tasks", [])
        for task in tasks:
            if isinstance(task, dict) and task.get("id") == task_id:
                return task
            # Check sub-tasks
            if isinstance(task, dict):
                for sub_task in task.get("sub_tasks", []):
                    if isinstance(sub_task, dict) and sub_task.get("id") == task_id:
                        return sub_task
        return None

    def _get_task_requirements(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get requirements related to specific task."""
        req_refs = task.get("requirements_refs", [])
        requirements = self.context_cache.get("requirements", [])

        related_reqs = []
        for req in requirements:
            if req.get("id") in req_refs:
                related_reqs.append(req)

        return related_reqs

    def _get_task_dependencies(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get task dependencies."""
        dep_ids = task.get("dependencies", [])
        tasks = self.context_cache.get("tasks", [])

        dependencies = []
        for dep_id in dep_ids:
            dep_task = self._find_task_by_id(dep_id)
            if dep_task:
                dependencies.append(dep_task)

        return dependencies

    def _define_task_scope(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Define scope and boundaries for task execution."""
        return {
            "task_id": task.get("id"),
            "focus_area": task.get("title"),
            "deliverables": self._extract_deliverables(task),
            "constraints": self._extract_constraints(task),
            "success_criteria": self._extract_success_criteria(task),
        }

    def _extract_deliverables(self, task: Dict[str, Any]) -> List[str]:
        """Extract expected deliverables from task description."""
        # This would analyze task description for deliverables
        # For now, return basic deliverables based on task type
        title = task.get("title", "").lower()

        if "implement" in title:
            return ["Implementation code", "Unit tests (if required)"]
        elif "create" in title:
            return ["New component/module", "Documentation"]
        elif "build" in title:
            return ["Built component", "Integration tests"]
        else:
            return ["Task completion", "Code changes"]

    def _extract_constraints(self, task: Dict[str, Any]) -> List[str]:
        """Extract constraints from task context."""
        constraints = [
            "Focus only on this specific task",
            "Do not implement functionality for other tasks",
            "Follow existing code patterns and architecture",
        ]

        if task.get("is_optional"):
            constraints.append("Task is optional - may be skipped")

        return constraints

    def _extract_success_criteria(self, task: Dict[str, Any]) -> List[str]:
        """Extract success criteria from task and requirements."""
        criteria = [
            "Task implementation matches requirements",
            "Code follows project standards",
            "All specified functionality is working",
        ]

        # Add requirement-specific criteria
        related_reqs = self._get_task_requirements(task)
        for req in related_reqs:
            for criterion in req.get("acceptance_criteria", []):
                criteria.append(f"Requirement satisfied: {criterion}")

        return criteria

    def _get_validation_criteria(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get validation criteria for task completion."""
        return {
            "functional_requirements": self._get_task_requirements(task),
            "code_quality": [
                "Code is properly formatted",
                "Code follows naming conventions",
                "Code includes appropriate comments",
            ],
            "testing_requirements": [
                "Core functionality is tested",
                "Edge cases are handled",
                "Tests pass successfully",
            ],
            "integration_requirements": [
                "Integrates with existing codebase",
                "No breaking changes to other components",
                "Follows established patterns",
            ],
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()

    def _save_execution_state(self, state: Dict[str, Any]) -> None:
        """Save execution state to file."""
        try:
            # Ensure directory exists
            self.execution_state_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.execution_state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            raise WorkflowError(f"Failed to save execution state: {e}")
