"""
Unit tests for Design Generator functionality.
"""

import pytest
from packages.feature_planning.design_generator import DesignGenerator, ResearchFinding, TechnicalDecision
from packages.feature_planning.base import Requirement, EARSPattern, ValidationStatus


class TestDesignGenerator:
    """Test cases for Design Generator functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.design_generator = DesignGenerator()
        
        # Create sample requirements for testing
        self.sample_requirements = [
            Requirement(
                id="1.1",
                user_story="As a developer, I want to validate requirements, so that I can ensure quality",
                acceptance_criteria=[
                    "WHEN requirements are provided, THE System SHALL validate EARS patterns",
                    "THE System SHALL check INCOSE compliance"
                ],
                ears_pattern=EARSPattern.EVENT_DRIVEN,
                referenced_terms=["System", "EARS", "INCOSE"],
                validation_status=ValidationStatus.VALID
            ),
            Requirement(
                id="2.1",
                user_story="As a developer, I want to generate designs, so that I can create technical specifications",
                acceptance_criteria=[
                    "THE Design_Generator SHALL create architecture documentation",
                    "THE Design_Generator SHALL define component interfaces"
                ],
                ears_pattern=EARSPattern.UBIQUITOUS,
                referenced_terms=["Design_Generator"],
                validation_status=ValidationStatus.VALID
            )
        ]
    
    def test_validate_input_valid_requirements(self):
        """Test input validation with valid requirements."""
        result = self.design_generator.validate_input(self.sample_requirements)
        assert result is True
    
    def test_validate_input_empty_requirements(self):
        """Test input validation with empty requirements list."""
        result = self.design_generator.validate_input([])
        assert result is False
    
    def test_validate_input_invalid_status(self):
        """Test input validation with invalid requirement status."""
        invalid_req = Requirement(
            id="1.1",
            user_story="Test story",
            acceptance_criteria=["Test criteria"],
            ears_pattern=EARSPattern.UBIQUITOUS,
            referenced_terms=[],
            validation_status=ValidationStatus.INVALID
        )
        
        result = self.design_generator.validate_input([invalid_req])
        assert result is False
    
    def test_validate_input_missing_fields(self):
        """Test input validation with missing required fields."""
        invalid_req = Requirement(
            id="1.1",
            user_story="",  # Empty user story
            acceptance_criteria=[],  # Empty criteria
            ears_pattern=EARSPattern.UBIQUITOUS,
            referenced_terms=[],
            validation_status=ValidationStatus.VALID
        )
        
        result = self.design_generator.validate_input([invalid_req])
        assert result is False
    
    def test_extract_components(self):
        """Test component extraction from requirements."""
        components = self.design_generator._extract_components(self.sample_requirements)
        
        assert len(components) > 0
        assert isinstance(components, list)
        
        # Should extract components based on keywords
        component_names = " ".join(components).lower()
        assert any(keyword in component_names for keyword in ['generator', 'validator', 'engine'])
    
    def test_generate_architecture(self):
        """Test architecture documentation generation."""
        architecture_doc = self.design_generator.generate_architecture(self.sample_requirements)
        
        assert len(architecture_doc) > 0
        assert "### Core Components" in architecture_doc
        assert "```mermaid" in architecture_doc
        assert "graph TB" in architecture_doc
        assert "### Component Descriptions" in architecture_doc
    
    def test_create_interfaces(self):
        """Test interface specification creation."""
        components = ["Requirements Validator", "Design Generator"]
        interface_doc = self.design_generator.create_interfaces(components)
        
        assert len(interface_doc) > 0
        assert "## Components and Interfaces" in interface_doc
        assert "### Requirements Validator" in interface_doc
        assert "### Design Generator" in interface_doc
        assert "**Purpose**:" in interface_doc
        assert "**Interface**:" in interface_doc
        assert "```python" in interface_doc
    
    def test_define_data_models(self):
        """Test data model definition."""
        entities = ["Requirement", "Design Document", "Task"]
        data_model_doc = self.design_generator.define_data_models(entities)
        
        assert len(data_model_doc) > 0
        assert "## Data Models" in data_model_doc
        assert "### Requirement Model" in data_model_doc
        assert "@dataclass" in data_model_doc
        assert "```python" in data_model_doc
    
    def test_generate_overview(self):
        """Test overview generation from requirements."""
        overview = self.design_generator._generate_overview(self.sample_requirements)
        
        assert len(overview) > 0
        assert "system" in overview.lower()
        assert "component" in overview.lower()
    
    def test_extract_entities(self):
        """Test entity extraction from requirements."""
        entities = self.design_generator._extract_entities(self.sample_requirements)
        
        assert len(entities) > 0
        assert isinstance(entities, list)
        
        # Should include common entities
        entity_names = " ".join(entities).lower()
        assert any(keyword in entity_names for keyword in ['requirement', 'design', 'task'])
    
    def test_add_research_finding(self):
        """Test adding research findings."""
        initial_count = len(self.design_generator.research_findings)
        
        self.design_generator.add_research_finding(
            topic="Architecture Patterns",
            finding="Modular architecture improves maintainability",
            source="Software Engineering Best Practices",
            relevance="Applies to component design",
            impact="Influences component separation strategy"
        )
        
        assert len(self.design_generator.research_findings) == initial_count + 1
        
        finding = self.design_generator.research_findings[-1]
        assert finding.topic == "Architecture Patterns"
        assert finding.finding == "Modular architecture improves maintainability"
    
    def test_add_technical_decision(self):
        """Test adding technical decisions."""
        initial_count = len(self.design_generator.technical_decisions)
        
        self.design_generator.add_technical_decision(
            decision="Use dependency injection",
            rationale="Improves testability and flexibility",
            alternatives=["Direct instantiation", "Factory pattern"],
            trade_offs="Increased complexity but better maintainability",
            requirements_refs=["1.1", "2.1"]
        )
        
        assert len(self.design_generator.technical_decisions) == initial_count + 1
        
        decision = self.design_generator.technical_decisions[-1]
        assert decision.decision == "Use dependency injection"
        assert "1.1" in decision.requirements_refs
    
    def test_incorporate_research_findings_empty(self):
        """Test research findings incorporation with no findings."""
        result = self.design_generator.incorporate_research_findings(self.sample_requirements)
        assert result == ""
    
    def test_incorporate_research_findings_with_data(self):
        """Test research findings incorporation with data."""
        self.design_generator.add_research_finding(
            topic="Test Topic",
            finding="Test finding",
            source="Test source",
            relevance="Test relevance",
            impact="Test impact"
        )
        
        result = self.design_generator.incorporate_research_findings(self.sample_requirements)
        
        assert len(result) > 0
        assert "## Research Findings" in result
        assert "### Test Topic" in result
        assert "**Finding**: Test finding" in result
    
    def test_document_technical_decisions(self):
        """Test technical decisions documentation."""
        result = self.design_generator.document_technical_decisions(self.sample_requirements)
        
        assert len(result) > 0
        assert "## Technical Decisions" in result
        assert "### Decision" in result
        assert "**Rationale**:" in result
    
    def test_generate_error_handling_strategy(self):
        """Test error handling strategy generation."""
        result = self.design_generator.generate_error_handling_strategy(self.sample_requirements)
        
        assert len(result) > 0
        assert "## Error Handling" in result
        assert "### Validation Errors" in result
        assert "### Workflow Errors" in result
        assert "### Recovery Strategies" in result
    
    def test_plan_testing_strategy(self):
        """Test testing strategy planning."""
        result = self.design_generator.plan_testing_strategy(self.sample_requirements)
        
        assert len(result) > 0
        assert "## Testing Strategy" in result
        assert "### Unit Testing" in result
        assert "### Integration Testing" in result
        assert "### Validation Testing" in result
    
    def test_generate_complete_design(self):
        """Test complete design document generation."""
        result = self.design_generator.generate(self.sample_requirements)
        
        assert len(result) > 0
        assert "# Design Document" in result
        assert "## Overview" in result
        assert "## Architecture" in result
        assert "## Components and Interfaces" in result
        assert "## Data Models" in result
        assert "## Technical Decisions" in result
        assert "## Error Handling" in result
        assert "## Testing Strategy" in result
    
    def test_generate_with_invalid_input(self):
        """Test design generation with invalid input."""
        invalid_req = Requirement(
            id="1.1",
            user_story="",
            acceptance_criteria=[],
            ears_pattern=EARSPattern.UBIQUITOUS,
            referenced_terms=[],
            validation_status=ValidationStatus.INVALID
        )
        
        with pytest.raises(ValueError, match="Invalid requirements provided"):
            self.design_generator.generate([invalid_req])
    
    def test_component_description_generation(self):
        """Test component description generation."""
        description = self.design_generator._generate_component_description(
            "Requirements Validator", 
            self.sample_requirements
        )
        
        assert len(description) > 0
        assert "validate" in description.lower()
    
    def test_component_purpose_generation(self):
        """Test component purpose generation."""
        purpose = self.design_generator._generate_component_purpose("EARS Engine")
        
        assert len(purpose) > 0
        assert "ears" in purpose.lower() or "pattern" in purpose.lower()
    
    def test_interface_code_generation(self):
        """Test interface code generation."""
        code = self.design_generator._generate_interface_code("Requirements Validator")
        
        assert len(code) > 0
        assert "class" in code
        assert "def " in code
        assert "RequirementsValidator" in code
    
    def test_key_methods_generation(self):
        """Test key methods generation."""
        methods = self.design_generator._generate_key_methods("EARS Engine")
        
        assert len(methods) > 0
        assert isinstance(methods, list)
        assert all(isinstance(method, str) for method in methods)
    
    def test_data_model_code_generation(self):
        """Test data model code generation."""
        code = self.design_generator._generate_data_model_code("Requirement")
        
        assert len(code) > 0
        assert "@dataclass" in code
        assert "class Requirement:" in code
        assert "id: str" in code
    
    def test_validation_errors_identification(self):
        """Test validation errors identification."""
        errors = self.design_generator._identify_validation_errors(self.sample_requirements)
        
        assert len(errors) > 0
        assert all('type' in error and 'description' in error for error in errors)
    
    def test_workflow_errors_identification(self):
        """Test workflow errors identification."""
        errors = self.design_generator._identify_workflow_errors(self.sample_requirements)
        
        assert len(errors) > 0
        assert all('type' in error and 'description' in error for error in errors)
    
    def test_recovery_strategies_generation(self):
        """Test recovery strategies generation."""
        strategies = self.design_generator._generate_recovery_strategies(self.sample_requirements)
        
        assert len(strategies) > 0
        assert all('scenario' in strategy and 'strategy' in strategy for strategy in strategies)
    
    def test_unit_testing_strategy_generation(self):
        """Test unit testing strategy generation."""
        tests = self.design_generator._generate_unit_testing_strategy(self.sample_requirements)
        
        assert len(tests) > 0
        assert isinstance(tests, list)
        assert all(isinstance(test, str) for test in tests)
    
    def test_integration_testing_strategy_generation(self):
        """Test integration testing strategy generation."""
        tests = self.design_generator._generate_integration_testing_strategy(self.sample_requirements)
        
        assert len(tests) > 0
        assert isinstance(tests, list)
        assert all(isinstance(test, str) for test in tests)
    
    def test_validation_testing_strategy_generation(self):
        """Test validation testing strategy generation."""
        tests = self.design_generator._generate_validation_testing_strategy(self.sample_requirements)
        
        assert len(tests) > 0
        assert isinstance(tests, list)
        assert all(isinstance(test, str) for test in tests)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])