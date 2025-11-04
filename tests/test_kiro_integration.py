"""
Comprehensive Integration Tests for Kiro Infrastructure

Tests complete system integration with Kiro infrastructure,
error handling, recovery mechanisms, and real-world scenarios.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from packages.feature_planning import (
    KiroIntegrationManager,
    KiroFileSystemAdapter,
    KiroUserInputAdapter,
    KiroTaskStatusAdapter,
    SpecManager,
    WorkflowController,
    SystemConfiguration,
    FeaturePlanningSystem,
    initialize_system,
    get_error_handler,
    ErrorCategory,
    ErrorSeverity,
    handle_error,
)


class TestKiroIntegrationManager:
    """Test Kiro integration manager functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.integration_manager = KiroIntegrationManager()
        self.feature_name = "test-feature"
    
    def test_file_system_adapter_integration(self):
        """Test file system adapter operations"""
        adapter = self.integration_manager.file_system
        
        # Test write operation
        test_path = f"{self.temp_dir}/test_file.md"
        test_content = "# Test Content\n\nThis is a test file."
        
        result = adapter.write_file(test_path, test_content)
        assert result.success
        assert result.data['path'] == test_path
        
        # Verify file was created
        assert Path(test_path).exists()
        
        # Test read operation
        read_result = adapter.read_file(test_path)
        assert read_result.success
        assert read_result.data == test_content
        
        # Test append operation
        append_content = "\n\nAppended content."
        append_result = adapter.append_file(test_path, append_content)
        assert append_result.success
        
        # Verify append worked
        final_read = adapter.read_file(test_path)
        assert final_read.success
        assert append_content in final_read.data
    
    def test_user_input_adapter_integration(self):
        """Test user input adapter operations"""
        adapter = self.integration_manager.user_input
        
        # Test approval request
        question = "Do the requirements look good?"
        reason = "spec-requirements-review"
        options = ["Yes", "No", "Needs changes"]
        
        result = adapter.request_approval(question, reason, options)
        assert result.success
        assert 'approved' in result.data
        assert 'response' in result.data
        
        # Check input history
        history = adapter.get_input_history()
        assert len(history) == 1
        assert history[0]['question'] == question
        assert history[0]['reason'] == reason
        assert history[0]['options'] == options
    
    def test_task_status_adapter_integration(self):
        """Test task status adapter operations"""
        adapter = self.integration_manager.task_status
        
        # Test task status update
        task_file_path = f".kiro/specs/{self.feature_name}/tasks.md"
        task_name = "1.1 Create base interfaces"
        status = "in_progress"
        
        result = adapter.update_task_status(task_file_path, task_name, status)
        assert result.success
        assert result.data['task'] == task_name
        assert result.data['status'] == status
        
        # Check status history
        updates = adapter.get_status_updates()
        assert len(updates) == 1
        assert updates[0]['task'] == task_name
        assert updates[0]['status'] == status
    
    def test_spec_manager_integration(self):
        """Test spec manager with Kiro integration"""
        # Initialize spec manager with Kiro integration
        spec_manager = self.integration_manager.initialize_spec_manager(self.feature_name)
        
        # Verify Kiro adapter is injected
        assert spec_manager._file_adapter is not None
        assert spec_manager._file_adapter == self.integration_manager.file_system
        
        # Test spec creation with Kiro tools
        with patch.object(spec_manager._file_adapter, 'write_file') as mock_write:
            mock_write.return_value = Mock(success=True)
            
            result = spec_manager.create(self.feature_name)
            assert result
            
            # Verify Kiro file operations were called
            assert mock_write.called
    
    def test_workflow_controller_integration(self):
        """Test workflow controller with Kiro integration"""
        # Initialize components
        spec_manager = self.integration_manager.initialize_spec_manager(self.feature_name)
        workflow_controller = self.integration_manager.initialize_workflow_controller(spec_manager)
        
        # Verify Kiro adapters are injected
        assert workflow_controller._user_input_adapter is not None
        assert workflow_controller._task_status_adapter is not None
        
        # Test approval request with Kiro integration
        with patch.object(workflow_controller._user_input_adapter, 'request_approval') as mock_input:
            mock_input.return_value = Mock(success=True, data={'response': 'yes', 'approved': True})
            
            from packages.feature_planning.base import WorkflowPhase
            result = workflow_controller.request_approval(WorkflowPhase.REQUIREMENTS)
            assert result
            
            # Verify Kiro user input was called
            assert mock_input.called
    
    def test_create_feature_spec_end_to_end(self):
        """Test complete feature spec creation workflow"""
        feature_idea = "A comprehensive user authentication system"
        
        # Mock file operations to avoid actual file creation
        with patch.object(self.integration_manager.file_system, 'write_file') as mock_write:
            mock_write.return_value = Mock(success=True)
            
            result = self.integration_manager.create_feature_spec(self.feature_name, feature_idea)
            
            assert result.success
            assert result.data['feature_name'] == self.feature_name
            assert result.data['workflow_started']
            assert 'current_phase' in result.data
    
    def test_execute_task_integration(self):
        """Test task execution with Kiro integration"""
        task_id = "1.1 Create base interfaces"
        
        # Mock task status updates
        with patch.object(self.integration_manager.task_status, 'update_task_status') as mock_status:
            mock_status.return_value = Mock(success=True)
            
            result = self.integration_manager.execute_task(self.feature_name, task_id)
            
            assert result.success
            assert result.data['task_id'] == task_id
            assert result.data['status'] == 'completed'
            
            # Verify task status was updated twice (in_progress, then completed)
            assert mock_status.call_count == 2
    
    def test_integration_status_reporting(self):
        """Test integration status reporting"""
        # Perform some operations to generate history
        self.integration_manager.file_system.write_file("test.md", "content")
        self.integration_manager.user_input.request_approval("test?", "test")
        self.integration_manager.task_status.update_task_status("tasks.md", "task1", "done")
        
        status = self.integration_manager.get_integration_status()
        
        assert 'file_system' in status
        assert 'user_input' in status
        assert 'task_status' in status
        
        assert status['file_system']['operations_count'] == 1
        assert status['user_input']['requests_count'] == 1
        assert status['task_status']['updates_count'] == 1


class TestSystemConfiguration:
    """Test system configuration and initialization"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = SystemConfiguration(
            specs_directory=f"{self.temp_dir}/.kiro/specs",
            templates_directory=f"{self.temp_dir}/.kiro/templates",
            backup_directory=f"{self.temp_dir}/.kiro/backups"
        )
    
    def test_system_initialization(self):
        """Test complete system initialization"""
        system = FeaturePlanningSystem(self.config)
        
        # Mock directory creation to avoid actual file operations
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', create=True), \
             patch('json.dump'):
            
            result = system.initialize()
            assert result
            assert system.is_initialized()
    
    def test_configuration_management(self):
        """Test configuration loading and saving"""
        from packages.feature_planning.system_config import SystemInitializer
        
        initializer = SystemInitializer(self.config)
        
        # Mock file operations
        with patch('builtins.open', create=True) as mock_open, \
             patch('json.dump') as mock_dump, \
             patch('json.load') as mock_load:
            
            # Test save configuration
            result = initializer.save_configuration(self.config)
            assert result
            assert mock_dump.called
            
            # Test load configuration
            mock_load.return_value = self.config.__dict__
            loaded_config = initializer.load_configuration()
            assert loaded_config is not None
    
    def test_system_status_validation(self):
        """Test system status and health checks"""
        from packages.feature_planning.system_config import SystemInitializer
        
        initializer = SystemInitializer(self.config)
        
        # Mock path existence checks
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            status = initializer.get_system_status()
            
            assert 'initialized' in status
            assert 'configuration_valid' in status
            assert 'directories_exist' in status
            assert 'templates_exist' in status
            assert 'healthy' in status


class TestErrorHandlingIntegration:
    """Test error handling and recovery mechanisms"""
    
    def setup_method(self):
        """Set up test environment"""
        self.error_handler = get_error_handler()
        self.error_handler.clear_error_log()  # Start with clean log
    
    def test_file_system_error_recovery(self):
        """Test file system error handling and recovery"""
        from packages.feature_planning.error_handling import ErrorContext
        
        # Simulate file system error
        error = FileNotFoundError("Directory not found: .kiro/specs/test-feature")
        context = ErrorContext(
            component="SpecManager",
            operation="create",
            feature_name="test-feature"
        )
        
        # Mock directory creation for recovery
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            error_record = self.error_handler.handle_error(
                error, context, ErrorCategory.FILE_SYSTEM, ErrorSeverity.HIGH
            )
            
            assert error_record.category == ErrorCategory.FILE_SYSTEM
            assert error_record.auto_recovery_attempted
            # Recovery should succeed with mocked mkdir
            assert error_record.auto_recovery_successful
    
    def test_validation_error_handling(self):
        """Test validation error handling"""
        from packages.feature_planning.error_handling import ErrorContext
        
        # Simulate validation error
        error = ValueError("EARS pattern not recognized")
        context = ErrorContext(
            component="EARSEngine",
            operation="validate_pattern"
        )
        
        error_record = self.error_handler.handle_error(
            error, context, ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM
        )
        
        assert error_record.category == ErrorCategory.VALIDATION
        assert error_record.auto_recovery_attempted
        # Validation errors typically can't be auto-recovered
        assert not error_record.auto_recovery_successful
        assert error_record.user_action_required
        
        # Check that suggestions were added
        assert len(error_record.recovery_suggestions) > 0
        assert any("EARS" in suggestion for suggestion in error_record.recovery_suggestions)
    
    def test_workflow_error_recovery(self):
        """Test workflow error handling and recovery"""
        from packages.feature_planning.error_handling import ErrorContext
        
        # Simulate workflow error
        error = Exception("Invalid workflow state transition")
        context = ErrorContext(
            component="WorkflowController",
            operation="transition_phase",
            feature_name="test-feature"
        )
        
        # Mock workflow state reset
        with patch('packages.feature_planning.workflow_controller.WorkflowController._save_workflow_state'):
            error_record = self.error_handler.handle_error(
                error, context, ErrorCategory.WORKFLOW, ErrorSeverity.HIGH
            )
            
            assert error_record.category == ErrorCategory.WORKFLOW
            assert error_record.auto_recovery_attempted
    
    def test_user_friendly_error_messages(self):
        """Test user-friendly error message generation"""
        from packages.feature_planning.error_handling import ErrorContext, ErrorRecord
        
        error_record = ErrorRecord(
            error_id="TEST_001",
            timestamp="2024-01-01T12:00:00",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.HIGH,
            message="EARS pattern validation failed",
            technical_details="Stack trace here...",
            context=ErrorContext(
                component="EARSEngine",
                operation="validate_pattern",
                feature_name="test-feature"
            ),
            recovery_suggestions=[
                "Check EARS pattern syntax",
                "Review requirement format"
            ],
            auto_recovery_attempted=True,
            auto_recovery_successful=False
        )
        
        message = self.error_handler.get_user_friendly_message(error_record)
        
        assert "❌ Validation Error" in message
        assert "Operation: validate_pattern" in message
        assert "Component: EARSEngine" in message
        assert "Feature: test-feature" in message
        assert "EARS pattern validation failed" in message
        assert "Check EARS pattern syntax" in message
        assert "Manual intervention required" in message
    
    def test_error_summary_reporting(self):
        """Test error summary and reporting"""
        from packages.feature_planning.error_handling import ErrorContext
        
        # Generate multiple errors
        errors = [
            (ValueError("Validation error 1"), ErrorCategory.VALIDATION),
            (FileNotFoundError("File error 1"), ErrorCategory.FILE_SYSTEM),
            (Exception("Workflow error 1"), ErrorCategory.WORKFLOW),
        ]
        
        for error, category in errors:
            context = ErrorContext(component="TestComponent", operation="test_op")
            self.error_handler.handle_error(error, context, category)
        
        summary = self.error_handler.get_error_summary()
        
        assert summary['total_errors'] == 3
        assert summary['by_category']['validation'] == 1
        assert summary['by_category']['file_system'] == 1
        assert summary['by_category']['workflow'] == 1
        assert len(summary['recent_errors']) == 3


class TestRealWorldScenarios:
    """Test real-world feature specification scenarios"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.integration_manager = KiroIntegrationManager()
    
    def test_complete_feature_development_workflow(self):
        """Test complete workflow from idea to implementation"""
        feature_name = "user-authentication"
        feature_idea = "Implement secure user authentication with multi-factor support"
        
        # Mock all file operations
        with patch.object(self.integration_manager.file_system, 'write_file') as mock_write, \
             patch.object(self.integration_manager.user_input, 'request_approval') as mock_input, \
             patch.object(self.integration_manager.task_status, 'update_task_status') as mock_status:
            
            mock_write.return_value = Mock(success=True)
            mock_input.return_value = Mock(success=True, data={'response': 'yes', 'approved': True})
            mock_status.return_value = Mock(success=True)
            
            # Step 1: Create feature specification
            spec_result = self.integration_manager.create_feature_spec(feature_name, feature_idea)
            assert spec_result.success
            
            # Step 2: Execute first task
            task_result = self.integration_manager.execute_task(feature_name, "1.1 Create base interfaces")
            assert task_result.success
            
            # Verify integration operations
            assert mock_write.called  # File operations occurred
            assert mock_status.called  # Task status updates occurred
    
    def test_error_recovery_in_workflow(self):
        """Test error recovery during workflow execution"""
        feature_name = "error-prone-feature"
        
        # Simulate file system error during spec creation
        with patch.object(self.integration_manager.file_system, 'write_file') as mock_write:
            # First call fails, second succeeds (simulating recovery)
            mock_write.side_effect = [
                Mock(success=False, error="Permission denied"),
                Mock(success=True)
            ]
            
            # This should trigger error handling and recovery
            result = self.integration_manager.create_feature_spec(feature_name, "test idea")
            
            # Even with initial failure, the operation should eventually succeed
            # due to error handling and recovery mechanisms
            assert mock_write.call_count >= 1
    
    def test_concurrent_operations_handling(self):
        """Test handling of concurrent operations"""
        features = ["feature-1", "feature-2", "feature-3"]
        
        # Mock file operations
        with patch.object(self.integration_manager.file_system, 'write_file') as mock_write:
            mock_write.return_value = Mock(success=True)
            
            # Create multiple features concurrently (simulated)
            results = []
            for feature in features:
                result = self.integration_manager.create_feature_spec(feature, f"Idea for {feature}")
                results.append(result)
            
            # All operations should succeed
            assert all(result.success for result in results)
            
            # Verify file operations for each feature
            assert mock_write.call_count >= len(features)
    
    def test_large_specification_handling(self):
        """Test handling of large, complex specifications"""
        feature_name = "complex-system"
        
        # Create a complex feature with many requirements
        complex_idea = """
        A comprehensive enterprise resource planning system with:
        - User management and authentication
        - Inventory tracking and management
        - Financial reporting and analytics
        - Customer relationship management
        - Supply chain optimization
        - Real-time dashboard and notifications
        """
        
        with patch.object(self.integration_manager.file_system, 'write_file') as mock_write:
            mock_write.return_value = Mock(success=True)
            
            result = self.integration_manager.create_feature_spec(feature_name, complex_idea)
            assert result.success
            
            # Verify that the system can handle complex specifications
            assert result.data['feature_name'] == feature_name
    
    def test_integration_status_monitoring(self):
        """Test integration status monitoring and health checks"""
        # Perform various operations
        operations = [
            ("file_write", lambda: self.integration_manager.file_system.write_file("test.md", "content")),
            ("user_input", lambda: self.integration_manager.user_input.request_approval("test?", "test")),
            ("task_status", lambda: self.integration_manager.task_status.update_task_status("tasks.md", "task", "done")),
        ]
        
        for op_name, operation in operations:
            operation()
        
        # Check integration status
        status = self.integration_manager.get_integration_status()
        
        # Verify all components have recorded operations
        assert status['file_system']['operations_count'] > 0
        assert status['user_input']['requests_count'] > 0
        assert status['task_status']['updates_count'] > 0
        
        # Verify recent operations are tracked
        assert len(status['file_system']['last_operations']) > 0
        assert len(status['user_input']['last_requests']) > 0
        assert len(status['task_status']['last_updates']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])