"""
Integration tests for Spec Manager document lifecycle management.

Tests directory creation, file operations, versioning, backup functionality,
and rollback mechanisms.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from packages.feature_planning.spec_manager import SpecManager
from packages.feature_planning.base import WorkflowPhase


class TestSpecManagerIntegration:
    """Integration tests for SpecManager functionality."""
    
    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.spec_manager = SpecManager(base_path=self.temp_dir)
        self.test_feature_name = "test-feature"
    
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_create_specification_directory(self):
        """Test specification directory creation and structure."""
        # Create specification
        result = self.spec_manager.create(self.test_feature_name)
        assert result is True
        
        # Verify directory structure
        spec_dir = self.temp_dir / self.test_feature_name
        assert spec_dir.exists()
        assert spec_dir.is_dir()
        
        # Verify required files exist
        required_files = ["requirements.md", "design.md", "tasks.md", "metadata.json"]
        for filename in required_files:
            file_path = spec_dir / filename
            assert file_path.exists(), f"Missing required file: {filename}"
        
        # Verify metadata content
        metadata_file = spec_dir / "metadata.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        assert metadata["feature_name"] == self.test_feature_name
        assert metadata["kebab_name"] == self.test_feature_name
        assert metadata["current_phase"] == WorkflowPhase.REQUIREMENTS.value
        assert "created_at" in metadata
        assert "version" in metadata
    
    def test_kebab_case_conversion(self):
        """Test feature name conversion to kebab-case."""
        test_cases = [
            ("My Feature Name", "my-feature-name"),
            ("Feature_With_Underscores", "feature-with-underscores"),
            ("Feature   With   Spaces", "feature-with-spaces"),
            ("Feature123", "feature123"),
            ("Feature-Already-Kebab", "feature-already-kebab"),
            ("Feature!@#$%Name", "featurename")
        ]
        
        for input_name, expected_kebab in test_cases:
            result = self.spec_manager.create(input_name)
            assert result is True
            
            # Check directory was created with kebab-case name
            spec_dir = self.temp_dir / expected_kebab
            assert spec_dir.exists(), f"Failed for input: {input_name}"
            
            # Clean up for next test
            shutil.rmtree(spec_dir)
    
    def test_load_specification(self):
        """Test loading existing specification documents."""
        # Create specification first
        self.spec_manager.create(self.test_feature_name)
        
        # Load specification
        loaded_spec = self.spec_manager.load(self.test_feature_name)
        assert loaded_spec is not None
        
        # Verify structure
        assert "metadata" in loaded_spec
        assert "documents" in loaded_spec
        assert "directory" in loaded_spec
        
        # Verify documents
        documents = loaded_spec["documents"]
        assert "requirements" in documents
        assert "design" in documents
        assert "tasks" in documents
        
        # Verify metadata
        metadata = loaded_spec["metadata"]
        assert metadata["feature_name"] == self.test_feature_name
    
    def test_load_nonexistent_specification(self):
        """Test loading specification that doesn't exist."""
        result = self.spec_manager.load("nonexistent-feature")
        assert result is None
    
    def test_update_document(self):
        """Test updating specification documents."""
        # Create specification
        self.spec_manager.create(self.test_feature_name)
        
        # Update requirements document
        new_content = "# Updated Requirements\n\nThis is updated content."
        update_data = {
            "document_type": "requirements",
            "content": new_content
        }
        
        result = self.spec_manager.update(self.test_feature_name, update_data)
        assert result is True
        
        # Verify update
        loaded_spec = self.spec_manager.load(self.test_feature_name)
        assert loaded_spec["documents"]["requirements"] == new_content
        
        # Verify metadata timestamp was updated
        metadata = loaded_spec["metadata"]
        assert "last_modified" in metadata
    
    def test_update_metadata(self):
        """Test updating specification metadata."""
        # Create specification
        self.spec_manager.create(self.test_feature_name)
        
        # Update metadata
        new_metadata = {
            "feature_name": self.test_feature_name,
            "current_phase": WorkflowPhase.DESIGN.value,
            "custom_field": "custom_value"
        }
        
        update_data = {
            "document_type": "metadata",
            "content": new_metadata
        }
        
        result = self.spec_manager.update(self.test_feature_name, update_data)
        assert result is True
        
        # Verify update
        loaded_spec = self.spec_manager.load(self.test_feature_name)
        metadata = loaded_spec["metadata"]
        assert metadata["current_phase"] == WorkflowPhase.DESIGN.value
        assert metadata["custom_field"] == "custom_value"
    
    def test_validate_structure(self):
        """Test specification structure validation."""
        # Test validation of nonexistent specification
        assert self.spec_manager.validate_structure("nonexistent") is False
        
        # Create specification
        self.spec_manager.create(self.test_feature_name)
        
        # Test validation of complete specification
        assert self.spec_manager.validate_structure(self.test_feature_name) is True
        
        # Test validation with missing file
        spec_dir = self.temp_dir / self.test_feature_name
        requirements_file = spec_dir / "requirements.md"
        requirements_file.unlink()
        
        assert self.spec_manager.validate_structure(self.test_feature_name) is False
    
    def test_list_specifications(self):
        """Test listing all available specifications."""
        # Initially empty
        specs = self.spec_manager.list_specifications()
        assert len(specs) == 0
        
        # Create multiple specifications
        feature_names = ["feature-one", "feature-two", "feature-three"]
        for name in feature_names:
            self.spec_manager.create(name)
        
        # List specifications
        specs = self.spec_manager.list_specifications()
        assert len(specs) == 3
        assert set(specs) == set(feature_names)
        
        # Verify sorted order
        assert specs == sorted(feature_names)
    
    def test_delete_specification(self):
        """Test deleting specification and all documents."""
        # Create specification
        self.spec_manager.create(self.test_feature_name)
        spec_dir = self.temp_dir / self.test_feature_name
        assert spec_dir.exists()
        
        # Delete specification
        result = self.spec_manager.delete(self.test_feature_name)
        assert result is True
        assert not spec_dir.exists()
        
        # Test deleting nonexistent specification
        result = self.spec_manager.delete("nonexistent")
        assert result is False
    
    def test_backup_document(self):
        """Test document backup functionality."""
        # Create specification
        self.spec_manager.create(self.test_feature_name)
        
        # Update document to create content worth backing up
        update_data = {
            "document_type": "requirements",
            "content": "# Original Requirements\n\nOriginal content."
        }
        self.spec_manager.update(self.test_feature_name, update_data)
        
        # Update again to trigger backup of the original content
        update_data2 = {
            "document_type": "requirements",
            "content": "# Updated Requirements\n\nUpdated content."
        }
        self.spec_manager.update(self.test_feature_name, update_data2)
        
        # Verify backup exists (created during the second update)
        backup_dir = self.temp_dir / ".backups" / self.test_feature_name
        assert backup_dir.exists()
        
        backup_files = list(backup_dir.glob("requirements_*.backup"))
        assert len(backup_files) >= 1
        
        # Verify backup content (should contain the original content)
        # Sort backup files by modification time to get the most recent
        backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        backup_file = backup_files[0]  # Most recent backup
        with open(backup_file, 'r') as f:
            backup_content = f.read()
        assert "Original content" in backup_content
    
    def test_backup_history(self):
        """Test backup history tracking."""
        # Create specification and content
        self.spec_manager.create(self.test_feature_name)
        
        # Create initial content first
        initial_update = {
            "document_type": "requirements",
            "content": "# Initial Requirements\n\nInitial content."
        }
        self.spec_manager.update(self.test_feature_name, initial_update)
        
        # Create multiple backups by updating content
        for i in range(3):
            update_data = {
                "document_type": "requirements",
                "content": f"# Requirements Version {i}\n\nContent version {i}."
            }
            self.spec_manager.update(self.test_feature_name, update_data)  # This creates backup automatically
        
        # Get backup history
        history = self.spec_manager.get_backup_history(self.test_feature_name, "requirements")
        assert len(history) >= 3
        
        # Verify history structure
        for backup_info in history:
            assert "filename" in backup_info
            assert "path" in backup_info
            assert "timestamp" in backup_info
            assert "size" in backup_info
            assert backup_info["document_type"] == "requirements"
        
        # Verify chronological order (newest first)
        timestamps = [backup["timestamp"] for backup in history]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_version_snapshots(self):
        """Test version snapshot creation and management."""
        # Create specification
        self.spec_manager.create(self.test_feature_name)
        
        # Update documents
        update_data = {
            "document_type": "requirements",
            "content": "# Approved Requirements\n\nFinal requirements content."
        }
        self.spec_manager.update(self.test_feature_name, update_data)
        
        # Create version snapshot
        result = self.spec_manager.create_version_snapshot(self.test_feature_name, "approved_requirements")
        assert result is True
        
        # Verify version directory exists
        spec_dir = self.temp_dir / self.test_feature_name
        versions_dir = spec_dir / ".versions"
        assert versions_dir.exists()
        
        # Verify version files
        version_dirs = list(versions_dir.glob("approved_requirements_*"))
        assert len(version_dirs) == 1
        
        version_dir = version_dirs[0]
        assert (version_dir / "requirements.md").exists()
        assert (version_dir / "design.md").exists()
        assert (version_dir / "tasks.md").exists()
        assert (version_dir / "metadata.json").exists()
        assert (version_dir / "version_info.json").exists()
    
    def test_list_versions(self):
        """Test listing version snapshots."""
        # Create specification
        self.spec_manager.create(self.test_feature_name)
        
        # Create multiple versions
        version_names = ["v1_requirements", "v2_design", "v3_tasks"]
        for version_name in version_names:
            self.spec_manager.create_version_snapshot(self.test_feature_name, version_name)
        
        # List versions
        versions = self.spec_manager.list_versions(self.test_feature_name)
        assert len(versions) == 3
        
        # Verify version structure
        for version in versions:
            assert "version_name" in version
            assert "created_at" in version
            assert "feature_name" in version
            assert "directory" in version
        
        # Verify version names
        version_names_found = [v["version_name"] for v in versions]
        assert set(version_names_found) == set(version_names)
    
    def test_rollback_to_version(self):
        """Test rollback functionality."""
        # Create specification
        self.spec_manager.create(self.test_feature_name)
        
        # Create initial content and version
        original_content = "# Original Requirements\n\nOriginal content."
        update_data = {
            "document_type": "requirements",
            "content": original_content
        }
        self.spec_manager.update(self.test_feature_name, update_data)
        self.spec_manager.create_version_snapshot(self.test_feature_name, "original_version")
        
        # Update content again
        modified_content = "# Modified Requirements\n\nModified content."
        update_data["content"] = modified_content
        self.spec_manager.update(self.test_feature_name, update_data)
        
        # Verify current content is modified
        loaded_spec = self.spec_manager.load(self.test_feature_name)
        assert "Modified content" in loaded_spec["documents"]["requirements"]
        
        # Rollback to original version
        result = self.spec_manager.rollback_to_version(self.test_feature_name, "original_version")
        assert result is True
        
        # Verify content was restored
        loaded_spec = self.spec_manager.load(self.test_feature_name)
        assert "Original content" in loaded_spec["documents"]["requirements"]
        assert "Modified content" not in loaded_spec["documents"]["requirements"]
        
        # Verify rollback metadata
        metadata = loaded_spec["metadata"]
        assert "last_rollback" in metadata
        assert metadata["last_rollback"]["from_version"] == "original_version"
    
    def test_restore_from_backup(self):
        """Test restoring document from backup."""
        # Create specification
        self.spec_manager.create(self.test_feature_name)
        
        # Create original content
        original_content = "# Original Requirements\n\nOriginal content."
        update_data = {
            "document_type": "requirements",
            "content": original_content
        }
        self.spec_manager.update(self.test_feature_name, update_data)
        
        # Modify content (this will create a backup of the original content)
        modified_content = "# Modified Requirements\n\nModified content."
        update_data["content"] = modified_content
        self.spec_manager.update(self.test_feature_name, update_data)
        
        # Get backup filename (should contain the original content)
        history = self.spec_manager.get_backup_history(self.test_feature_name, "requirements")
        assert len(history) >= 1
        backup_filename = history[0]["filename"]
        
        # Restore from backup
        result = self.spec_manager.restore_from_backup(self.test_feature_name, "requirements", backup_filename)
        assert result is True
        
        # Verify content was restored
        loaded_spec = self.spec_manager.load(self.test_feature_name)
        assert "Original content" in loaded_spec["documents"]["requirements"]
    
    def test_error_handling(self):
        """Test error handling for various failure scenarios."""
        # Test invalid document type
        self.spec_manager.create(self.test_feature_name)
        
        invalid_update = {
            "document_type": "invalid_type",
            "content": "some content"
        }
        result = self.spec_manager.update(self.test_feature_name, invalid_update)
        assert result is False
        
        # Test malformed update data
        malformed_update = {"wrong_key": "wrong_value"}
        result = self.spec_manager.update(self.test_feature_name, malformed_update)
        assert result is False
        
        # Test backup of nonexistent document
        result = self.spec_manager.backup_document("nonexistent", "requirements")
        assert result is False
        
        # Test rollback to nonexistent version
        result = self.spec_manager.rollback_to_version(self.test_feature_name, "nonexistent_version")
        assert result is False
    
    def test_get_document_path(self):
        """Test document path generation."""
        # Test various document types
        req_path = self.spec_manager.get_document_path(self.test_feature_name, "requirements")
        assert req_path == self.temp_dir / self.test_feature_name / "requirements.md"
        
        design_path = self.spec_manager.get_document_path(self.test_feature_name, "design")
        assert design_path == self.temp_dir / self.test_feature_name / "design.md"
        
        tasks_path = self.spec_manager.get_document_path(self.test_feature_name, "tasks")
        assert tasks_path == self.temp_dir / self.test_feature_name / "tasks.md"
        
        metadata_path = self.spec_manager.get_document_path(self.test_feature_name, "metadata")
        assert metadata_path == self.temp_dir / self.test_feature_name / "metadata.json"
    
    def test_backup_cleanup(self):
        """Test automatic cleanup of old backups."""
        # Create specification
        self.spec_manager.create(self.test_feature_name)
        
        # Create many backups (more than the cleanup limit)
        for i in range(15):
            update_data = {
                "document_type": "requirements",
                "content": f"# Requirements Version {i}\n\nContent {i}."
            }
            self.spec_manager.update(self.test_feature_name, update_data)
            self.spec_manager.backup_document(self.test_feature_name, "requirements")
        
        # Verify cleanup occurred (should keep only 10 most recent)
        backup_dir = self.temp_dir / ".backups" / self.test_feature_name
        backup_files = list(backup_dir.glob("requirements_*.backup"))
        assert len(backup_files) <= 10