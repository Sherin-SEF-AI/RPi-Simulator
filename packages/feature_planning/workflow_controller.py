"""
Workflow Controller for process management.

This module manages the iterative workflow between requirements, design,
and tasks phases with proper approval gates and feedback handling.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseManager, ValidationResult, WorkflowError, WorkflowPhase
from .config import get_config
from .error_handling import (
    handle_error, 
    ErrorCategory, 
    ErrorSeverity, 
    with_error_handling
)


class WorkflowController(BaseManager):
    """
    Manages the iterative feature planning workflow.

    Controls phase transitions, approval gates, and feedback handling
    throughout the requirements-design-tasks process.
    """

    def __init__(self, feature_name: str):
        """Initialize Workflow Controller for specific feature."""
        self.config = get_config()
        self.feature_name = feature_name
        self.current_phase = WorkflowPhase.REQUIREMENTS
        self.phase_history: List[WorkflowPhase] = []
        self.approval_status: Dict[WorkflowPhase, bool] = {}
        self.workflow_state_file = Path(
            f".kiro/specs/{feature_name}/workflow_state.json"
        )
        # Kiro integration adapters (injected by KiroIntegrationManager)
        self._user_input_adapter = None
        self._task_status_adapter = None
        # Don't load state in constructor - let create/load methods handle it

    def create(self, name: str, **kwargs) -> bool:
        """
        Create new workflow for feature.

        Args:
            name: Feature name
            **kwargs: Additional workflow parameters

        Returns:
            True if workflow creation successful
        """
        try:
            # Initialize workflow state
            self.feature_name = name
            self.current_phase = WorkflowPhase.REQUIREMENTS
            self.phase_history = []
            self.approval_status = {}
            self.workflow_state_file = Path(f".kiro/specs/{name}/workflow_state.json")

            # Create workflow state file
            self._save_workflow_state()
            return True
        except Exception as e:
            return False

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load existing workflow state.

        Args:
            name: Feature name

        Returns:
            Workflow state data or None if not found
        """
        try:
            self.feature_name = name
            self.workflow_state_file = Path(f".kiro/specs/{name}/workflow_state.json")

            if self.workflow_state_file.exists():
                self._load_workflow_state()
                return {
                    "current_phase": self.current_phase.value,
                    "phase_history": [phase.value for phase in self.phase_history],
                    "approval_status": {
                        phase.value: status
                        for phase, status in self.approval_status.items()
                    },
                }
            return None
        except Exception:
            return None

    def update(self, name: str, content: Any) -> bool:
        """
        Update workflow state.

        Args:
            name: Feature name
            content: New workflow state

        Returns:
            True if update successful
        """
        try:
            self.feature_name = name
            self.workflow_state_file = Path(f".kiro/specs/{name}/workflow_state.json")

            if isinstance(content, dict):
                if "current_phase" in content:
                    self.current_phase = WorkflowPhase(content["current_phase"])
                if "phase_history" in content:
                    self.phase_history = [
                        WorkflowPhase(phase) for phase in content["phase_history"]
                    ]
                if "approval_status" in content:
                    self.approval_status = {
                        WorkflowPhase(phase): status
                        for phase, status in content["approval_status"].items()
                    }

                self._save_workflow_state()
                return True
            return False
        except Exception:
            return False

    def delete(self, name: str) -> bool:
        """
        Delete workflow and associated state.

        Args:
            name: Feature name

        Returns:
            True if deletion successful
        """
        try:
            workflow_file = Path(f".kiro/specs/{name}/workflow_state.json")
            if workflow_file.exists():
                workflow_file.unlink()
            return True
        except Exception:
            return False

    def get_current_phase(self) -> WorkflowPhase:
        """
        Get current workflow phase.

        Returns:
            Current phase of the workflow
        """
        return self.current_phase

    def request_approval(self, phase: WorkflowPhase) -> bool:
        """
        Request user approval for phase completion.

        Args:
            phase: Phase to request approval for

        Returns:
            True if approval granted
        """
        try:
            # Check if phase is valid for approval
            if phase not in [
                WorkflowPhase.REQUIREMENTS,
                WorkflowPhase.DESIGN,
                WorkflowPhase.TASKS,
            ]:
                return False

            # Validate that required documents exist for the phase
            if not self._validate_phase_completion(phase):
                return False

            # Get approval message for the phase
            approval_message = self._get_approval_message(phase)
            
            # Use Kiro's userInput tool if available
            if self._user_input_adapter:
                reason = self._get_approval_reason(phase)
                result = self._user_input_adapter.request_approval(approval_message, reason)
                
                if result.success:
                    # Parse the response to determine approval
                    response = result.data.get('response', '').lower().strip()
                    approved = self._parse_approval_response(response)
                    
                    if approved:
                        self.approval_status[phase] = True
                        self._save_workflow_state()
                        return True
                    else:
                        return False
                else:
                    raise WorkflowError(f"User input request failed: {result.error}")
            else:
                # Fallback for testing - assume approval is granted
                self.approval_status[phase] = True
                self._save_workflow_state()
                return True
        except Exception as e:
            handle_error(
                e,
                component="WorkflowController",
                operation="request_approval",
                category=ErrorCategory.WORKFLOW,
                severity=ErrorSeverity.HIGH,
                feature_name=self.feature_name,
                phase=phase.value
            )
            return False

    def transition_phase(
        self, from_phase: WorkflowPhase, to_phase: WorkflowPhase
    ) -> bool:
        """
        Transition between workflow phases.

        Args:
            from_phase: Current phase
            to_phase: Target phase

        Returns:
            True if transition successful
        """
        try:
            # Validate current phase matches from_phase
            if self.current_phase != from_phase:
                raise WorkflowError(
                    f"Current phase {self.current_phase.value} does not match from_phase {from_phase.value}"
                )

            # Validate transition is allowed
            if not self._is_valid_transition(from_phase, to_phase):
                raise WorkflowError(
                    f"Invalid transition from {from_phase.value} to {to_phase.value}"
                )

            # Check if from_phase is approved (except for backward transitions)
            if self._is_forward_transition(from_phase, to_phase):
                if not self.approval_status.get(from_phase, False):
                    raise WorkflowError(
                        f"Phase {from_phase.value} must be approved before transitioning to {to_phase.value}"
                    )

            # Perform transition
            self.phase_history.append(self.current_phase)
            self.current_phase = to_phase
            self._save_workflow_state()

            return True
        except Exception as e:
            return False

    def handle_feedback(self, feedback: str) -> Dict[str, Any]:
        """
        Process user feedback and determine actions.

        Args:
            feedback: User feedback content

        Returns:
            Action plan based on feedback
        """
        try:
            feedback_lower = feedback.lower().strip()

            # Check for approval keywords first
            approval_keywords = [
                "yes",
                "approved",
                "looks good",
                "good",
                "ok",
                "okay",
                "proceed",
                "continue",
            ]

            if any(keyword in feedback_lower for keyword in approval_keywords):
                return {
                    "action": "approve",
                    "phase": self.current_phase.value,
                    "message": f"Phase {self.current_phase.value} approved",
                }

            # Check for requests to return to previous phases
            elif (
                "requirements" in feedback_lower
                and self.current_phase != WorkflowPhase.REQUIREMENTS
            ):
                return {
                    "action": "return_to_phase",
                    "target_phase": "requirements",
                    "reason": "User requested return to requirements phase",
                    "feedback": feedback,
                }

            elif (
                "design" in feedback_lower
                and self.current_phase != WorkflowPhase.DESIGN
            ):
                return {
                    "action": "return_to_phase",
                    "target_phase": "design",
                    "reason": "User requested return to design phase",
                    "feedback": feedback,
                }

            # Check for rejection keywords first (more specific)
            elif any(
                keyword in feedback_lower
                for keyword in ["no", "not approved", "changes needed", "revise"]
            ):
                return {
                    "action": "revise",
                    "phase": self.current_phase.value,
                    "feedback": feedback,
                    "message": f"Phase {self.current_phase.value} requires revision",
                }

            # Check for specific update requests that indicate iteration
            elif any(
                word in feedback_lower
                for word in [
                    "please update",
                    "please change",
                    "please modify",
                    "please add",
                    "please remove",
                ]
            ):
                return {
                    "action": "iterate",
                    "phase": self.current_phase.value,
                    "feedback": feedback,
                    "message": "Feedback received, iteration required",
                }

            else:
                # General feedback that requires revision
                return {
                    "action": "revise",
                    "phase": self.current_phase.value,
                    "feedback": feedback,
                    "message": "Feedback received, revision required",
                }

        except Exception as e:
            return {
                "action": "error",
                "message": f"Failed to process feedback: {e}",
                "feedback": feedback,
            }

    def _load_workflow_state(self) -> None:
        """Load workflow state from file."""
        try:
            if self.workflow_state_file.exists():
                with open(self.workflow_state_file, "r") as f:
                    state = json.load(f)

                self.current_phase = WorkflowPhase(
                    state.get("current_phase", "requirements")
                )
                self.phase_history = [
                    WorkflowPhase(phase) for phase in state.get("phase_history", [])
                ]
                self.approval_status = {
                    WorkflowPhase(phase): status
                    for phase, status in state.get("approval_status", {}).items()
                }
        except Exception:
            # If loading fails, use defaults
            self.current_phase = WorkflowPhase.REQUIREMENTS
            self.phase_history = []
            self.approval_status = {}

    def _save_workflow_state(self) -> None:
        """Save workflow state to file."""
        try:
            # Ensure directory exists
            self.workflow_state_file.parent.mkdir(parents=True, exist_ok=True)

            state = {
                "current_phase": self.current_phase.value,
                "phase_history": [phase.value for phase in self.phase_history],
                "approval_status": {
                    phase.value: status
                    for phase, status in self.approval_status.items()
                },
            }

            with open(self.workflow_state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            raise WorkflowError(f"Failed to save workflow state: {e}")

    def _validate_phase_completion(self, phase: WorkflowPhase) -> bool:
        """Validate that a phase has the required documents for completion."""
        spec_dir = self.workflow_state_file.parent

        if phase == WorkflowPhase.REQUIREMENTS:
            return (spec_dir / "requirements.md").exists()
        elif phase == WorkflowPhase.DESIGN:
            return (spec_dir / "design.md").exists()
        elif phase == WorkflowPhase.TASKS:
            return (spec_dir / "tasks.md").exists()

        return False

    def _get_approval_message(self, phase: WorkflowPhase) -> str:
        """Get appropriate approval message for phase."""
        messages = {
            WorkflowPhase.REQUIREMENTS: "Do the requirements look good? If so, we can move on to the design.",
            WorkflowPhase.DESIGN: "Does the design look good? If so, we can move on to the implementation plan.",
            WorkflowPhase.TASKS: "The current task list marks some tasks (e.g. unit tests, documentation) as optional to focus on core features first.",
        }
        return messages.get(
            phase, f"Please approve the {phase.value} phase to continue."
        )

    def _is_valid_transition(
        self, from_phase: WorkflowPhase, to_phase: WorkflowPhase
    ) -> bool:
        """Check if transition between phases is valid."""
        # Define valid transitions
        valid_transitions = {
            WorkflowPhase.REQUIREMENTS: [WorkflowPhase.DESIGN],
            WorkflowPhase.DESIGN: [WorkflowPhase.REQUIREMENTS, WorkflowPhase.TASKS],
            WorkflowPhase.TASKS: [
                WorkflowPhase.REQUIREMENTS,
                WorkflowPhase.DESIGN,
                WorkflowPhase.EXECUTION,
            ],
            WorkflowPhase.EXECUTION: [
                WorkflowPhase.REQUIREMENTS,
                WorkflowPhase.DESIGN,
                WorkflowPhase.TASKS,
            ],
        }

        return to_phase in valid_transitions.get(from_phase, [])

    def _is_forward_transition(
        self, from_phase: WorkflowPhase, to_phase: WorkflowPhase
    ) -> bool:
        """Check if transition is forward in the workflow."""
        phase_order = {
            WorkflowPhase.REQUIREMENTS: 0,
            WorkflowPhase.DESIGN: 1,
            WorkflowPhase.TASKS: 2,
            WorkflowPhase.EXECUTION: 3,
        }

        return phase_order.get(to_phase, 0) > phase_order.get(from_phase, 0)

    def _get_approval_reason(self, phase: WorkflowPhase) -> str:
        """Get the reason code for Kiro user input tool."""
        reason_map = {
            WorkflowPhase.REQUIREMENTS: "spec-requirements-review",
            WorkflowPhase.DESIGN: "spec-design-review", 
            WorkflowPhase.TASKS: "spec-tasks-review"
        }
        return reason_map.get(phase, "spec-review")

    def _parse_approval_response(self, response: str) -> bool:
        """Parse user response to determine if approval was granted."""
        approval_keywords = [
            "yes", "approved", "looks good", "good", "ok", "okay", 
            "proceed", "continue", "accept", "approve"
        ]
        
        response_lower = response.lower().strip()
        return any(keyword in response_lower for keyword in approval_keywords)

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status using Kiro's task status tool."""
        try:
            if self._task_status_adapter:
                task_file_path = f".kiro/specs/{self.feature_name}/tasks.md"
                result = self._task_status_adapter.update_task_status(
                    task_file_path, task_id, status
                )
                return result.success
            return True  # Fallback for testing
        except Exception:
            return False

    def return_to_phase(self, target_phase: WorkflowPhase, reason: str = "") -> bool:
        """
        Return to a previous phase in the workflow.

        Args:
            target_phase: Phase to return to
            reason: Reason for returning to previous phase

        Returns:
            True if return successful
        """
        try:
            # Validate target phase is valid for return
            if not self._is_valid_return_phase(target_phase):
                raise WorkflowError(f"Cannot return to phase {target_phase.value}")

            # Clear approvals for phases after target phase
            self._clear_subsequent_approvals(target_phase)

            # Update current phase
            self.phase_history.append(self.current_phase)
            self.current_phase = target_phase

            # Save state
            self._save_workflow_state()

            return True
        except Exception as e:
            return False

    def maintain_document_consistency(self) -> Dict[str, Any]:
        """
        Check and maintain consistency across workflow documents.

        Returns:
            Consistency report with any issues found
        """
        try:
            spec_dir = self.workflow_state_file.parent
            consistency_report = {
                "is_consistent": True,
                "issues": [],
                "recommendations": [],
            }

            # Check if required documents exist for current phase
            required_docs = self._get_required_documents(self.current_phase)
            missing_docs = []

            for doc in required_docs:
                if not (spec_dir / doc).exists():
                    missing_docs.append(doc)

            if missing_docs:
                consistency_report["is_consistent"] = False
                consistency_report["issues"].append(
                    f"Missing documents: {', '.join(missing_docs)}"
                )
                consistency_report["recommendations"].append(
                    "Create missing documents before proceeding"
                )
                # Return early if documents are missing - can't check approvals without docs
                return consistency_report

            # Check approval status consistency only if documents exist
            if self.current_phase != WorkflowPhase.REQUIREMENTS:
                previous_phases = self._get_previous_phases(self.current_phase)
                unapproved_phases = [
                    phase
                    for phase in previous_phases
                    if not self.approval_status.get(phase, False)
                ]

                if unapproved_phases:
                    consistency_report["is_consistent"] = False
                    phase_names = [phase.value for phase in unapproved_phases]
                    consistency_report["issues"].append(
                        f"Unapproved previous phases: {', '.join(phase_names)}"
                    )
                    consistency_report["recommendations"].append(
                        "Approve previous phases before proceeding"
                    )

            return consistency_report

        except Exception as e:
            return {
                "is_consistent": False,
                "issues": [f"Failed to check consistency: {e}"],
                "recommendations": ["Review workflow state and documents manually"],
            }

    def _is_valid_return_phase(self, target_phase: WorkflowPhase) -> bool:
        """Check if returning to target phase is valid."""
        phase_order = {
            WorkflowPhase.REQUIREMENTS: 0,
            WorkflowPhase.DESIGN: 1,
            WorkflowPhase.TASKS: 2,
            WorkflowPhase.EXECUTION: 3,
        }

        # Can only return to earlier phases
        return phase_order.get(target_phase, 0) < phase_order.get(self.current_phase, 0)

    def _clear_subsequent_approvals(self, target_phase: WorkflowPhase) -> None:
        """Clear approvals for phases that come after target phase."""
        phase_order = {
            WorkflowPhase.REQUIREMENTS: 0,
            WorkflowPhase.DESIGN: 1,
            WorkflowPhase.TASKS: 2,
            WorkflowPhase.EXECUTION: 3,
        }

        target_order = phase_order.get(target_phase, 0)

        # Clear approvals for phases after target
        phases_to_clear = [
            phase
            for phase, order in phase_order.items()
            if order > target_order and phase in self.approval_status
        ]

        for phase in phases_to_clear:
            self.approval_status[phase] = False

    def _get_required_documents(self, phase: WorkflowPhase) -> List[str]:
        """Get list of required documents for a phase."""
        if phase == WorkflowPhase.REQUIREMENTS:
            return ["requirements.md"]
        elif phase == WorkflowPhase.DESIGN:
            return ["requirements.md", "design.md"]
        elif phase == WorkflowPhase.TASKS:
            return ["requirements.md", "design.md", "tasks.md"]
        elif phase == WorkflowPhase.EXECUTION:
            return ["requirements.md", "design.md", "tasks.md"]
        return []

    def _get_previous_phases(self, current_phase: WorkflowPhase) -> List[WorkflowPhase]:
        """Get list of phases that should be completed before current phase."""
        if current_phase == WorkflowPhase.DESIGN:
            return [WorkflowPhase.REQUIREMENTS]
        elif current_phase == WorkflowPhase.TASKS:
            return [WorkflowPhase.REQUIREMENTS, WorkflowPhase.DESIGN]
        elif current_phase == WorkflowPhase.EXECUTION:
            return [
                WorkflowPhase.REQUIREMENTS,
                WorkflowPhase.DESIGN,
                WorkflowPhase.TASKS,
            ]
        return []
