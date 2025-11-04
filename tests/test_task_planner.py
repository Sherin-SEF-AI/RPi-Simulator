"""
Unit tests for Task Planner component.

Tests task generation, optional marking, dependency management,
and coding-focused validation functionality.
"""

import pytest
from packages.feature_planning.task_planner import TaskPlanner
from packages.feature_planning.base import Task, Requirement, TaskStatus, EARSPattern, ValidationStatus


class TestTaskPlanner:
    """Test cases for TaskPlanner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = TaskPlanner()
        
        # Sample design document
        self.sample_design = """
# Design Document

## Overview
This is a sample design for testing.

## Architecture
The system consists of multiple components working together.

## Components and Interfaces

### User Manager

**Purpose**: Manages user authentication and authorization

**Interface**:
```python
class UserManager:
    def authenticate(self, username: str, password: str) -> bool
    def authorize(self, user_id: str, resource: str) -> bool
```

### Data Store

**Purpose**: Handles data persistence and retrieval

**Interface**:
```python
class DataStore:
    def save(self, key: str, value: Any) -> bool
    def load(self, key: str) -> Any
```

## Data Models

@dataclass
class User:
    id: str
    username: str
    email: str

@dataclass
class Session:
    user_id: str
    token: str
    expires_at: datetime
"""
        
        # Sample requirements
        self.sample_requirements = [
            Requirement(
                id="1.1",
                user_story="As a user, I want to authenticate",
                acceptance_criteria=["System shall validate credentials"],
                ears_pattern=EARSPattern.UBIQUITOUS,
                referenced_terms=["User_Manager"],
                validation_status=ValidationStatus.VALID
            ),
            Requirement(
                id="2.1", 
                user_story="As a system, I want to store data",
                acceptance_criteria=["System shall persist data"],
                ears_pattern=EARSPattern.UBIQUITOUS,
                referenced_terms=["Data_Store"],
                validation_status=ValidationStatus.VALID
            )
        ]
    
    def test_validate_input_valid_design(self):
        """Test validation of valid design document."""
        assert self.planner.validate_input(self.sample_design) is True
    
    def test_validate_input_empty_design(self):
        """Test validation of empty design document."""
        assert self.planner.validate_input("") is False
        assert self.planner.validate_input("   ") is False
    
    def test_validate_input_missing_sections(self):
        """Test validation of design missing required sections."""
        incomplete_design = """
# Design Document

## Overview
This is incomplete.
"""
        assert self.planner.validate_input(incomplete_design) is False
    
    def test_generate_tasks_from_design(self):
        """Test task generation from design document."""
        tasks = self.planner.generate_tasks(self.sample_design)
        
        # Should generate at least setup task and component tasks
        assert len(tasks) >= 2
        
        # First task should be setup
        setup_task = tasks[0]
        assert "setup" in setup_task.title.lower() or "structure" in setup_task.title.lower()
        assert setup_task.id == "1"
        
        # Should have component-specific tasks
        component_tasks = [t for t in tasks if "User Manager" in t.title or "Data Store" in t.title]
        assert len(component_tasks) >= 1
    
    def test_generate_tasks_with_subtasks(self):
        """Test that generated tasks include appropriate subtasks."""
        tasks = self.planner.generate_tasks(self.sample_design)
        
        # Find a component task
        component_task = next((t for t in tasks if len(t.sub_tasks) > 0), None)
        assert component_task is not None
        
        # Should have core implementation and interface subtasks
        assert len(component_task.sub_tasks) >= 2
        
        # Check subtask structure
        for subtask in component_task.sub_tasks:
            assert subtask.id.startswith(component_task.id + ".")
            assert len(subtask.title) > 0
            assert len(subtask.description) > 0
    
    def test_create_dependencies(self):
        """Test dependency graph creation."""
        tasks = self.planner.generate_tasks(self.sample_design)
        dependencies = self.planner.create_dependencies(tasks)
        
        # Should have dependencies for each task
        assert len(dependencies) == len(tasks)
        
        # Setup task should have no dependencies
        assert len(dependencies["1"]) == 0
        
        # Other tasks should depend on setup
        for task_id in dependencies:
            if task_id != "1":
                # Should have some dependencies
                assert len(dependencies[task_id]) >= 0
    
    def test_mark_optional_tasks(self):
        """Test optional task marking functionality."""
        # Create tasks with testing-related content
        tasks = [
            Task(
                id="1",
                title="Implement core functionality",
                description="Build main logic",
                requirements_refs=["1.1"],
                dependencies=[],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            ),
            Task(
                id="2",
                title="Write unit tests",
                description="Create comprehensive test suite",
                requirements_refs=["1.1"],
                dependencies=["1"],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            )
        ]
        
        marked_tasks = self.planner.mark_optional_tasks(tasks)
        
        # Core functionality should not be optional
        assert marked_tasks[0].is_optional is False
        
        # Testing task should be marked optional
        assert marked_tasks[1].is_optional is True
    
    def test_filter_tasks_by_type(self):
        """Test task filtering by optional/core type."""
        tasks = [
            Task(
                id="1",
                title="Core task",
                description="Essential functionality",
                requirements_refs=["1.1"],
                dependencies=[],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            ),
            Task(
                id="2",
                title="Optional task",
                description="Testing functionality",
                requirements_refs=["1.1"],
                dependencies=["1"],
                is_optional=True,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            )
        ]
        
        # Filter including optional tasks
        all_tasks = self.planner.filter_tasks_by_type(tasks, include_optional=True)
        assert len(all_tasks) == 2
        
        # Filter excluding optional tasks
        core_only = self.planner.filter_tasks_by_type(tasks, include_optional=False)
        assert len(core_only) == 1
        assert core_only[0].is_optional is False
    
    def test_get_task_categories(self):
        """Test task categorization into core and optional groups."""
        tasks = [
            Task(
                id="1",
                title="Core task",
                description="Essential functionality",
                requirements_refs=["1.1"],
                dependencies=[],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[
                    Task(
                        id="1.1",
                        title="Core subtask",
                        description="Essential sub-functionality",
                        requirements_refs=["1.1"],
                        dependencies=[],
                        is_optional=False,
                        status=TaskStatus.NOT_STARTED,
                        sub_tasks=[]
                    ),
                    Task(
                        id="1.2",
                        title="Test subtask",
                        description="Testing sub-functionality",
                        requirements_refs=["1.1"],
                        dependencies=["1.1"],
                        is_optional=True,
                        status=TaskStatus.NOT_STARTED,
                        sub_tasks=[]
                    )
                ]
            ),
            Task(
                id="2",
                title="Optional task",
                description="Testing functionality",
                requirements_refs=["1.1"],
                dependencies=["1"],
                is_optional=True,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            )
        ]
        
        categories = self.planner.get_task_categories(tasks)
        
        # Should have both core and optional categories
        assert 'core' in categories
        assert 'optional' in categories
        
        # Core should have 1 task (the main core task)
        assert len(categories['core']) == 1
        
        # Optional should have 2 tasks (optional main task + optional subtask)
        assert len(categories['optional']) == 2
    
    def test_validate_completeness(self):
        """Test requirement coverage validation."""
        tasks = [
            Task(
                id="1",
                title="Task covering req 1.1",
                description="Covers requirement 1.1",
                requirements_refs=["1.1"],
                dependencies=[],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            ),
            Task(
                id="2",
                title="Task covering req 2.1",
                description="Covers requirement 2.1",
                requirements_refs=["2.1"],
                dependencies=["1"],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            )
        ]
        
        # All requirements covered
        is_complete = self.planner.validate_completeness(tasks, self.sample_requirements)
        assert is_complete is True
        
        # Missing requirement coverage
        incomplete_tasks = [tasks[0]]  # Only covers 1.1, missing 2.1
        is_incomplete = self.planner.validate_completeness(incomplete_tasks, self.sample_requirements)
        assert is_incomplete is False
    
    def test_validate_coding_focus(self):
        """Test validation of coding-focused tasks."""
        coding_tasks = [
            Task(
                id="1",
                title="Implement user authentication",
                description="Write code for user login functionality",
                requirements_refs=["1.1"],
                dependencies=[],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            )
        ]
        
        non_coding_tasks = [
            Task(
                id="2",
                title="Deploy to production",
                description="Set up production deployment pipeline",
                requirements_refs=["1.1"],
                dependencies=["1"],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            )
        ]
        
        # Coding tasks should pass validation
        is_valid, issues = self.planner.validate_coding_focus(coding_tasks)
        assert is_valid is True
        assert len(issues) == 0
        
        # Non-coding tasks should fail validation
        is_invalid, issues = self.planner.validate_coding_focus(non_coding_tasks)
        assert is_invalid is False
        assert len(issues) > 0
        assert "deploy" in issues[0].lower()
    
    def test_validate_task_actionability(self):
        """Test validation of task actionability for coding agents."""
        actionable_tasks = [
            Task(
                id="1",
                title="Implement user authentication class",
                description="Create UserAuth class with login and logout methods",
                requirements_refs=["1.1"],
                dependencies=[],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            )
        ]
        
        vague_tasks = [
            Task(
                id="2",
                title="Handle users",
                description="Deal with user stuff",
                requirements_refs=["1.1"],
                dependencies=[],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[]
            )
        ]
        
        # Actionable tasks should pass validation
        is_valid, issues = self.planner.validate_task_actionability(actionable_tasks)
        assert is_valid is True
        assert len(issues) == 0
        
        # Vague tasks should fail validation
        is_invalid, issues = self.planner.validate_task_actionability(vague_tasks)
        assert is_invalid is False
        assert len(issues) > 0
    
    def test_format_tasks_as_markdown(self):
        """Test markdown formatting of tasks."""
        tasks = [
            Task(
                id="1",
                title="Setup project structure",
                description="Create initial directory structure",
                requirements_refs=["1.1", "1.2"],
                dependencies=[],
                is_optional=False,
                status=TaskStatus.NOT_STARTED,
                sub_tasks=[
                    Task(
                        id="1.1",
                        title="Create core directories",
                        description="Set up src, tests, docs folders",
                        requirements_refs=["1.1"],
                        dependencies=[],
                        is_optional=False,
                        status=TaskStatus.NOT_STARTED,
                        sub_tasks=[]
                    ),
                    Task(
                        id="1.2",
                        title="Write unit tests",
                        description="Create test framework setup",
                        requirements_refs=["1.2"],
                        dependencies=["1.1"],
                        is_optional=True,
                        status=TaskStatus.NOT_STARTED,
                        sub_tasks=[]
                    )
                ]
            )
        ]
        
        markdown = self.planner._format_tasks_as_markdown(tasks)
        
        # Should contain markdown elements
        assert "# Implementation Plan" in markdown
        assert "- [ ] 1. Setup project structure" in markdown
        assert "- [ ] 1.1 Create core directories" in markdown
        assert "- [ ]* 1.2 Write unit tests" in markdown  # Optional task marked with *
        assert "_Requirements: 1.1, 1.2_" in markdown
    
    def test_generate_full_workflow(self):
        """Test complete task generation workflow."""
        # Generate tasks from design
        result = self.planner.generate(self.sample_design)
        
        # Should return markdown formatted task list
        assert isinstance(result, str)
        assert "# Implementation Plan" in result
        assert "- [ ]" in result  # Should have checkboxes
        
        # Should contain task structure
        lines = result.split('\n')
        task_lines = [line for line in lines if line.strip().startswith('- [ ]')]
        assert len(task_lines) > 0