"""
Spec Manager for document lifecycle management.

This module handles specification document creation, versioning,
and file system operations within the Kiro framework.
"""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import BaseManager, WorkflowPhase
from .config import get_config
from .error_handling import (
    handle_error, 
    ErrorCategory, 
    ErrorSeverity, 
    with_error_handling
)


class SpecManager(BaseManager):
    """
    Manages specification documents and their lifecycle.

    Handles directory creation, document versioning, and integration
    with Kiro's file system tools.
    """

    def __init__(self, base_path: Optional[Path] = None) -> None:
        """Initialize Spec Manager with base directory."""
        self.config = get_config()
        self.base_path = base_path or Path(
            self.config.get_setting("default_spec_directory", ".kiro/specs")
        )
        # Kiro file system adapter (injected by KiroIntegrationManager)
        self._file_adapter = None

    def create(self, name: str, **kwargs: Any) -> bool:
        """
        Create new specification directory and initial documents.

        Args:
            name: Feature name (will be converted to kebab-case)
            **kwargs: Additional creation parameters

        Returns:
            True if creation successful
        """
        try:
            # Create directory structure
            spec_dir = self.create_spec_directory(name)

            # Initialize metadata
            metadata = {
                "feature_name": name,
                "kebab_name": self._to_kebab_case(name),
                "created_at": datetime.now().isoformat(),
                "current_phase": WorkflowPhase.REQUIREMENTS.value,
                "version": "1.0.0",
                **kwargs,
            }

            # Save metadata
            metadata_file = spec_dir / "metadata.json"
            metadata_content = json.dumps(metadata, indent=2)
            
            if self._file_adapter:
                result = self._file_adapter.write_file(str(metadata_file), metadata_content)
                if not result.success:
                    raise Exception(f"Kiro file write failed: {result.error}")
            else:
                with open(metadata_file, "w") as f:
                    f.write(metadata_content)

            return True

        except Exception as e:
            handle_error(
                e,
                component="SpecManager",
                operation="create",
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.HIGH,
                feature_name=name
            )
            return False

    def load(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load existing specification documents.

        Args:
            name: Feature name to load

        Returns:
            Dictionary containing all spec documents or None if not found
        """
        try:
            kebab_name = self._to_kebab_case(name)
            spec_dir = self.base_path / kebab_name

            if not spec_dir.exists():
                return None

            # Load metadata
            metadata_file = spec_dir / "metadata.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

            # Load documents
            documents: Dict[str, Optional[str]] = {}
            for doc_type in ["requirements", "design", "tasks"]:
                doc_file = spec_dir / f"{doc_type}.md"
                if doc_file.exists():
                    with open(doc_file, "r") as f:
                        documents[doc_type] = f.read()
                else:
                    documents[doc_type] = None

            return {"metadata": metadata, "documents": documents, "directory": spec_dir}

        except Exception as e:
            handle_error(
                e,
                component="SpecManager",
                operation="load",
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                feature_name=name
            )
            return None

    def update(self, name: str, content: Any) -> bool:
        """
        Update specification document with new content.

        Args:
            name: Feature name
            content: Dictionary with document_type and content keys

        Returns:
            True if update successful
        """
        try:
            if (
                not isinstance(content, dict)
                or "document_type" not in content
                or "content" not in content
            ):
                raise ValueError(
                    "Content must be dict with 'document_type' and 'content' keys"
                )

            kebab_name = self._to_kebab_case(name)
            spec_dir = self.base_path / kebab_name

            if not spec_dir.exists():
                return False

            document_type = content["document_type"]
            document_content = content["content"]

            # Validate document type
            if document_type not in ["requirements", "design", "tasks", "metadata"]:
                raise ValueError(f"Invalid document type: {document_type}")

            # Create backup before updating (will be implemented in task 4.2)
            if self.config.get_setting("auto_backup", True):
                self.backup_document(name, document_type)

            # Update document
            if document_type == "metadata":
                metadata_file = spec_dir / "metadata.json"
                content = json.dumps(document_content, indent=2)
                
                if self._file_adapter:
                    result = self._file_adapter.write_file(str(metadata_file), content)
                    if not result.success:
                        raise Exception(f"Kiro file write failed: {result.error}")
                else:
                    with open(metadata_file, "w") as f:
                        f.write(content)
            else:
                doc_file = spec_dir / f"{document_type}.md"
                
                if self._file_adapter:
                    result = self._file_adapter.write_file(str(doc_file), document_content)
                    if not result.success:
                        raise Exception(f"Kiro file write failed: {result.error}")
                else:
                    with open(doc_file, "w") as f:
                        f.write(document_content)

            # Update metadata timestamp
            self._update_metadata_timestamp(spec_dir)

            return True

        except Exception as e:
            print(f"Error updating specification: {e}")
            return False

    def delete(self, name: str) -> bool:
        """
        Delete specification and all associated documents.

        Args:
            name: Feature name to delete

        Returns:
            True if deletion successful
        """
        try:
            kebab_name = self._to_kebab_case(name)
            spec_dir = self.base_path / kebab_name

            if not spec_dir.exists():
                return False

            # Create final backup before deletion
            backup_dir = self._create_backup_directory(kebab_name)
            if backup_dir:
                shutil.copytree(
                    spec_dir,
                    backup_dir
                    / f"final_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                )

            # Remove directory and all contents
            shutil.rmtree(spec_dir)

            return True

        except Exception as e:
            print(f"Error deleting specification: {e}")
            return False

    def create_spec_directory(self, feature_name: str) -> Path:
        """
        Create specification directory structure.

        Args:
            feature_name: Name of the feature (kebab-case)

        Returns:
            Path to created directory
        """
        # Convert to kebab-case if needed
        kebab_name = self._to_kebab_case(feature_name)

        # Create directory path
        spec_dir = self.base_path / kebab_name

        # Create directory if it doesn't exist
        spec_dir.mkdir(parents=True, exist_ok=True)

        # Create initial document files if they don't exist
        self._create_initial_documents(spec_dir)

        return spec_dir

    def backup_document(self, feature_name: str, document_type: str) -> bool:
        """
        Create backup of document before modification.

        Args:
            feature_name: Feature name
            document_type: Type of document (requirements, design, tasks)

        Returns:
            True if backup successful
        """
        try:
            kebab_name = self._to_kebab_case(feature_name)
            spec_dir = self.base_path / kebab_name

            # Get source document path
            if document_type == "metadata":
                source_file = spec_dir / "metadata.json"
            else:
                source_file = spec_dir / f"{document_type}.md"

            if not source_file.exists():
                return False

            # Create backup directory
            backup_dir = self._create_backup_directory(kebab_name)
            if not backup_dir:
                return False

            # Create timestamped backup with microsecond precision
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_filename = f"{document_type}_{timestamp}.backup"
            backup_file = backup_dir / backup_filename

            # Copy file to backup location
            shutil.copy2(source_file, backup_file)

            # Maintain backup history (keep last 10 backups per document type)
            self._cleanup_old_backups(backup_dir, document_type, max_backups=10)

            return True

        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def validate_structure(self, feature_name: str) -> bool:
        """
        Validate specification directory structure.

        Args:
            feature_name: Feature name to validate

        Returns:
            True if structure is valid
        """
        try:
            kebab_name = self._to_kebab_case(feature_name)
            spec_dir = self.base_path / kebab_name

            # Check if directory exists
            if not spec_dir.exists() or not spec_dir.is_dir():
                return False

            # Check for required files
            required_files = ["requirements.md", "design.md", "tasks.md"]
            for file_name in required_files:
                file_path = spec_dir / file_name
                if not file_path.exists():
                    return False

            # Check metadata file
            metadata_file = spec_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                    # Validate required metadata fields
                    required_fields = ["feature_name", "created_at", "current_phase"]
                    for field in required_fields:
                        if field not in metadata:
                            return False
                except json.JSONDecodeError:
                    return False

            return True

        except Exception:
            return False

    def list_specifications(self) -> List[str]:
        """
        List all available specifications.

        Returns:
            List of specification names
        """
        try:
            if not self.base_path.exists():
                return []

            specs = []
            for item in self.base_path.iterdir():
                if item.is_dir() and self.validate_structure(item.name):
                    specs.append(item.name)

            return sorted(specs)

        except Exception:
            return []

    def get_document_path(self, feature_name: str, document_type: str) -> Path:
        """
        Get path to specific document.

        Args:
            feature_name: Feature name
            document_type: Type of document (requirements, design, tasks, metadata)

        Returns:
            Path to document file
        """
        kebab_name = self._to_kebab_case(feature_name)
        spec_dir = self.base_path / kebab_name

        if document_type == "metadata":
            return spec_dir / "metadata.json"
        else:
            return spec_dir / f"{document_type}.md"

    def _to_kebab_case(self, name: str) -> str:
        """
        Convert name to kebab-case format.

        Args:
            name: Input name

        Returns:
            Kebab-case formatted name
        """
        # Replace spaces and underscores with hyphens
        name = re.sub(r"[\s_]+", "-", name)
        # Convert to lowercase
        name = name.lower()
        # Remove any non-alphanumeric characters except hyphens
        name = re.sub(r"[^a-z0-9-]", "", name)
        # Remove multiple consecutive hyphens
        name = re.sub(r"-+", "-", name)
        # Remove leading/trailing hyphens
        name = name.strip("-")

        return name

    def _create_initial_documents(self, spec_dir: Path) -> None:
        """
        Create initial document templates.

        Args:
            spec_dir: Specification directory path
        """
        # Create requirements.md template
        requirements_template = """# Requirements Document

## Introduction

[Summary of the feature/system]

## Glossary

- **System/Term**: [Definition]

## Requirements

### Requirement 1

**User Story:** As a [role], I want [feature], so that [benefit]

#### Acceptance Criteria

1. WHEN [event], THE [System_Name] SHALL [response]
2. WHILE [state], THE [System_Name] SHALL [response]
3. IF [undesired event], THEN THE [System_Name] SHALL [response]
"""

        # Create design.md template
        design_template = """# Design Document

## Overview

[System overview and purpose]

## Architecture

[System architecture description]

## Components and Interfaces

[Component specifications]

## Data Models

[Data structure definitions]

## Error Handling

[Error handling strategy]

## Testing Strategy

[Testing approach and methods]
"""

        # Create tasks.md template
        tasks_template = """# Implementation Plan

- [ ] 1. [First major task]
  - [Task details and requirements]
  - _Requirements: [requirement references]_

- [ ] 2. [Second major task]
- [ ] 2.1 [Sub-task]
  - [Sub-task details]
  - _Requirements: [requirement references]_
"""

        # Write template files if they don't exist
        templates = {
            "requirements.md": requirements_template,
            "design.md": design_template,
            "tasks.md": tasks_template,
        }

        for filename, content in templates.items():
            file_path = spec_dir / filename
            if not file_path.exists():
                with open(file_path, "w") as f:
                    f.write(content)

    def _update_metadata_timestamp(self, spec_dir: Path) -> None:
        """
        Update the last modified timestamp in metadata.

        Args:
            spec_dir: Specification directory path
        """
        try:
            metadata_file = spec_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

                metadata["last_modified"] = datetime.now().isoformat()

                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)
        except Exception:
            pass  # Fail silently for metadata updates

    def _create_backup_directory(self, feature_name: str) -> Optional[Path]:
        """
        Create backup directory for a specification.

        Args:
            feature_name: Feature name

        Returns:
            Path to backup directory or None if creation failed
        """
        try:
            backup_base = self.base_path / ".backups" / feature_name
            backup_base.mkdir(parents=True, exist_ok=True)
            return backup_base
        except Exception:
            return None

    def create_version_snapshot(self, feature_name: str, version_name: str) -> bool:
        """
        Create a named version snapshot of the entire specification.

        Args:
            feature_name: Feature name
            version_name: Name for this version (e.g., "approved_requirements")

        Returns:
            True if snapshot created successfully
        """
        try:
            kebab_name = self._to_kebab_case(feature_name)
            spec_dir = self.base_path / kebab_name

            if not spec_dir.exists():
                return False

            # Create versions directory
            versions_dir = spec_dir / ".versions"
            versions_dir.mkdir(exist_ok=True)

            # Create version snapshot directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            version_dir = versions_dir / f"{version_name}_{timestamp}"
            version_dir.mkdir(exist_ok=True)

            # Copy all documents to version directory
            for doc_type in ["requirements", "design", "tasks"]:
                source_file = spec_dir / f"{doc_type}.md"
                if source_file.exists():
                    shutil.copy2(source_file, version_dir / f"{doc_type}.md")

            # Copy metadata
            metadata_file = spec_dir / "metadata.json"
            if metadata_file.exists():
                shutil.copy2(metadata_file, version_dir / "metadata.json")

            # Create version info
            version_info = {
                "version_name": version_name,
                "created_at": datetime.now().isoformat(),
                "feature_name": feature_name,
                "description": f"Version snapshot: {version_name}",
            }

            with open(version_dir / "version_info.json", "w") as f:
                json.dump(version_info, f, indent=2)

            return True

        except Exception as e:
            print(f"Error creating version snapshot: {e}")
            return False

    def list_versions(self, feature_name: str) -> List[Dict[str, Any]]:
        """
        List all version snapshots for a specification.

        Args:
            feature_name: Feature name

        Returns:
            List of version information dictionaries
        """
        try:
            kebab_name = self._to_kebab_case(feature_name)
            spec_dir = self.base_path / kebab_name
            versions_dir = spec_dir / ".versions"

            if not versions_dir.exists():
                return []

            versions = []
            for version_dir in versions_dir.iterdir():
                if version_dir.is_dir():
                    version_info_file = version_dir / "version_info.json"
                    if version_info_file.exists():
                        try:
                            with open(version_info_file, "r") as f:
                                version_info = json.load(f)
                            version_info["directory"] = str(version_dir)
                            versions.append(version_info)
                        except json.JSONDecodeError:
                            continue

            # Sort by creation date (newest first)
            versions.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
            return versions

        except Exception:
            return []

    def rollback_to_version(self, feature_name: str, version_name: str) -> bool:
        """
        Rollback specification to a previous version.

        Args:
            feature_name: Feature name
            version_name: Name of version to rollback to

        Returns:
            True if rollback successful
        """
        try:
            kebab_name = self._to_kebab_case(feature_name)
            spec_dir = self.base_path / kebab_name

            # Find the version directory
            versions = self.list_versions(feature_name)
            target_version = None
            for version in versions:
                if version["version_name"] == version_name:
                    target_version = version
                    break

            if not target_version:
                return False

            version_dir = Path(target_version["directory"])
            if not version_dir.exists():
                return False

            # Create backup of current state before rollback
            self.create_version_snapshot(
                feature_name, f"pre_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Restore documents from version
            for doc_type in ["requirements", "design", "tasks"]:
                version_file = version_dir / f"{doc_type}.md"
                target_file = spec_dir / f"{doc_type}.md"

                if version_file.exists():
                    shutil.copy2(version_file, target_file)

            # Restore metadata (but update rollback info)
            version_metadata_file = version_dir / "metadata.json"
            if version_metadata_file.exists():
                with open(version_metadata_file, "r") as f:
                    metadata = json.load(f)

                # Update rollback information
                metadata["last_rollback"] = {
                    "timestamp": datetime.now().isoformat(),
                    "from_version": version_name,
                    "rollback_reason": "Manual rollback",
                }
                metadata["last_modified"] = datetime.now().isoformat()

                with open(spec_dir / "metadata.json", "w") as f:
                    json.dump(metadata, f, indent=2)

            return True

        except Exception as e:
            print(f"Error during rollback: {e}")
            return False

    def get_backup_history(
        self, feature_name: str, document_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get backup history for a specific document.

        Args:
            feature_name: Feature name
            document_type: Type of document

        Returns:
            List of backup information
        """
        try:
            kebab_name = self._to_kebab_case(feature_name)
            backup_dir = self._create_backup_directory(kebab_name)

            if not backup_dir or not backup_dir.exists():
                return []

            backups = []
            pattern = f"{document_type}_*.backup"

            for backup_file in backup_dir.glob(pattern):
                # Extract timestamp from filename
                filename = backup_file.name
                timestamp_part = filename.replace(f"{document_type}_", "").replace(
                    ".backup", ""
                )

                try:
                    # Parse timestamp (try with microseconds first, then without)
                    try:
                        backup_time = datetime.strptime(
                            timestamp_part, "%Y%m%d_%H%M%S_%f"
                        )
                    except ValueError:
                        backup_time = datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")

                    backups.append(
                        {
                            "filename": filename,
                            "path": str(backup_file),
                            "timestamp": backup_time.isoformat(),
                            "size": backup_file.stat().st_size,
                            "document_type": document_type,
                        }
                    )
                except ValueError:
                    continue

            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: str(x["timestamp"]), reverse=True)
            return backups

        except Exception:
            return []

    def restore_from_backup(
        self, feature_name: str, document_type: str, backup_filename: str
    ) -> bool:
        """
        Restore document from a specific backup.

        Args:
            feature_name: Feature name
            document_type: Type of document
            backup_filename: Name of backup file to restore from

        Returns:
            True if restore successful
        """
        try:
            kebab_name = self._to_kebab_case(feature_name)
            spec_dir = self.base_path / kebab_name
            backup_dir = self._create_backup_directory(kebab_name)

            if not backup_dir:
                return False

            backup_file = backup_dir / backup_filename
            if not backup_file.exists():
                return False

            # Create backup of current state before restore
            self.backup_document(feature_name, document_type)

            # Restore from backup
            if document_type == "metadata":
                target_file = spec_dir / "metadata.json"
            else:
                target_file = spec_dir / f"{document_type}.md"

            shutil.copy2(backup_file, target_file)

            # Update metadata
            self._update_metadata_timestamp(spec_dir)

            return True

        except Exception as e:
            print(f"Error restoring from backup: {e}")
            return False

    def _cleanup_old_backups(
        self, backup_dir: Path, document_type: str, max_backups: int = 10
    ) -> None:
        """
        Clean up old backup files, keeping only the most recent ones.

        Args:
            backup_dir: Backup directory path
            document_type: Type of document
            max_backups: Maximum number of backups to keep
        """
        try:
            pattern = f"{document_type}_*.backup"
            backup_files = list(backup_dir.glob(pattern))

            if len(backup_files) <= max_backups:
                return

            # Sort by modification time (oldest first)
            backup_files.sort(key=lambda f: f.stat().st_mtime)

            # Remove oldest files
            files_to_remove = backup_files[:-max_backups]
            for file_to_remove in files_to_remove:
                file_to_remove.unlink()

        except Exception:
            pass  # Fail silently for cleanup operations
