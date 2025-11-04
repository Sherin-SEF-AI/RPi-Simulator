"""
Unit tests for EARS Engine pattern recognition and validation.
"""

import pytest
from packages.feature_planning.ears_engine import EARSEngine
from packages.feature_planning.base import EARSPattern, ValidationResult


class TestEARSEngine:
    """Test cases for EARS Engine functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.ears_engine = EARSEngine()
    
    def test_ubiquitous_pattern_recognition(self):
        """Test recognition of ubiquitous EARS pattern."""
        # Valid ubiquitous patterns
        valid_requirements = [
            "THE System SHALL validate user input",
            "THE Database SHALL maintain data integrity",
            "THE Application SHALL log all transactions"
        ]
        
        for requirement in valid_requirements:
            pattern = self.ears_engine.validate_pattern(requirement)
            assert pattern == EARSPattern.UBIQUITOUS, f"Failed to recognize ubiquitous pattern: {requirement}"
    
    def test_event_driven_pattern_recognition(self):
        """Test recognition of event-driven EARS pattern."""
        # Valid event-driven patterns
        valid_requirements = [
            "WHEN user clicks submit, THE System SHALL validate the form",
            "WHEN timeout occurs, THE Connection SHALL retry automatically",
            "WHEN data is received, THE Parser SHALL process the message"
        ]
        
        for requirement in valid_requirements:
            pattern = self.ears_engine.validate_pattern(requirement)
            assert pattern == EARSPattern.EVENT_DRIVEN, f"Failed to recognize event-driven pattern: {requirement}"
    
    def test_state_driven_pattern_recognition(self):
        """Test recognition of state-driven EARS pattern."""
        # Valid state-driven patterns
        valid_requirements = [
            "WHILE system is offline, THE Cache SHALL store pending requests",
            "WHILE user is authenticated, THE System SHALL allow access",
            "WHILE backup is running, THE Database SHALL queue write operations"
        ]
        
        for requirement in valid_requirements:
            pattern = self.ears_engine.validate_pattern(requirement)
            assert pattern == EARSPattern.STATE_DRIVEN, f"Failed to recognize state-driven pattern: {requirement}"
    
    def test_unwanted_event_pattern_recognition(self):
        """Test recognition of unwanted event EARS pattern."""
        # Valid unwanted event patterns
        valid_requirements = [
            "IF connection fails, THEN THE System SHALL display error message",
            "IF invalid data detected, THEN THE Validator SHALL reject input",
            "IF memory limit exceeded, THEN THE Application SHALL free resources"
        ]
        
        for requirement in valid_requirements:
            pattern = self.ears_engine.validate_pattern(requirement)
            assert pattern == EARSPattern.UNWANTED_EVENT, f"Failed to recognize unwanted event pattern: {requirement}"
    
    def test_optional_feature_pattern_recognition(self):
        """Test recognition of optional feature EARS pattern."""
        # Valid optional feature patterns
        valid_requirements = [
            "WHERE advanced mode is enabled, THE Interface SHALL show debug options",
            "WHERE premium subscription active, THE System SHALL unlock features",
            "WHERE debug logging enabled, THE Logger SHALL record detailed traces"
        ]
        
        for requirement in valid_requirements:
            pattern = self.ears_engine.validate_pattern(requirement)
            assert pattern == EARSPattern.OPTIONAL_FEATURE, f"Failed to recognize optional feature pattern: {requirement}"
    
    def test_complex_pattern_recognition(self):
        """Test recognition of complex EARS pattern."""
        # Valid complex patterns
        valid_requirements = [
            "WHERE debug mode enabled, WHILE system running, WHEN error occurs, THE Logger SHALL record detailed trace",
            "WHILE user authenticated, IF session expires, THEN THE System SHALL redirect to login",
            "WHERE premium active, WHEN user requests feature, THE System SHALL grant access"
        ]
        
        for requirement in valid_requirements:
            pattern = self.ears_engine.validate_pattern(requirement)
            assert pattern == EARSPattern.COMPLEX, f"Failed to recognize complex pattern: {requirement}"
    
    def test_invalid_pattern_recognition(self):
        """Test handling of invalid or non-EARS patterns."""
        # Invalid patterns
        invalid_requirements = [
            "System should validate input",  # Missing SHALL
            "The system will process data",  # Wrong modal verb
            "User can enter data",  # Not a system requirement
            "",  # Empty string
            "Random text without structure"
        ]
        
        for requirement in invalid_requirements:
            pattern = self.ears_engine.validate_pattern(requirement)
            assert pattern is None, f"Incorrectly recognized pattern for invalid requirement: {requirement}"
    
    def test_validation_success(self):
        """Test successful validation of EARS-compliant requirements."""
        valid_requirement = "WHEN user clicks submit, THE System SHALL validate the form"
        
        result = self.ears_engine.validate(valid_requirement)
        
        assert result.is_valid is True
        assert result.pattern == EARSPattern.EVENT_DRIVEN
        assert len(result.issues) == 0
        assert len(result.suggestions) == 0
    
    def test_validation_failure(self):
        """Test validation failure for non-compliant requirements."""
        invalid_requirement = "System should validate input"
        
        result = self.ears_engine.validate(invalid_requirement)
        
        assert result.is_valid is False
        assert result.pattern is None
        assert len(result.issues) > 0
        assert len(result.suggestions) > 0
    
    def test_empty_requirement_validation(self):
        """Test validation of empty requirements."""
        result = self.ears_engine.validate("")
        
        assert result.is_valid is False
        assert "Empty requirement" in result.issues
        assert result.pattern is None
    
    def test_suggestion_generation(self):
        """Test suggestion generation for non-compliant requirements."""
        # Test different types of partial requirements
        test_cases = [
            ("System validates input", ["SHALL"]),  # Missing SHALL
            ("User can enter data", ["THE", "WHEN", "WHILE"]),  # Missing proper structure
            ("WHEN error occurs, system handles it", ["SHALL"]),  # Missing SHALL
        ]
        
        for requirement, expected_keywords in test_cases:
            suggestions = self.ears_engine.get_suggestions(requirement)
            
            assert len(suggestions) > 0, f"No suggestions generated for: {requirement}"
            
            # Check that suggestions contain expected keywords
            suggestions_text = " ".join(suggestions).upper()
            for keyword in expected_keywords:
                assert keyword in suggestions_text, f"Missing keyword '{keyword}' in suggestions for: {requirement}"
    
    def test_user_story_formatting(self):
        """Test formatting of user stories into EARS requirements."""
        user_story = "As a developer, I want to save project data, so that I can preserve my work"
        
        criteria = self.ears_engine.format_requirement(user_story)
        
        assert len(criteria) > 0, "No acceptance criteria generated"
        
        # Check that at least one criterion is EARS-compliant
        valid_criteria = []
        for criterion in criteria:
            if self.ears_engine.validate_pattern(criterion):
                valid_criteria.append(criterion)
        
        assert len(valid_criteria) > 0, "No EARS-compliant criteria generated"
    
    def test_invalid_user_story_formatting(self):
        """Test handling of invalid user story format."""
        invalid_story = "I want to do something"
        
        criteria = self.ears_engine.format_requirement(invalid_story)
        
        assert len(criteria) > 0
        assert "Invalid user story format" in criteria[0]
    
    def test_bulk_compliance_checking(self):
        """Test bulk compliance checking for multiple requirements."""
        requirements = [
            "THE System SHALL validate user input",  # Valid
            "WHEN user clicks submit, THE System SHALL process form",  # Valid
            "System should handle errors",  # Invalid
            "WHILE authenticated, THE User SHALL access features",  # Valid
        ]
        
        result = self.ears_engine.check_compliance(requirements)
        
        # Should have 75% compliance (3/4 valid)
        assert result.is_valid is False  # Below 80% threshold
        assert len(result.issues) > 0
        assert "Requirement 3:" in " ".join(result.issues)  # Should identify the invalid requirement
    
    def test_empty_requirements_list(self):
        """Test bulk compliance checking with empty list."""
        result = self.ears_engine.check_compliance([])
        
        assert result.is_valid is False
        assert "No requirements provided" in result.issues
    
    def test_clause_ordering_validation(self):
        """Test clause ordering validation for complex patterns."""
        # Valid ordering
        valid_complex = "WHERE debug enabled, WHILE system running, WHEN error occurs, THE Logger SHALL record trace"
        result = self.ears_engine.validate(valid_complex)
        assert result.is_valid is True
        
        # Invalid ordering (WHEN before WHILE)
        invalid_complex = "WHERE debug enabled, WHEN error occurs, WHILE system running, THE Logger SHALL record trace"
        result = self.ears_engine.validate(invalid_complex)
        assert result.is_valid is False
        assert len(result.issues) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])