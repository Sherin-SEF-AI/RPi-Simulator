"""
Integration tests for Workflow Controller.

Tests complete workflow from requirements to tasks, phase transitions,
approval mechanisms, and feedback handling.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from packages.feature_planning.workflow_controller import WorkflowController
from packages.feature_planning.base import WorkflowPhase, WorkflowError


class TestWorkflowController:
    """Test suite for WorkflowController integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.feature_name = "test-feature"
        
        # Create .kiro/specs directory structure
        self.spec_dir = Path(self.temp_dir) / ".kiro" / "specs" / self.feature_name
        self.spec_dir.mkdir(parents=True, exist_ok=True)
        
        # Patch the workflow controller to use temp directory
        self.original_cwd = Path.cwd()
        
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def _setup_controller(self):
        """Helper to set up controller with correct paths."""
        controller = WorkflowController(self.feature_name)
        controller.workflow_state_file = self.spec_dir / "workflow_state.json"
        return controller
    
    def test_create_workflow(self):
        """Test workflow creation."""
        controller = self._setup_controller()
        
        # Test workflow creation
        result = controller.create(self.feature_name)
        assert result is True
        assert controller.current_phase == WorkflowPhase.REQUIREMENTS
        assert controller.phase_history == []
        assert controller.approval_status == {}
        
        # Check workflow state file was created
        workflow_file = self.spec_dir / "workflow_state.json"
        assert workflow_file.exists()
    
    def test_load_workflow(self):
        """Test workflow loading."""
        # Create and save initial workflow
        controller = self._setup_controller()
        controller.create(self.feature_name)
        controller.current_phase = WorkflowPhase.DESIGN
        controller.approval_status[WorkflowPhase.REQUIREMENTS] = True
        controller._save_workflow_state()
        
        # Load workflow in new controller instance
        new_controller = self._setup_controller()
        result = new_controller.load(self.feature_name)
        
        assert result is not None
        assert result["current_phase"] == "design"
        assert result["approval_status"]["requirements"] is True
        assert new_controller.current_phase == WorkflowPhase.DESIGN
    
    def test_phase_transitions(self):
        """Test phase transition validation and execution."""
        controller = self._setup_controller()
        controller.create(self.feature_name)
        
        # Create required documents
        (self.spec_dir / "requirements.md").write_text("# Requirements")
        (self.spec_dir / "design.md").write_text("# Design")
        
        # Test valid transition with approval
        controller.approval_status[WorkflowPhase.REQUIREMENTS] = True
        result = controller.transition_phase(WorkflowPhase.REQUIREMENTS, WorkflowPhase.DESIGN)
        assert result is True
        assert controller.current_phase == WorkflowPhase.DESIGN
        assert WorkflowPhase.REQUIREMENTS in controller.phase_history
        
        # Test invalid transition without approval
        controller.current_phase = WorkflowPhase.REQUIREMENTS
        controller.approval_status[WorkflowPhase.REQUIREMENTS] = False
        
        with pytest.raises(WorkflowError):
            controller.transition_phase(WorkflowPhase.REQUIREMENTS, WorkflowPhase.DESIGN)
    
    def test_approval_system(self):
        """Test approval request and handling system."""
        controller = self._setup_controller()
        controller.create(self.feature_name)
        
        # Create requirements document
        (self.spec_dir / "requirements.md").write_text("# Requirements")
        
        # Test approval request
        result = controller.request_approval(WorkflowPhase.REQUIREMENTS)
        assert result is True
        assert controller.approval_status[WorkflowPhase.REQUIREMENTS] is True
        
        # Test approval request without required document
        result = controller.request_approval(WorkflowPhase.DESIGN)
        assert result is False
    
    def test_feedback_handling(self):
        """Test feedback processing and action planning."""
        controller = self._setup_controller()
        controller.create(self.feature_name)
        
        # Test approval feedback
        result = controller.handle_feedback("yes, looks good")
        assert result["action"] == "approve"
        assert result["phase"] == "requirements"
        
        # Test revision feedback
        result = controller.handle_feedback("no, changes needed")
        assert result["action"] == "revise"
        assert result["phase"] == "requirements"
        
        # Test return to previous phase feedback
        controller.current_phase = WorkflowPhase.DESIGN
        result = controller.handle_feedback("let's go back to requirements")
        assert result["action"] == "return_to_phase"
        assert result["target_phase"] == "requirements"
        
        # Test general iteration feedback
        result = controller.handle_feedback("please update the user stories")
        assert result["action"] == "iterate"
        assert "feedback" in result
    
    def test_return_to_previous_phase(self):
        """Test return to previous phase functionality."""
        controller = self._setup_controller()
        controller.create(self.feature_name)
        
        # Set up workflow in tasks phase
        controller.current_phase = WorkflowPhase.TASKS
        controller.approval_status[WorkflowPhase.REQUIREMENTS] = True
        controller.approval_status[WorkflowPhase.DESIGN] = True
        controller.approval_status[WorkflowPhase.TASKS] = True
        
        # Return to design phase
        result = controller.return_to_phase(WorkflowPhase.DESIGN, "Need to update design")
        assert result is True
        assert controller.current_phase == WorkflowPhase.DESIGN
        
        # Check that subsequent approvals were cleared
        assert controller.approval_status[WorkflowPhase.TASKS] is False
        assert controller.approval_status[WorkflowPhase.DESIGN] is True  # Should remain
        assert controller.approval_status[WorkflowPhase.REQUIREMENTS] is True  # Should remain
    
    def test_document_consistency_maintenance(self):
        """Test document consistency checking across iterations."""
        controller = self._setup_controller()
        controller.create(self.feature_name)
        
        # Test with missing documents
        controller.current_phase = WorkflowPhase.DESIGN
        report = controller.maintain_document_consistency()
        assert report["is_consistent"] is False
        assert "Missing documents" in report["issues"][0]
        
        # Create required documents
        (self.spec_dir / "requirements.md").write_text("# Requirements")
        (self.spec_dir / "design.md").write_text("# Design")
        
        # Test with unapproved previous phases
        report = controller.maintain_document_consistency()
        assert report["is_consistent"] is False
        assert "Unapproved previous phases" in report["issues"][0]
        
        # Approve previous phases
        controller.approval_status[WorkflowPhase.REQUIREMENTS] = True
        
        # Test consistent state
        report = controller.maintain_document_consistency()
        assert report["is_consistent"] is True
        assert len(report["issues"]) == 0
    
    def test_complete_workflow_cycle(self):
        """Test complete workflow from requirements to tasks."""
        controller = self._setup_controller()
        controller.create(self.feature_name)
        
        # Create all required documents
        (self.spec_dir / "requirements.md").write_text("# Requirements")
        (self.spec_dir / "design.md").write_text("# Design")
        (self.spec_dir / "tasks.md").write_text("# Tasks")
        
        # Requirements phase
        assert controller.current_phase == WorkflowPhase.REQUIREMENTS
        controller.request_approval(WorkflowPhase.REQUIREMENTS)
        assert controller.approval_status[WorkflowPhase.REQUIREMENTS] is True
        
        # Transition to design
        controller.transition_phase(WorkflowPhase.REQUIREMENTS, WorkflowPhase.DESIGN)
        assert controller.current_phase == WorkflowPhase.DESIGN
        
        # Design phase
        controller.request_approval(WorkflowPhase.DESIGN)
        assert controller.approval_status[WorkflowPhase.DESIGN] is True
        
        # Transition to tasks
        controller.transition_phase(WorkflowPhase.DESIGN, WorkflowPhase.TASKS)
        assert controller.current_phase == WorkflowPhase.TASKS
        
        # Tasks phase
        controller.request_approval(WorkflowPhase.TASKS)
        assert controller.approval_status[WorkflowPhase.TASKS] is True
        
        # Verify complete workflow state
        assert len(controller.phase_history) == 2
        assert all(phase in controller.approval_status for phase in [
            WorkflowPhase.REQUIREMENTS, WorkflowPhase.DESIGN, WorkflowPhase.TASKS
        ])
    
    def test_workflow_error_handling(self):
        """Test error handling in workflow operations."""
        controller = self._setup_controller()
        controller.create(self.feature_name)
        
        # Test invalid phase transition
        with pytest.raises(WorkflowError):
            controller.transition_phase(WorkflowPhase.REQUIREMENTS, WorkflowPhase.EXECUTION)
        
        # Test transition from wrong current phase
        controller.current_phase = WorkflowPhase.DESIGN
        with pytest.raises(WorkflowError):
            controller.transition_phase(WorkflowPhase.REQUIREMENTS, WorkflowPhase.DESIGN)
        
        # Test invalid return to phase
        controller.current_phase = WorkflowPhase.REQUIREMENTS
        with pytest.raises(WorkflowError):
            controller.return_to_phase(WorkflowPhase.DESIGN, "Invalid return")
    
    def test_workflow_state_persistence(self):
        """Test workflow state persistence across sessions."""
        # Create and modify workflow
        controller1 = self._setup_controller()
        controller1.create(self.feature_name)
        controller1.current_phase = WorkflowPhase.DESIGN
        controller1.approval_status[WorkflowPhase.REQUIREMENTS] = True
        controller1.phase_history = [WorkflowPhase.REQUIREMENTS]
        controller1._save_workflow_state()
        
        # Load workflow in new instance
        controller2 = self._setup_controller()
        state = controller2.load(self.feature_name)
        
        # Verify state was preserved
        assert controller2.current_phase == WorkflowPhase.DESIGN
        assert controller2.approval_status[WorkflowPhase.REQUIREMENTS] is True
        assert WorkflowPhase.REQUIREMENTS in controller2.phase_history
        
        # Test update workflow state
        new_state = {
            "current_phase": "tasks",
            "phase_history": ["requirements", "design"],
            "approval_status": {"requirements": True, "design": True}
        }
        
        result = controller2.update(self.feature_name, new_state)
        assert result is True
        assert controller2.current_phase == WorkflowPhase.TASKS
        assert controller2.approval_status[WorkflowPhase.DESIGN] is True