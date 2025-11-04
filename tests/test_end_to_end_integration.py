"""
End-to-End Integration Tests

Tests complete system integration from system initialization
through feature specification creation and task execution.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from packages.feature_planning import (
    initialize_system,
    get_system,
    SystemConfiguration,
    get_kiro_integration,
    SpecManager,
    WorkflowController,
    EARSEngine,
    RequirementsValidator,
    DesignGenerator,
    TaskPlanner,
    get_error_handler,
    ErrorCategory,
    ErrorSeverity,
)


class TestEndToEndIntegration:
    """End-to-end integration tests for the complete system"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()
        
        # Create test configuration
        self.config = SystemConfiguration(
            specs_directory=f"{self.temp_dir}/.kiro/specs",
            templates_directory=f"{self.temp_dir}/.kiro/templates",
            backup_directory=f"{self.temp_dir}/.kiro/backups"
        )
        
        # Clear error log
        get_error_handler().clear_error_log()
    
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_system_initialization(self):
        """Test complete system initialization from scratch"""
        # Mock file operations to avoid actual file creation
        with patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('builtins.open', create=True) as mock_open, \
             patch('json.dump') as mock_dump:
            
            # Initialize system
            result = initialize_system(self.config)
            assert result
            
            # Verify system is initialized
            system = get_system()
            assert system.is_initialized()
            
            # Verify configuration is set
            config = system.get_configuration()
            assert config.specs_directory == self.config.specs_directory
            
            # Verify directories would be created
            assert mock_mkdir.called
    
    def test_feature_specification_creation_workflow(self):
        """Test complete feature specification creation workflow"""
        feature_name = "user-authentication"
        
        # Mock all file operations
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True), \
             patch('json.dump'), \
             patch('json.load') as mock_load:
            
            # Mock existing metadata for workflow
            mock_load.return_value = {
                "feature_name": feature_name,
                "created_at": "2024-01-01T12:00:00",
                "current_phase": "requirements"
            }
            
            # Initialize system
            initialize_system(self.config)
            
            # Get Kiro integration
            kiro_integration = get_kiro_integration()
            
            # Create feature specification
            result = kiro_integration.create_feature_spec(
                feature_name, 
                "Secure user authentication system with MFA support"
            )
            
            assert result.success
            assert result.data['feature_name'] == feature_name
            assert result.data['workflow_started']
    
    def test_requirements_generation_and_validation(self):
        """Test requirements generation and validation workflow"""
        feature_name = "data-processing"
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True), \
             patch('json.dump'):
            
            # Initialize components
            spec_manager = SpecManager()
            ears_engine = EARSEngine()
            requirements_validator = RequirementsValidator()
            
            # Create spec directory
            spec_manager.create(feature_name)
            
            # Generate sample requirements
            user_story = "As a data analyst, I want to process large datasets efficiently, so that I can generate insights quickly"
            
            # Generate EARS-compliant requirements
            requirements = ears_engine.format_requirement(user_story)
            assert len(requirements) > 0
            
            # Validate requirements
            for requirement in requirements:
                pattern_result = ears_engine.validate_pattern(requirement)
                assert pattern_result.is_valid
                
                incose_result = requirements_validator.check_incose_rules(requirement)
                assert incose_result.is_valid
    
    def test_design_generation_workflow(self):
        """Test design generation from requirements"""
        feature_name = "api-gateway"
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True), \
             patch('json.dump'):
            
            # Create sample requirements
            requirements = [
                {
                    'id': 'REQ-1',
                    'user_story': 'As an API consumer, I want secure access to services, so that my data is protected',
                    'acceptance_criteria': [
                        'WHEN a client requests API access, THE API_Gateway SHALL authenticate the request',
                        'THE API_Gateway SHALL enforce rate limiting on all requests'
                    ]
                }
            ]
            
            # Generate design
            design_generator = DesignGenerator()
            design_doc = design_generator.generate_design(requirements)
            
            assert design_doc is not None
            assert "## Overview" in design_doc
            assert "## Architecture" in design_doc
            assert "## Components and Interfaces" in design_doc
    
    def test_task_planning_workflow(self):
        """Test task planning from design document"""
        feature_name = "notification-system"
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True), \
             patch('json.dump'):
            
            # Create sample design document
            design_doc = """
            # Design Document
            
            ## Overview
            A real-time notification system for user alerts.
            
            ## Architecture
            - Notification Service
            - Message Queue
            - Delivery Channels (Email, SMS, Push)
            
            ## Components and Interfaces
            ### Notification Service
            - Handles notification creation and routing
            - Manages delivery preferences
            """
            
            # Create sample requirements for reference
            requirements = [
                {
                    'id': 'REQ-1',
                    'user_story': 'As a user, I want to receive notifications, so that I stay informed',
                    'acceptance_criteria': [
                        'WHEN an event occurs, THE Notification_System SHALL send appropriate notifications'
                    ]
                }
            ]
            
            # Generate tasks
            task_planner = TaskPlanner()
            tasks = task_planner.generate_tasks(design_doc, requirements)
            
            assert len(tasks) > 0
            
            # Verify task structure
            for task in tasks:
                assert 'id' in task
                assert 'title' in task
                assert 'requirements_refs' in task
    
    def test_workflow_phase_transitions(self):
        """Test complete workflow phase transitions"""
        feature_name = "search-engine"
        
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True), \
             patch('json.dump'), \
             patch('json.load') as mock_load:
            
            # Mock workflow state
            mock_load.return_value = {
                "current_phase": "requirements",
                "approval_status": {},
                "phase_history": []
            }
            
            # Initialize workflow controller
            spec_manager = SpecManager()
            spec_manager.create(feature_name)
            
            workflow_controller = WorkflowController(feature_name)
            
            # Mock user input for approvals
            with patch.object(workflow_controller, '_user_input_adapter') as mock_input:
                mock_input.request_approval.return_value = Mock(
                    success=True, 
                    data={'response': 'yes', 'approved': True}
                )
                
                from packages.feature_planning.base import WorkflowPhase
                
                # Test requirements approval
                result = workflow_controller.request_approval(WorkflowPhase.REQUIREMENTS)
                assert result
                
                # Test transition to design
                transition_result = workflow_controller.transition_phase(
                    WorkflowPhase.REQUIREMENTS, 
                    WorkflowPhase.DESIGN
                )
                assert transition_result
                
                # Verify current phase
                assert workflow_controller.current_phase == WorkflowPhase.DESIGN
    
    def test_error_handling_throughout_workflow(self):
        """Test error handling at various points in the workflow"""
        feature_name = "error-test-feature"
        
        # Test file system error handling
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            spec_manager = SpecManager()
            
            # This should trigger error handling
            result = spec_manager.create(feature_name)
            assert not result  # Should fail gracefully
            
            # Check that error was logged
            error_summary = get_error_handler().get_error_summary()
            assert error_summary['total_errors'] > 0
    
    def test_kiro_integration_end_to_end(self):
        """Test complete Kiro integration workflow"""
        feature_name = "kiro-integration-test"
        feature_idea = "Test feature for Kiro integration"
        
        # Get Kiro integration manager
        kiro_integration = get_kiro_integration()
        
        # Mock all Kiro tool operations
        with patch.object(kiro_integration.file_system, 'write_file') as mock_write, \
             patch.object(kiro_integration.user_input, 'request_approval') as mock_input, \
             patch.object(kiro_integration.task_status, 'update_task_status') as mock_status:
            
            # Configure mocks
            mock_write.return_value = Mock(success=True)
            mock_input.return_value = Mock(success=True, data={'response': 'approved'})
            mock_status.return_value = Mock(success=True)
            
            # Step 1: Create feature specification
            spec_result = kiro_integration.create_feature_spec(feature_name, feature_idea)
            assert spec_result.success
            
            # Step 2: Execute a task
            task_result = kiro_integration.execute_task(feature_name, "1.1 Setup infrastructure")
            assert task_result.success
            
            # Step 3: Check integration status
            status = kiro_integration.get_integration_status()
            assert status['file_system']['operations_count'] > 0
            assert status['task_status']['updates_count'] > 0
    
    def test_system_recovery_mechanisms(self):
        """Test system recovery from various failure scenarios"""
        feature_name = "recovery-test"
        
        # Test recovery from corrupted configuration
        with patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
            from packages.feature_planning.system_config import SystemInitializer
            
            initializer = SystemInitializer(self.config)
            
            # This should trigger error handling and recovery
            with patch.object(initializer, 'reset_configuration', return_value=True):
                # Recovery should be attempted
                config = initializer.load_configuration()
                # Should return None due to JSON error, triggering recovery
                assert config is None
    
    def test_concurrent_feature_development(self):
        """Test handling multiple features being developed concurrently"""
        features = [
            ("auth-system", "User authentication and authorization"),
            ("payment-gateway", "Payment processing system"),
            ("notification-service", "Real-time notification system")
        ]
        
        kiro_integration = get_kiro_integration()
        
        # Mock file operations
        with patch.object(kiro_integration.file_system, 'write_file') as mock_write:
            mock_write.return_value = Mock(success=True)
            
            # Create multiple features
            results = []
            for feature_name, feature_idea in features:
                result = kiro_integration.create_feature_spec(feature_name, feature_idea)
                results.append(result)
            
            # All should succeed
            assert all(result.success for result in results)
            
            # Verify separate file operations for each feature
            assert mock_write.call_count >= len(features)
    
    def test_performance_with_large_specifications(self):
        """Test system performance with large, complex specifications"""
        feature_name = "enterprise-system"
        
        # Create a large, complex feature idea
        complex_idea = """
        Enterprise Resource Planning System with the following modules:
        """ + "\n".join([f"- Module {i}: Complex business logic with multiple integrations" for i in range(50)])
        
        kiro_integration = get_kiro_integration()
        
        # Mock file operations
        with patch.object(kiro_integration.file_system, 'write_file') as mock_write:
            mock_write.return_value = Mock(success=True)
            
            # This should complete without timeout or memory issues
            result = kiro_integration.create_feature_spec(feature_name, complex_idea)
            assert result.success
    
    def test_system_state_consistency(self):
        """Test that system maintains consistent state throughout operations"""
        feature_name = "state-consistency-test"
        
        # Initialize system
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True), \
             patch('json.dump'):
            
            initialize_system(self.config)
            system = get_system()
            
            # Verify initial state
            assert system.is_initialized()
            initial_config = system.get_configuration()
            
            # Perform various operations
            kiro_integration = get_kiro_integration()
            
            with patch.object(kiro_integration.file_system, 'write_file') as mock_write:
                mock_write.return_value = Mock(success=True)
                
                # Create feature
                result = kiro_integration.create_feature_spec(feature_name, "Test feature")
                assert result.success
                
                # Verify system state is still consistent
                final_config = system.get_configuration()
                assert final_config.specs_directory == initial_config.specs_directory
                assert system.is_initialized()
    
    def test_cleanup_and_resource_management(self):
        """Test proper cleanup and resource management"""
        feature_name = "cleanup-test"
        
        # Create multiple operations that should be cleaned up
        kiro_integration = get_kiro_integration()
        
        # Perform operations
        with patch.object(kiro_integration.file_system, 'write_file') as mock_write:
            mock_write.return_value = Mock(success=True)
            
            # Create and execute multiple operations
            for i in range(10):
                kiro_integration.create_feature_spec(f"{feature_name}-{i}", f"Test feature {i}")
        
        # Check that operations are tracked but not causing memory leaks
        status = kiro_integration.get_integration_status()
        
        # Should have reasonable limits on stored operations
        assert len(status['file_system']['last_operations']) <= 5  # Should limit stored operations
        
        # Error log should also be manageable
        error_summary = get_error_handler().get_error_summary()
        assert len(error_summary.get('recent_errors', [])) <= 10  # Should limit stored errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])