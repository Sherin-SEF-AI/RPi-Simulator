"""
End-to-end tests for Task Execution Framework.

Tests complete task execution workflow, context loading, validation,
user review, and progression control.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from packages.feature_planning.task_executor import TaskExecutor
from packages.feature_planning.task_validator import TaskValidator
from packages.feature_planning.task_progression_controller import TaskProgressionController
from packages.feature_planning.spec_manager import SpecManager
from packages.feature_planning.base import TaskStatus, ValidationResult, WorkflowError


class TestTaskExecutionFramework:
    """Test suite for complete task execution framework."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.feature_name = "test-execution-feature"
        
        # Create .kiro/specs directory structure
        self.spec_dir = Path(self.temp_dir) / ".kiro" / "specs" / self.feature_name
        self.spec_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test specification documents
        self._create_test_documents()
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_documents(self):
        """Create test specification documents."""
        # Requirements document
        requirements_content = """# Requirements Document

## Introduction

Test feature for task execution framework validation.

## Glossary

- **Test_System**: The system under test
- **Task_Executor**: Component that executes implementation tasks

## Requirements

### Requirement 1

**User Story:** As a developer, I want to execute tasks systematically, so that I can implement features incrementally.

#### Acceptance Criteria

1. WHEN a task is selected, THE Task_Executor SHALL load complete context
2. THE Task_Executor SHALL validate implementation against requirements
3. THE Task_Executor SHALL provide feedback on task completion
4. THE Task_Executor SHALL prevent automatic progression to next tasks
5. THE Task_Executor SHALL require user approval before marking tasks complete

### Requirement 2

**User Story:** As a developer, I want task validation and feedback, so that I can ensure quality implementations.

#### Acceptance Criteria

1. THE Task_Executor SHALL validate code quality and structure
2. THE Task_Executor SHALL check requirement traceability
3. THE Task_Executor SHALL provide specific improvement suggestions
4. THE Task_Executor SHALL track task completion status
"""
        
        # Design document
        design_content = """# Design Document

## Overview

Task execution framework with context loading, validation, and progression control.

## Architecture

The framework consists of three main components:
- TaskExecutor: Manages context and task focus
- TaskValidator: Validates implementations and provides feedback
- TaskProgressionController: Controls user review and progression

## Components and Interfaces

### TaskExecutor
- Loads specification context (requirements, design, tasks)
- Focuses on individual tasks with scope management
- Validates context before execution

### TaskValidator
- Validates implementations against requirements
- Provides quality feedback and suggestions
- Tracks validation history

### TaskProgressionController
- Manages user review process
- Prevents automatic task progression
- Tracks completion status

## Data Models

Task execution context includes:
- Requirements with acceptance criteria
- Design specifications
- Task definitions with dependencies
- Validation criteria and success metrics

## Error Handling

- Context loading failures are reported with specific error messages
- Validation errors include actionable suggestions
- Progression control prevents invalid state transitions

## Testing Strategy

- Unit tests for individual components
- Integration tests for component interactions
- End-to-end tests for complete workflow
"""
        
        # Tasks document
        tasks_content = """# Implementation Plan

- [ ] 1. Set up task execution infrastructure
  - Create TaskExecutor with context loading
  - Implement validation framework
  - Build progression control system
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 2. Implement core task execution
- [ ] 2.1 Create task context loading
  - Load requirements, design, and task documents
  - Parse and structure specification data
  - Validate context completeness
  - _Requirements: 1.1_

- [ ] 2.2 Build task validation system
  - Validate implementations against requirements
  - Check code quality and structure
  - Provide feedback and suggestions
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 2.3 Implement progression control
  - Create user review mechanisms
  - Prevent automatic task advancement
  - Track completion status
  - _Requirements: 1.4, 1.5_

- [ ] 3. Add testing and validation
- [ ] 3.1 Write unit tests for components
  - Test TaskExecutor functionality
  - Test TaskValidator operations
  - Test TaskProgressionController behavior
  - _Requirements: 1.1, 2.1_

- [ ] 3.2 Create integration tests
  - Test component interactions
  - Validate end-to-end workflows
  - Test error handling scenarios
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
"""
        
        # Write documents to files
        (self.spec_dir / "requirements.md").write_text(requirements_content)
        (self.spec_dir / "design.md").write_text(design_content)
        (self.spec_dir / "tasks.md").write_text(tasks_content)
        
        # Create metadata
        metadata = {
            "feature_name": self.feature_name,
            "created_at": "2024-01-01T00:00:00",
            "current_phase": "execution",
        }
        (self.spec_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    
    def _setup_executor(self):
        """Helper to set up task executor with correct paths."""
        executor = TaskExecutor(self.feature_name)
        executor.spec_manager.base_path = Path(self.temp_dir) / ".kiro" / "specs"
        executor.execution_state_file = self.spec_dir / "execution_state.json"
        return executor
    
    def _setup_validator(self):
        """Helper to set up task validator with correct paths."""
        validator = TaskValidator(self.feature_name)
        validator.validation_state_file = self.spec_dir / "validation_state.json"
        return validator
    
    def _setup_progression_controller(self):
        """Helper to set up progression controller with correct paths."""
        controller = TaskProgressionController(self.feature_name)
        controller.progression_state_file = self.spec_dir / "progression_state.json"
        controller.task_validator.validation_state_file = self.spec_dir / "validation_state.json"
        return controller


class TestTaskExecutor(TestTaskExecutionFramework):
    """Test TaskExecutor component."""
    
    def test_create_execution_context(self):
        """Test creating new task execution context."""
        executor = self._setup_executor()
        
        result = executor.create(self.feature_name)
        assert result is True
        
        # Check execution state file was created
        assert executor.execution_state_file.exists()
        
        # Load and verify state
        state = executor.load(self.feature_name)
        assert state is not None
        assert state["feature_name"] == self.feature_name
        assert state["context_loaded"] is False
    
    def test_load_execution_context(self):
        """Test loading complete execution context."""
        executor = self._setup_executor()
        executor.create(self.feature_name)
        
        # Load execution context
        context = executor.load_execution_context()
        
        # Verify context structure
        assert context["feature_name"] == self.feature_name
        assert "requirements" in context
        assert "design" in context
        assert "tasks" in context
        assert "metadata" in context
        
        # Verify requirements parsing
        requirements = context["requirements"]
        assert len(requirements) >= 2
        assert all("id" in req for req in requirements)
        assert all("user_story" in req for req in requirements)
        
        # Verify tasks parsing
        tasks = context["tasks"]
        assert len(tasks) > 0
        assert all("id" in task for task in tasks)
        assert all("title" in task for task in tasks)
    
    def test_validate_context(self):
        """Test context validation before task execution."""
        executor = self._setup_executor()
        executor.create(self.feature_name)
        
        # Test validation without loaded context
        result = executor.validate_context()
        assert result.is_valid is True  # Should load context automatically
        
        # Load context and test validation
        executor.load_execution_context()
        result = executor.validate_context()
        
        assert result.is_valid is True
        assert len(result.issues) == 0
    
    def test_focus_on_task(self):
        """Test focusing execution on specific task."""
        executor = self._setup_executor()
        executor.create(self.feature_name)
        executor.load_execution_context()
        
        # Focus on first task
        task_id = "1"
        focus_context = executor.focus_on_task(task_id)
        
        # Verify focus context
        assert focus_context["task"]["id"] == task_id
        assert "related_requirements" in focus_context
        assert "scope" in focus_context
        assert "validation_criteria" in focus_context
        
        # Verify current task is set
        assert executor.current_task is not None
        assert executor.current_task["id"] == task_id
    
    def test_get_task_context(self):
        """Test getting complete task execution context."""
        executor = self._setup_executor()
        executor.create(self.feature_name)
        executor.load_execution_context()
        
        # Get task context
        task_id = "2.1"
        task_context = executor.get_task_context(task_id)
        
        # Verify complete context
        assert task_context["task"]["id"] == task_id
        assert "requirements_document" in task_context
        assert "design_document" in task_context
        assert "all_tasks" in task_context
        assert "feature_metadata" in task_context
    
    def test_context_loading_error_handling(self):
        """Test error handling in context loading."""
        # Create executor with non-existent feature
        executor = TaskExecutor("non-existent-feature")
        executor.spec_manager.base_path = Path(self.temp_dir) / ".kiro" / "specs"
        
        # Test loading context without specification
        with pytest.raises(WorkflowError):
            executor.load_execution_context()
        
        # Test with missing documents
        executor.create(self.feature_name)
        (self.spec_dir / "requirements.md").unlink()
        
        with pytest.raises(WorkflowError):
            executor.load_execution_context()


class TestTaskValidator(TestTaskExecutionFramework):
    """Test TaskValidator component."""
    
    def test_validate_content(self):
        """Test basic content validation."""
        validator = self._setup_validator()
        
        # Test empty content
        result = validator.validate("")
        assert result.is_valid is False
        assert "No implementation content provided" in result.issues
        
        # Test valid code content
        code_content = """
def test_function():
    '''Test function with proper structure.'''
    return True
"""
        result = validator.validate(code_content)
        assert result.is_valid is True
    
    def test_validate_task_implementation(self):
        """Test complete task implementation validation."""
        validator = self._setup_validator()
        
        # Mock task context loading
        with patch.object(validator, '_load_task_context') as mock_load:
            mock_load.return_value = {
                "task_id": "2.1",
                "requirements": [{"id": "1.1", "acceptance_criteria": ["Test criteria"]}],
                "scope": {"deliverables": ["Implementation", "Tests"]},
            }
            
            # Test implementation
            implementation = {
                "code": "def implementation(): pass",
                "addresses_requirements": True,
                "deliverables": ["Implementation"],
                "summary": "Basic implementation",
            }
            
            result = validator.validate_task_implementation("2.1", implementation)
            assert isinstance(result, ValidationResult)
    
    def test_check_completion_status(self):
        """Test task completion status checking."""
        validator = self._setup_validator()
        
        # Mock task context and validation
        with patch.object(validator, '_load_task_context') as mock_load, \
             patch.object(validator, 'validate_task_implementation') as mock_validate:
            
            mock_load.return_value = {"task_id": "2.1"}
            mock_validate.return_value = ValidationResult(True, [], [])
            
            implementation = {"code": "test implementation"}
            status = validator.check_completion_status("2.1", implementation)
            
            assert status["task_id"] == "2.1"
            assert status["status"] == TaskStatus.COMPLETED.value
            assert status["completion_percentage"] == 100
            assert status["is_valid"] is True
    
    def test_track_task_status(self):
        """Test task status tracking."""
        validator = self._setup_validator()
        
        # Track status changes
        result = validator.track_task_status("2.1", TaskStatus.IN_PROGRESS, "Started implementation")
        assert result is True
        
        result = validator.track_task_status("2.1", TaskStatus.COMPLETED, "Implementation finished")
        assert result is True
        
        # Verify tracking state
        tracking_state = validator._load_tracking_state()
        assert "2.1" in tracking_state["task_statuses"]
        assert len(tracking_state["task_statuses"]["2.1"]) == 2
    
    def test_provide_feedback(self):
        """Test comprehensive feedback provision."""
        validator = self._setup_validator()
        
        # Mock dependencies
        with patch.object(validator, 'validate_task_implementation') as mock_validate, \
             patch.object(validator, 'check_completion_status') as mock_status:
            
            mock_validate.return_value = ValidationResult(True, [], ["Consider adding tests"])
            mock_status.return_value = {
                "status": TaskStatus.COMPLETED.value,
                "completion_percentage": 90,
            }
            
            implementation = {"code": "implementation"}
            feedback = validator.provide_feedback("2.1", implementation)
            
            assert feedback["task_id"] == "2.1"
            assert "overall_assessment" in feedback
            assert "specific_suggestions" in feedback
            assert "quality_score" in feedback


class TestTaskProgressionController(TestTaskExecutionFramework):
    """Test TaskProgressionController component."""
    
    def test_create_progression_control(self):
        """Test creating progression control context."""
        controller = self._setup_progression_controller()
        
        result = controller.create(self.feature_name)
        assert result is True
        
        # Verify progression state
        state = controller.load(self.feature_name)
        assert state is not None
        assert state["feature_name"] == self.feature_name
        assert state["auto_progression_disabled"] is True
    
    def test_request_task_review(self):
        """Test requesting user review for completed task."""
        controller = self._setup_progression_controller()
        controller.create(self.feature_name)
        
        # Mock validator methods
        with patch.object(controller.task_validator, 'validate_task_implementation') as mock_validate, \
             patch.object(controller.task_validator, 'provide_feedback') as mock_feedback:
            
            mock_validate.return_value = ValidationResult(True, [], [])
            mock_feedback.return_value = {"overall_assessment": "Good implementation"}
            
            implementation = {"code": "test implementation"}
            review_request = controller.request_task_review("2.1", implementation)
            
            assert review_request["task_id"] == "2.1"
            assert review_request["review_status"] == "pending"
            assert review_request["requires_user_approval"] is True
            
            # Verify review was added to pending
            state = controller.load(self.feature_name)
            assert len(state["pending_reviews"]) == 1
    
    def test_process_user_review(self):
        """Test processing user review decisions."""
        controller = self._setup_progression_controller()
        controller.create(self.feature_name)
        
        # Add pending review
        with patch.object(controller.task_validator, 'validate_task_implementation'), \
             patch.object(controller.task_validator, 'provide_feedback'):
            
            controller.request_task_review("2.1", {"code": "test"})
        
        # Test approval
        result = controller.process_user_review("2.1", "approved", "Looks good")
        assert result["success"] is True
        assert result["decision"] == "approved"
        
        # Verify task was marked completed
        state = controller.load(self.feature_name)
        assert "2.1" in state["completed_tasks"]
        assert len(state["pending_reviews"]) == 0
    
    def test_get_progression_status(self):
        """Test getting progression status report."""
        controller = self._setup_progression_controller()
        controller.create(self.feature_name)
        
        # Mock total task count
        with patch.object(controller, '_get_total_task_count', return_value=5):
            status = controller.get_progression_status()
            
            assert status["feature_name"] == self.feature_name
            assert status["completed_tasks_count"] == 0
            assert status["total_tasks_count"] == 5
            assert status["completion_percentage"] == 0.0
            assert status["auto_progression_enabled"] is False
    
    def test_prevent_auto_progression(self):
        """Test ensuring auto-progression is disabled."""
        controller = self._setup_progression_controller()
        controller.create(self.feature_name)
        
        result = controller.prevent_auto_progression()
        assert result is True
        
        # Verify auto-progression is disabled
        state = controller.load(self.feature_name)
        assert state["auto_progression_disabled"] is True
        assert state["auto_progression_policy"] == "manual_only"
    
    def test_create_task_report(self):
        """Test creating comprehensive task reports."""
        controller = self._setup_progression_controller()
        controller.create(self.feature_name)
        
        # Add some task history
        controller.task_validator.track_task_status("2.1", TaskStatus.IN_PROGRESS)
        controller.task_validator.track_task_status("2.1", TaskStatus.COMPLETED)
        
        report = controller.create_task_report("2.1")
        
        assert report["task_id"] == "2.1"
        assert "status_history" in report
        assert "validation_history" in report
        assert "current_status" in report
        assert "time_spent" in report


class TestEndToEndWorkflow(TestTaskExecutionFramework):
    """Test complete end-to-end task execution workflow."""
    
    def test_complete_task_execution_workflow(self):
        """Test complete workflow from context loading to task completion."""
        # Set up all components
        executor = self._setup_executor()
        validator = self._setup_validator()
        controller = self._setup_progression_controller()
        
        # Step 1: Create execution context
        executor.create(self.feature_name)
        controller.create(self.feature_name)
        
        # Step 2: Load and validate context
        context = executor.load_execution_context()
        validation_result = executor.validate_context()
        assert validation_result.is_valid is True
        
        # Step 3: Focus on specific task
        task_id = "2.1"
        task_context = executor.get_task_context(task_id)
        assert task_context["task"]["id"] == task_id
        
        # Step 4: Implement task (simulated)
        implementation = {
            "code": """
def load_task_context():
    '''Load requirements, design, and task documents.'''
    return {"requirements": [], "design": {}, "tasks": []}
""",
            "addresses_requirements": True,
            "deliverables": ["Implementation"],
            "has_tests": False,
            "summary": "Implemented task context loading functionality",
        }
        
        # Step 5: Validate implementation
        with patch.object(validator, '_load_task_context') as mock_load:
            mock_load.return_value = {
                "task_id": task_id,
                "requirements": [{"id": "1.1", "acceptance_criteria": ["Load context"]}],
                "scope": {"deliverables": ["Implementation"]},
            }
            
            validation_result = validator.validate_task_implementation(task_id, implementation)
            assert validation_result.is_valid is True
        
        # Step 6: Request user review
        with patch.object(controller.task_validator, 'validate_task_implementation') as mock_validate, \
             patch.object(controller.task_validator, 'provide_feedback') as mock_feedback:
            
            mock_validate.return_value = ValidationResult(True, [], ["Consider adding tests"])
            mock_feedback.return_value = {
                "overall_assessment": "Good implementation",
                "quality_score": 85,
            }
            
            review_request = controller.request_task_review(task_id, implementation)
            assert review_request["review_status"] == "pending"
        
        # Step 7: Process user approval
        review_result = controller.process_user_review(task_id, "approved", "Implementation looks good")
        assert review_result["success"] is True
        
        # Step 8: Verify task completion
        status = controller.get_progression_status()
        assert task_id in status["pending_reviews"] or len(status["pending_reviews"]) == 0
        
        # Step 9: Generate task report
        report = controller.create_task_report(task_id)
        assert report["task_id"] == task_id
    
    def test_workflow_with_revision_cycle(self):
        """Test workflow with task revision and resubmission."""
        controller = self._setup_progression_controller()
        controller.create(self.feature_name)
        
        task_id = "2.2"
        implementation = {"code": "incomplete implementation"}
        
        # Mock validation to show issues
        with patch.object(controller.task_validator, 'validate_task_implementation') as mock_validate, \
             patch.object(controller.task_validator, 'provide_feedback') as mock_feedback:
            
            mock_validate.return_value = ValidationResult(False, ["Missing tests"], ["Add unit tests"])
            mock_feedback.return_value = {"overall_assessment": "Needs improvement"}
            
            # Request review
            review_request = controller.request_task_review(task_id, implementation)
            assert review_request["validation_result"]["is_valid"] is False
            
            # User requests revision
            review_result = controller.process_user_review(task_id, "needs_revision", "Please add tests")
            assert review_result["success"] is True
            assert review_result["next_action"] == "Address feedback and resubmit for review"
            
            # Verify task is still in progress
            state = controller.load(self.feature_name)
            assert task_id not in state.get("completed_tasks", [])
    
    def test_workflow_error_scenarios(self):
        """Test workflow behavior in error scenarios."""
        executor = self._setup_executor()
        
        # Test context loading without specification
        with pytest.raises(WorkflowError):
            executor.load_execution_context()
        
        # Test focusing on non-existent task
        executor.create(self.feature_name)
        executor.load_execution_context()
        
        with pytest.raises(WorkflowError):
            executor.focus_on_task("non-existent-task")
        
        # Test validation with invalid implementation
        validator = self._setup_validator()
        result = validator.validate("")
        assert result.is_valid is False
        assert len(result.issues) > 0
    
    def test_context_validation_comprehensive(self):
        """Test comprehensive context validation scenarios."""
        executor = self._setup_executor()
        executor.create(self.feature_name)
        
        # Test with complete valid context
        context = executor.load_execution_context()
        validation = executor.validate_context()
        assert validation.is_valid is True
        
        # Test validation with missing requirements
        executor.context_cache["requirements"] = []
        validation = executor.validate_context()
        # Should still be valid as we have other required elements
        
        # Test validation with invalid task structure
        executor.context_cache["tasks"] = [{"invalid": "task"}]
        validation = executor.validate_context()
        assert validation.is_valid is False
        assert any("Invalid task structure" in issue for issue in validation.issues)
    
    def test_user_review_and_progression_control(self):
        """Test comprehensive user review and progression control."""
        controller = self._setup_progression_controller()
        controller.create(self.feature_name)
        
        # Ensure auto-progression is disabled
        assert controller.prevent_auto_progression() is True
        
        # Test multiple task reviews
        task_ids = ["1", "2.1", "2.2"]
        
        for task_id in task_ids:
            with patch.object(controller.task_validator, 'validate_task_implementation'), \
                 patch.object(controller.task_validator, 'provide_feedback'):
                
                # Request review
                controller.request_task_review(task_id, {"code": f"implementation for {task_id}"})
        
        # Verify all reviews are pending
        status = controller.get_progression_status()
        assert status["pending_reviews_count"] == 3
        
        # Process reviews with different outcomes
        controller.process_user_review("1", "approved", "Good work")
        controller.process_user_review("2.1", "rejected", "Needs complete rework")
        controller.process_user_review("2.2", "needs_revision", "Minor fixes needed")
        
        # Verify final state
        final_status = controller.get_progression_status()
        assert final_status["completed_tasks_count"] == 1  # Only task "1" approved
        assert final_status["pending_reviews_count"] == 1  # Task "2.2" still pending revision