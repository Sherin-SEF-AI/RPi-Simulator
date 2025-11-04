"""
Unit tests for Requirements Validator INCOSE compliance checking.

Tests all INCOSE quality rules, glossary management, and validation scenarios.
"""

import pytest
from packages.feature_planning.requirements_validator import RequirementsValidator
from packages.feature_planning.base import ValidationResult, QualityIssue


class TestRequirementsValidator:
    """Test suite for Requirements Validator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = RequirementsValidator()
    
    def test_active_voice_detection(self):
        """Test active voice validation."""
        # Valid active voice
        valid_req = "THE System SHALL validate user input"
        result = self.validator.validate(valid_req)
        active_voice_issues = [issue for issue in self.validator.check_incose_rules(valid_req) 
                              if issue.rule == "active_voice"]
        assert len(active_voice_issues) == 0
        
        # Invalid passive voice
        passive_req = "User input SHALL be validated by the system"
        passive_issues = self.validator.check_incose_rules(passive_req)
        active_voice_issues = [issue for issue in passive_issues if issue.rule == "active_voice"]
        assert len(active_voice_issues) > 0
        assert "passive voice" in active_voice_issues[0].description.lower()
        
        # "SHALL be" construction
        shall_be_req = "THE data SHALL be processed correctly"
        shall_be_issues = self.validator.check_incose_rules(shall_be_req)
        active_voice_issues = [issue for issue in shall_be_issues if issue.rule == "active_voice"]
        assert len(active_voice_issues) > 0
    
    def test_vague_terms_detection(self):
        """Test detection of vague and subjective terms."""
        # Valid specific requirement
        specific_req = "THE System SHALL respond within 200 milliseconds"
        result = self.validator.validate(specific_req)
        vague_issues = [issue for issue in self.validator.check_incose_rules(specific_req) 
                       if issue.rule == "no_vague_terms"]
        assert len(vague_issues) == 0
        
        # Invalid vague terms
        vague_requirements = [
            "THE System SHALL respond quickly",
            "THE Interface SHALL be user-friendly",
            "THE Database SHALL provide adequate performance",
            "THE Security SHALL be robust and reliable"
        ]
        
        for req in vague_requirements:
            issues = self.validator.check_incose_rules(req)
            vague_issues = [issue for issue in issues if issue.rule == "no_vague_terms"]
            assert len(vague_issues) > 0, f"Expected vague terms in: {req}"
            # Check that at least one vague term is detected
            found_vague_terms = []
            for issue in vague_issues:
                if ('quickly' in issue.description or 'adequate' in issue.description or 
                    'robust' in issue.description or 'reliable' in issue.description or
                    'user-friendly' in issue.description):
                    found_vague_terms.append(issue.description)
            assert len(found_vague_terms) > 0, f"No expected vague terms found in issues: {[i.description for i in vague_issues]}"
    
    def test_escape_clauses_detection(self):
        """Test detection of escape clauses."""
        # Valid requirement without escape clauses
        valid_req = "THE System SHALL validate all user input before processing"
        result = self.validator.validate(valid_req)
        escape_issues = [issue for issue in self.validator.check_incose_rules(valid_req) 
                        if issue.rule == "no_escape_clauses"]
        assert len(escape_issues) == 0
        
        # Invalid requirements with escape clauses
        escape_requirements = [
            "THE System SHALL validate input where possible",
            "THE Database SHALL backup data if feasible",
            "THE Interface SHALL display warnings when necessary",
            "THE Security SHALL encrypt data as appropriate"
        ]
        
        for req in escape_requirements:
            issues = self.validator.check_incose_rules(req)
            escape_issues = [issue for issue in issues if issue.rule == "no_escape_clauses"]
            assert len(escape_issues) > 0
            assert "escape clause" in escape_issues[0].description.lower()
    
    def test_negative_statements_detection(self):
        """Test detection of negative requirements."""
        # Valid positive requirement
        positive_req = "THE System SHALL maintain 99.9% uptime"
        result = self.validator.validate(positive_req)
        negative_issues = [issue for issue in self.validator.check_incose_rules(positive_req) 
                          if issue.rule == "no_negatives"]
        assert len(negative_issues) == 0
        
        # Invalid negative requirements
        negative_requirements = [
            "THE System SHALL NOT crash during operation",
            "THE Database WILL NOT lose data",
            "THE Interface MUST NOT confuse users",
            "THE Security CANNOT be compromised"
        ]
        
        for req in negative_requirements:
            issues = self.validator.check_incose_rules(req)
            negative_issues = [issue for issue in issues if issue.rule == "no_negatives"]
            assert len(negative_issues) > 0
            assert "negative requirement" in negative_issues[0].description.lower()
    
    def test_single_thought_detection(self):
        """Test detection of multiple thoughts in requirements."""
        # Valid single thought
        single_req = "THE System SHALL validate user credentials"
        result = self.validator.validate(single_req)
        single_issues = [issue for issue in self.validator.check_incose_rules(single_req) 
                        if issue.rule == "single_thought"]
        assert len(single_issues) == 0
        
        # Invalid multiple thoughts with excessive ANDs
        multiple_and_req = "THE System SHALL validate input AND store data AND send notifications AND log events"
        and_issues = self.validator.check_incose_rules(multiple_and_req)
        single_issues = [issue for issue in and_issues if issue.rule == "single_thought"]
        assert len(single_issues) > 0
        assert "AND" in single_issues[0].description
        
        # Invalid multiple thoughts with OR
        or_req = "THE System SHALL validate input OR reject the request"
        or_issues = self.validator.check_incose_rules(or_req)
        single_issues = [issue for issue in or_issues if issue.rule == "single_thought"]
        assert len(single_issues) > 0
        assert "OR" in single_issues[0].description
    
    def test_measurability_detection(self):
        """Test detection of measurability issues."""
        # Valid measurable requirements
        measurable_requirements = [
            "THE System SHALL respond within 200 milliseconds",
            "THE Database SHALL store at least 1000 records",
            "THE Interface SHALL display all menu items"
        ]
        
        for req in measurable_requirements:
            result = self.validator.validate(req)
            measurable_issues = [issue for issue in self.validator.check_incose_rules(req) 
                               if issue.rule == "measurable"]
            assert len(measurable_issues) == 0
        
        # Invalid unmeasurable performance requirements
        unmeasurable_req = "THE System SHALL provide good performance"
        issues = self.validator.check_incose_rules(unmeasurable_req)
        measurable_issues = [issue for issue in issues if issue.rule == "measurable"]
        assert len(measurable_issues) > 0
        assert "measurable criteria" in measurable_issues[0].description.lower()
    
    def test_completeness_validation(self):
        """Test requirements set completeness checking."""
        # Valid requirements set
        valid_requirements = [
            "THE System SHALL validate user input",
            "THE Database SHALL store validated data",
            "THE Interface SHALL display confirmation messages"
        ]
        result = self.validator.ensure_completeness(valid_requirements)
        assert result.is_valid
        
        # Empty requirements
        empty_result = self.validator.ensure_completeness([])
        assert not empty_result.is_valid
        assert "No requirements provided" in empty_result.issues
        
        # Duplicate requirements
        duplicate_requirements = [
            "THE System SHALL validate user input",
            "THE System SHALL validate user input",  # Duplicate
            "THE Database SHALL store data"
        ]
        duplicate_result = self.validator.ensure_completeness(duplicate_requirements)
        assert not duplicate_result.is_valid
        assert any("duplicate" in issue.lower() for issue in duplicate_result.issues)
        
        # Requirements without SHALL
        no_shall_requirements = [
            "THE System validates user input",  # Missing SHALL
            "THE Database SHALL store data"
        ]
        no_shall_result = self.validator.ensure_completeness(no_shall_requirements)
        assert not no_shall_result.is_valid
        assert any("shall" in issue.lower() for issue in no_shall_result.issues)


class TestGlossaryValidation:
    """Test suite for glossary validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = RequirementsValidator()
    
    def test_valid_glossary(self):
        """Test validation of valid glossary."""
        valid_glossary = {
            "System": "The main software application that processes user requests",
            "Database": "PostgreSQL database that stores application data",
            "User_Interface": "Web-based interface for user interaction"
        }
        
        result = self.validator.validate_glossary(valid_glossary)
        assert result.is_valid
        assert len(result.issues) == 0
    
    def test_empty_glossary(self):
        """Test validation of empty glossary."""
        result = self.validator.validate_glossary({})
        assert not result.is_valid
        assert "Empty glossary" in result.issues[0]
    
    def test_invalid_terms_and_definitions(self):
        """Test validation of invalid terms and definitions."""
        invalid_glossary = {
            "": "Empty term name",  # Empty term
            "A": "Too short definition",  # Too short term
            "System": "",  # Empty definition
            "DB": "Short",  # Too short definition
            "Circular": "Circular definition that defines circular"  # Circular definition
        }
        
        result = self.validator.validate_glossary(invalid_glossary)
        assert not result.is_valid
        assert len(result.issues) > 0
        
        # Check specific issues
        issues_text = " ".join(result.issues)
        assert "empty term" in issues_text.lower()
        assert "too short" in issues_text.lower()
        assert "empty definition" in issues_text.lower()
        assert "circular" in issues_text.lower()
    
    def test_vague_definitions(self):
        """Test detection of vague terms in definitions."""
        vague_glossary = {
            "System": "A fast and reliable application that provides good performance",
            "Database": "An adequate storage solution for the system"
        }
        
        result = self.validator.validate_glossary(vague_glossary)
        assert not result.is_valid
        
        issues_text = " ".join(result.issues)
        assert "vague terms" in issues_text.lower()
    
    def test_circular_definitions(self):
        """Test detection of circular references in glossary."""
        circular_glossary = {
            "System": "The main component that interacts with the Database",
            "Database": "Storage component used by the System",
            "Interface": "User interface for the System"
        }
        
        result = self.validator.validate_glossary(circular_glossary)
        # This should detect circular reference between System and Database
        issues_text = " ".join(result.issues)
        assert "circular reference" in issues_text.lower()
    
    def test_technical_term_detection(self):
        """Test automatic detection of technical terms."""
        requirements_text = """
        THE User_Management_System SHALL validate user credentials.
        WHEN API request received, THE Authentication_Service SHALL verify tokens.
        THE Database SHALL store user data in JSON format.
        """
        
        detected_terms = self.validator.detect_technical_terms(requirements_text)
        
        # Should detect system names and technical terms
        assert "User_Management_System" in detected_terms
        assert "Authentication_Service" in detected_terms
        assert "JSON" in detected_terms
    
    def test_glossary_consistency_checking(self):
        """Test consistency between requirements and glossary."""
        requirements_text = """
        THE User_System SHALL validate credentials.
        THE Database SHALL store user data.
        THE API_Gateway SHALL handle requests.
        """
        
        # Glossary missing some terms and having unused terms
        glossary = {
            "Database": "PostgreSQL database for data storage",
            "Unused_Term": "This term is not used in requirements"
        }
        
        result = self.validator.check_glossary_consistency(requirements_text, glossary)
        assert not result.is_valid
        
        issues_text = " ".join(result.issues)
        assert "not in glossary" in issues_text.lower()
        assert "not used in requirements" in issues_text.lower()
    
    def test_inconsistent_capitalization(self):
        """Test detection of inconsistent term capitalization."""
        requirements_text = """
        THE System SHALL validate input.
        THE system SHALL store data.
        THE SYSTEM SHALL process requests.
        """
        
        glossary = {"System": "Main application system"}
        
        result = self.validator.check_glossary_consistency(requirements_text, glossary)
        issues_text = " ".join(result.issues)
        assert "inconsistent capitalization" in issues_text.lower()


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = RequirementsValidator()
    
    def test_complex_requirement_validation(self):
        """Test validation of complex requirements with multiple issues."""
        complex_req = """
        THE system SHALL quickly process user input where possible 
        AND validate data AND store information OR reject the request 
        if it cannot be handled adequately
        """
        
        issues = self.validator.check_incose_rules(complex_req)
        
        # Should detect multiple issues
        rule_types = {issue.rule for issue in issues}
        assert "no_vague_terms" in rule_types  # "quickly", "adequately"
        assert "no_escape_clauses" in rule_types  # "where possible"
        assert "single_thought" in rule_types  # Multiple AND/OR
    
    def test_well_formed_requirement(self):
        """Test validation of well-formed INCOSE-compliant requirement."""
        good_req = "THE Authentication_System SHALL verify user credentials within 2 seconds"
        
        result = self.validator.validate(good_req)
        assert result.is_valid
        assert len(result.issues) == 0
    
    def test_validation_suggestions(self):
        """Test that appropriate suggestions are provided."""
        poor_req = "THE system SHALL NOT be slow and SHALL work adequately where possible"
        
        suggestions = self.validator.get_suggestions(poor_req)
        assert len(suggestions) > 0
        
        suggestions_text = " ".join(suggestions).lower()
        assert "active voice" in suggestions_text or "specific" in suggestions_text
        assert "positive requirement" in suggestions_text
        assert "escape clause" in suggestions_text or "remove" in suggestions_text


if __name__ == "__main__":
    pytest.main([__file__])