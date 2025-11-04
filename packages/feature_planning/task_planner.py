"""
Task Planner for implementation planning.

This module converts approved designs into actionable implementation tasks
with proper dependency management and requirement traceability.
"""

import re
from typing import Dict, List, Optional, Tuple

from .base import BaseGenerator, Requirement, Task, TaskStatus
from .config import get_config


class TaskPlanner(BaseGenerator):
    """
    Converts designs into actionable implementation tasks.

    Creates numbered task lists with dependencies, requirement traceability,
    and optional task marking for focused development.
    """

    def __init__(self) -> None:
        """Initialize Task Planner with configuration."""
        self.config = get_config()
        self.max_hierarchy_levels = self.config.get_setting("task_hierarchy_levels", 2)

    def generate(self, input_data: str) -> str:
        """
        Generate task list from design document.

        Args:
            input_data: Design document content

        Returns:
            Generated task list in markdown format
        """
        if not self.validate_input(input_data):
            raise ValueError("Invalid design document provided")

        # Generate structured tasks
        tasks = self.generate_tasks(input_data)

        # Create dependency graph
        dependencies = self.create_dependencies(tasks)

        # Convert to markdown format
        return self._format_tasks_as_markdown(tasks)

    def validate_input(self, input_data: str) -> bool:
        """
        Validate design document before task generation.

        Args:
            input_data: Design document to validate

        Returns:
            True if design is valid for task generation
        """
        if not input_data or not input_data.strip():
            return False

        # Check for required sections
        required_sections = ["## Overview", "## Architecture", "## Components"]
        for section in required_sections:
            if section not in input_data:
                return False

        # Check for at least one component definition
        component_pattern = r"### ([A-Za-z\s]+)\n\n\*\*Purpose\*\*:"
        if not re.search(component_pattern, input_data):
            return False

        return True

    def generate_tasks(self, design_content: str) -> List[Task]:
        """
        Generate structured task list from design.

        Args:
            design_content: Design document content

        Returns:
            List of structured tasks with dependencies
        """
        tasks = []

        # Extract components from design document
        components = self._extract_components(design_content)
        interfaces = self._extract_interfaces(design_content)
        data_models = self._extract_data_models(design_content)

        # Generate tasks for each major component
        task_counter = 1

        # 1. Setup and infrastructure tasks
        setup_task = Task(
            id=f"{task_counter}",
            title="Set up project structure and core interfaces",
            description="Create directory structure and define base interfaces",
            requirements_refs=["1.1", "1.2"],
            dependencies=[],
            is_optional=False,
            status=TaskStatus.NOT_STARTED,
            sub_tasks=[],
        )
        tasks.append(setup_task)
        task_counter += 1

        # 2. Component implementation tasks
        for component in components:
            component_task = Task(
                id=f"{task_counter}",
                title=f"Implement {component['name']} component",
                description=f"Build {component['description']}",
                requirements_refs=component.get("requirements", []),
                dependencies=[setup_task.id],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=self._generate_component_subtasks(component, task_counter),
            )
            tasks.append(component_task)
            task_counter += 1

        # 3. Integration tasks
        if len(components) > 1:
            integration_task = Task(
                id=f"{task_counter}",
                title="Integrate components and finalize system",
                description="Wire components together and ensure system cohesion",
                requirements_refs=["4.1", "4.2"],
                dependencies=[str(i) for i in range(2, task_counter)],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[],
            )
            tasks.append(integration_task)

        return tasks

    def create_dependencies(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """
        Create dependency graph for tasks.

        Args:
            tasks: List of tasks to analyze

        Returns:
            Dictionary mapping task IDs to their dependencies
        """
        dependency_graph = {}

        for task in tasks:
            dependency_graph[task.id] = task.dependencies.copy()

            # Add implicit dependencies based on task ordering
            task_num = int(task.id)
            if task_num > 1:
                # Each task depends on the previous setup/foundation tasks
                for i in range(1, task_num):
                    dep_id = str(i)
                    if dep_id not in dependency_graph[task.id]:
                        # Only add if it's a foundational dependency
                        if self._is_foundational_dependency(tasks, dep_id, task.id):
                            dependency_graph[task.id].append(dep_id)

        return dependency_graph

    def mark_optional_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Mark optional tasks (tests, documentation) with "*" suffix.

        Args:
            tasks: List of tasks to analyze

        Returns:
            Tasks with optional marking applied
        """
        optional_keywords = [
            "test",
            "testing",
            "unit test",
            "integration test",
            "documentation",
            "docs",
            "readme",
            "comment",
            "logging",
            "debug",
            "monitor",
            "metric",
        ]

        for task in tasks:
            # Check main task
            if self._is_optional_task(task.title, task.description, optional_keywords):
                task.is_optional = True

            # Check sub-tasks
            for subtask in task.sub_tasks:
                if self._is_optional_task(
                    subtask.title, subtask.description, optional_keywords
                ):
                    subtask.is_optional = True

        return tasks

    def validate_completeness(
        self, tasks: List[Task], requirements: List[Requirement]
    ) -> bool:
        """
        Validate that tasks cover all requirements.

        Args:
            tasks: Generated tasks
            requirements: Original requirements

        Returns:
            True if all requirements are covered
        """
        # Get all requirement IDs from requirements
        requirement_ids = {req.id for req in requirements}

        # Get all requirement references from tasks
        covered_requirements = set()
        for task in tasks:
            covered_requirements.update(task.requirements_refs)
            for subtask in task.sub_tasks:
                covered_requirements.update(subtask.requirements_refs)

        # Check if all requirements are covered
        uncovered = requirement_ids - covered_requirements
        return len(uncovered) == 0

    def _extract_components(self, design_content: str) -> List[Dict]:
        """Extract component information from design document."""
        components = []

        # Look for component sections in the design
        component_pattern = r"### ([A-Za-z\s]+)\n\n\*\*Purpose\*\*:\s*([^\n]+)"
        matches = re.findall(component_pattern, design_content)

        for match in matches:
            name = match[0].strip()
            description = match[1].strip()

            # Extract requirements references for this component
            requirements = self._extract_requirements_for_component(
                design_content, name
            )

            components.append(
                {"name": name, "description": description, "requirements": requirements}
            )

        return components

    def _extract_interfaces(self, design_content: str) -> List[Dict]:
        """Extract interface definitions from design document."""
        interfaces = []

        # Look for interface code blocks
        interface_pattern = r"```python\nclass\s+(\w+):\n(.*?)\n```"
        matches = re.findall(interface_pattern, design_content, re.DOTALL)

        for match in matches:
            interfaces.append({"name": match[0], "definition": match[1]})

        return interfaces

    def _extract_data_models(self, design_content: str) -> List[Dict]:
        """Extract data model definitions from design document."""
        models = []

        # Look for dataclass definitions
        model_pattern = r"@dataclass\nclass\s+(\w+):\n(.*?)(?=\n@|\n```|\Z)"
        matches = re.findall(model_pattern, design_content, re.DOTALL)

        for match in matches:
            models.append({"name": match[0], "definition": match[1]})

        return models

    def _extract_requirements_for_component(
        self, design_content: str, component_name: str
    ) -> List[str]:
        """Extract requirement references for a specific component."""
        # Look for requirement references in the component section
        component_section_pattern = f"### {re.escape(component_name)}.*?(?=### |\\Z)"
        section_match = re.search(component_section_pattern, design_content, re.DOTALL)

        if section_match:
            section_text = section_match.group(0)
            # Find requirement references like "1.1", "2.3", etc.
            req_pattern = r"\b\d+\.\d+\b"
            requirements = re.findall(req_pattern, section_text)
            return list(set(requirements))  # Remove duplicates

        return []

    def _generate_component_subtasks(
        self, component: Dict, parent_id: int
    ) -> List[Task]:
        """Generate subtasks for a component."""
        subtasks = []

        # Core implementation subtask
        core_task = Task(
            id=f"{parent_id}.1",
            title=f"Implement core {component['name']} functionality",
            description=f"Build the main logic for {component['description']}",
            requirements_refs=component.get("requirements", []),
            dependencies=[],
            is_optional=False,
            status=TaskStatus.NOT_STARTED,
            sub_tasks=[],
        )
        subtasks.append(core_task)

        # Interface implementation subtask
        interface_task = Task(
            id=f"{parent_id}.2",
            title=f"Implement {component['name']} interfaces",
            description=f"Create public interfaces and API contracts",
            requirements_refs=component.get("requirements", []),
            dependencies=[f"{parent_id}.1"],
            is_optional=False,
            status=TaskStatus.NOT_STARTED,
            sub_tasks=[],
        )
        subtasks.append(interface_task)

        # Optional testing subtask
        test_task = Task(
            id=f"{parent_id}.3",
            title=f"Write unit tests for {component['name']}",
            description=f"Create comprehensive tests for {component['name']} functionality",
            requirements_refs=component.get("requirements", []),
            dependencies=[f"{parent_id}.2"],
            is_optional=True,  # Mark as optional
            status=TaskStatus.NOT_STARTED,
            sub_tasks=[],
        )
        subtasks.append(test_task)

        return subtasks

    def _is_foundational_dependency(
        self, tasks: List[Task], dep_id: str, task_id: str
    ) -> bool:
        """Check if a dependency is foundational (setup, core infrastructure)."""
        dep_task = next((t for t in tasks if t.id == dep_id), None)
        if not dep_task:
            return False

        # Setup and infrastructure tasks are foundational
        foundational_keywords = ["setup", "structure", "core", "base", "foundation"]
        return any(
            keyword in dep_task.title.lower() for keyword in foundational_keywords
        )

    def _format_tasks_as_markdown(self, tasks: List[Task]) -> str:
        """Format tasks as markdown checklist."""
        lines = ["# Implementation Plan", ""]

        for task in tasks:
            # Main task
            checkbox = "[ ]"
            optional_marker = "*" if task.is_optional else ""
            lines.append(f"- {checkbox}{optional_marker} {task.id}. {task.title}")

            if task.description:
                lines.append(f"  - {task.description}")

            if task.requirements_refs:
                req_refs = ", ".join(task.requirements_refs)
                lines.append(f"  - _Requirements: {req_refs}_")

            lines.append("")

            # Sub-tasks
            for subtask in task.sub_tasks:
                sub_checkbox = "[ ]"
                sub_optional = "*" if subtask.is_optional else ""
                lines.append(
                    f"- {sub_checkbox}{sub_optional} {subtask.id} {subtask.title}"
                )

                if subtask.description:
                    lines.append(f"  - {subtask.description}")

                if subtask.requirements_refs:
                    sub_req_refs = ", ".join(subtask.requirements_refs)
                    lines.append(f"  - _Requirements: {sub_req_refs}_")

                lines.append("")

        return "\n".join(lines)

    def _is_optional_task(
        self, title: str, description: str, optional_keywords: List[str]
    ) -> bool:
        """Check if a task should be marked as optional."""
        text_to_check = f"{title} {description}".lower()
        return any(keyword in text_to_check for keyword in optional_keywords)

    def filter_tasks_by_type(
        self, tasks: List[Task], include_optional: bool = True
    ) -> List[Task]:
        """Filter tasks based on optional/core categorization."""
        filtered_tasks = []

        for task in tasks:
            # Include task based on optional flag
            if include_optional or not task.is_optional:
                # Create a copy with filtered sub-tasks
                filtered_subtasks = [
                    subtask
                    for subtask in task.sub_tasks
                    if include_optional or not subtask.is_optional
                ]

                task_copy = Task(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    requirements_refs=task.requirements_refs,
                    dependencies=task.dependencies,
                    is_optional=task.is_optional,
                    status=task.status,
                    sub_tasks=filtered_subtasks,
                )
                filtered_tasks.append(task_copy)

        return filtered_tasks

    def get_task_categories(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """Categorize tasks into core and optional groups."""
        core_tasks = []
        optional_tasks = []

        for task in tasks:
            if task.is_optional:
                optional_tasks.append(task)
            else:
                core_tasks.append(task)

                # Check sub-tasks
                for subtask in task.sub_tasks:
                    if subtask.is_optional:
                        optional_tasks.append(subtask)

        return {"core": core_tasks, "optional": optional_tasks}

    def validate_coding_focus(self, tasks: List[Task]) -> Tuple[bool, List[str]]:
        """
        Validate that tasks focus exclusively on coding and testing activities.

        Args:
            tasks: List of tasks to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        # Non-coding activities to flag
        non_coding_keywords = [
            "deploy",
            "deployment",
            "production",
            "staging",
            "user testing",
            "user feedback",
            "user acceptance",
            "performance metrics",
            "analytics",
            "monitoring setup",
            "training",
            "documentation creation",
            "marketing",
            "business process",
            "organizational",
            "communication",
        ]

        for task in tasks:
            # Check main task
            task_issues = self._check_task_coding_focus(task, non_coding_keywords)
            issues.extend(task_issues)

            # Check sub-tasks
            for subtask in task.sub_tasks:
                subtask_issues = self._check_task_coding_focus(
                    subtask, non_coding_keywords
                )
                issues.extend(subtask_issues)

        return len(issues) == 0, issues

    def validate_task_actionability(self, tasks: List[Task]) -> Tuple[bool, List[str]]:
        """
        Validate that tasks are actionable for coding agents.

        Args:
            tasks: List of tasks to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []

        for task in tasks:
            # Check if task has clear coding objective
            if not self._has_clear_coding_objective(task):
                issues.append(
                    f"Task {task.id} lacks clear coding objective: {task.title}"
                )

            # Check if task is specific enough
            if not self._is_sufficiently_specific(task):
                issues.append(f"Task {task.id} is too vague: {task.title}")

            # Check sub-tasks
            for subtask in task.sub_tasks:
                if not self._has_clear_coding_objective(subtask):
                    issues.append(
                        f"Subtask {subtask.id} lacks clear coding objective: {subtask.title}"
                    )

                if not self._is_sufficiently_specific(subtask):
                    issues.append(f"Subtask {subtask.id} is too vague: {subtask.title}")

        return len(issues) == 0, issues

    def _check_task_coding_focus(
        self, task: Task, non_coding_keywords: List[str]
    ) -> List[str]:
        """Check if a single task focuses on coding activities."""
        issues = []
        text_to_check = f"{task.title} {task.description}".lower()

        for keyword in non_coding_keywords:
            if keyword in text_to_check:
                issues.append(
                    f"Task {task.id} contains non-coding activity '{keyword}': {task.title}"
                )

        return issues

    def _has_clear_coding_objective(self, task: Task) -> bool:
        """Check if task has a clear coding objective."""
        coding_verbs = [
            "implement",
            "create",
            "build",
            "write",
            "develop",
            "code",
            "program",
            "design",
            "construct",
            "generate",
            "test",
            "validate",
            "verify",
            "debug",
            "fix",
        ]

        text_to_check = f"{task.title} {task.description}".lower()
        return any(verb in text_to_check for verb in coding_verbs)

    def _is_sufficiently_specific(self, task: Task) -> bool:
        """Check if task is specific enough for implementation."""
        # Task should have description and not be too generic
        if not task.description or len(task.description.strip()) < 10:
            return False

        # Avoid overly generic terms
        generic_terms = ["support", "handle", "manage", "process", "deal with"]
        text_to_check = f"{task.title} {task.description}".lower()

        # If it contains generic terms without specifics, it's not specific enough
        has_generic = any(term in text_to_check for term in generic_terms)
        has_specifics = any(
            word in text_to_check
            for word in ["class", "function", "method", "interface", "api", "model"]
        )

        return not has_generic or has_specifics
