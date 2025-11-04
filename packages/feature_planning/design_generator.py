"""
Design Generator for technical specifications.

This module creates detailed technical designs from approved requirements,
including architecture, interfaces, and testing strategies.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base import BaseGenerator, Requirement, ValidationStatus
from .config import get_config


@dataclass
class ResearchFinding:
    """Research finding with source and relevance."""

    topic: str
    finding: str
    source: str
    relevance: str
    impact: str


@dataclass
class TechnicalDecision:
    """Technical decision with rationale and alternatives."""

    decision: str
    rationale: str
    alternatives: List[str]
    trade_offs: str
    requirements_refs: List[str]


class DesignGenerator(BaseGenerator):
    """
    Generates detailed technical designs from requirements.

    Creates architecture documentation, interface specifications,
    and testing strategies based on approved requirements.
    """

    def __init__(self) -> None:
        """Initialize Design Generator with configuration."""
        self.config = get_config()
        self.research_findings: List[ResearchFinding] = []
        self.technical_decisions: List[TechnicalDecision] = []

    def generate(self, input_data: List[Requirement]) -> str:
        """
        Generate complete design document from requirements.

        Args:
            input_data: List of approved requirements

        Returns:
            Generated design document content
        """
        if not self.validate_input(input_data):
            raise ValueError("Invalid requirements provided for design generation")

        design_doc = []

        # Generate overview
        design_doc.append("# Design Document\n")
        design_doc.append("## Overview\n")
        design_doc.append(self._generate_overview(input_data))
        design_doc.append("\n")

        # Generate architecture
        design_doc.append("## Architecture\n")
        components = self._extract_components(input_data)
        design_doc.append(self.generate_architecture(input_data))
        design_doc.append("\n")

        # Generate interfaces
        design_doc.append(self.create_interfaces(components))
        design_doc.append("\n")

        # Generate data models
        entities = self._extract_entities(input_data)
        design_doc.append(self.define_data_models(entities))
        design_doc.append("\n")

        # Generate research findings if available
        research_section = self.incorporate_research_findings(input_data)
        if research_section:
            design_doc.append(research_section)
            design_doc.append("\n")

        # Generate technical decisions
        decisions_section = self.document_technical_decisions(input_data)
        design_doc.append(decisions_section)
        design_doc.append("\n")

        # Generate error handling strategy
        error_handling_section = self.generate_error_handling_strategy(input_data)
        design_doc.append(error_handling_section)
        design_doc.append("\n")

        # Generate testing strategy
        testing_section = self.plan_testing_strategy(input_data)
        design_doc.append(testing_section)
        design_doc.append("\n")

        return "\n".join(design_doc)

    def validate_input(self, input_data: List[Requirement]) -> bool:
        """
        Validate requirements before design generation.

        Args:
            input_data: Requirements to validate

        Returns:
            True if requirements are valid for design generation
        """
        if not input_data:
            return False

        # Check that all requirements have valid status
        for req in input_data:
            if req.validation_status != ValidationStatus.VALID:
                return False

            # Check required fields
            if not req.user_story or not req.acceptance_criteria:
                return False

        return True

    def generate_architecture(self, requirements: List[Requirement]) -> str:
        """
        Generate architecture documentation from requirements.

        Args:
            requirements: List of requirements to analyze

        Returns:
            Architecture documentation content
        """
        components = self._extract_components(requirements)
        relationships = self._analyze_relationships(components, requirements)

        architecture_doc = []
        architecture_doc.append("### Core Components\n")

        # Generate Mermaid diagram
        architecture_doc.append("```mermaid")
        architecture_doc.append("graph TB")

        # Add main system node
        architecture_doc.append("    A[Feature System] --> B[Core Components]")

        # Add component nodes
        for i, component in enumerate(components, start=1):
            node_id = chr(66 + i)  # B, C, D, etc.
            architecture_doc.append(f"    B --> {node_id}[{component}]")

        # Add relationships
        for rel in relationships:
            architecture_doc.append(f"    {rel}")

        architecture_doc.append("```\n")

        # Add component descriptions
        architecture_doc.append("### Component Descriptions\n")
        for component in components:
            description = self._generate_component_description(component, requirements)
            architecture_doc.append(f"**{component}**: {description}\n")

        return "\n".join(architecture_doc)

    def create_interfaces(self, components: List[str]) -> str:
        """
        Create interface specifications for components.

        Args:
            components: List of identified components

        Returns:
            Interface specification content
        """
        interface_doc = []
        interface_doc.append("## Components and Interfaces\n")

        for component in components:
            interface_doc.append(f"### {component}\n")

            # Generate purpose and interface
            purpose = self._generate_component_purpose(component)
            interface_doc.append(f"**Purpose**: {purpose}\n")

            # Generate interface definition
            interface_code = self._generate_interface_code(component)
            interface_doc.append("**Interface**:")
            interface_doc.append("```python")
            interface_doc.append(interface_code)
            interface_doc.append("```\n")

            # Generate key methods
            methods = self._generate_key_methods(component)
            if methods:
                interface_doc.append("**Key Methods**:")
                for method in methods:
                    interface_doc.append(f"- {method}")
                interface_doc.append("")

        return "\n".join(interface_doc)

    def define_data_models(self, entities: List[str]) -> str:
        """
        Define data models and relationships.

        Args:
            entities: List of identified data entities

        Returns:
            Data model specification content
        """
        data_model_doc = []
        data_model_doc.append("## Data Models\n")

        for entity in entities:
            data_model_doc.append(f"### {entity} Model")

            # Generate dataclass definition
            model_code = self._generate_data_model_code(entity)
            data_model_doc.append("```python")
            data_model_doc.append(model_code)
            data_model_doc.append("```\n")

        return "\n".join(data_model_doc)

    def plan_testing_strategy(self, requirements: List[Requirement]) -> str:
        """
        Plan testing strategy and validation methods.

        Args:
            requirements: Requirements to create tests for

        Returns:
            Testing strategy documentation
        """
        testing_doc = []
        testing_doc.append("## Testing Strategy\n")

        # Unit testing strategy
        testing_doc.append("### Unit Testing")
        unit_tests = self._generate_unit_testing_strategy(requirements)
        for test in unit_tests:
            testing_doc.append(f"- {test}")
        testing_doc.append("")

        # Integration testing strategy
        testing_doc.append("### Integration Testing")
        integration_tests = self._generate_integration_testing_strategy(requirements)
        for test in integration_tests:
            testing_doc.append(f"- {test}")
        testing_doc.append("")

        # Validation testing strategy
        testing_doc.append("### Validation Testing")
        validation_tests = self._generate_validation_testing_strategy(requirements)
        for test in validation_tests:
            testing_doc.append(f"- {test}")
        testing_doc.append("")

        return "\n".join(testing_doc)

    def _extract_components(self, requirements: List[Requirement]) -> List[str]:
        """Extract system components from requirements."""
        components = set()

        # Common component patterns based on requirement analysis
        component_keywords = {
            "validator": "Requirements Validator",
            "generator": "Design Generator",
            "manager": "Spec Manager",
            "engine": "EARS Engine",
            "planner": "Task Planner",
            "controller": "Workflow Controller",
        }

        # Extract from user stories and acceptance criteria
        for req in requirements:
            text = (req.user_story + " " + " ".join(req.acceptance_criteria)).lower()
            for keyword, component in component_keywords.items():
                if keyword in text:
                    components.add(component)

        # Add core components if not found
        if not components:
            components.update(["Core Engine", "Document Manager", "Validation System"])

        return sorted(list(components))

    def _analyze_relationships(
        self, components: List[str], requirements: List[Requirement]
    ) -> List[str]:
        """Analyze relationships between components."""
        relationships = []

        # Generate basic relationships based on component types
        for i, component in enumerate(components):
            if i < len(components) - 1:
                node_from = chr(67 + i)  # C, D, E, etc.
                node_to = chr(68 + i)  # D, E, F, etc.
                relationships.append(f"    {node_from} --> {node_to}")

        return relationships

    def _generate_component_description(
        self, component: str, requirements: List[Requirement]
    ) -> str:
        """Generate description for a component based on requirements."""
        descriptions = {
            "Requirements Validator": "Validates requirements against EARS patterns and INCOSE quality rules",
            "Design Generator": "Creates detailed technical designs from approved requirements",
            "Spec Manager": "Manages specification documents and their lifecycle",
            "EARS Engine": "Processes and validates EARS requirement patterns",
            "Task Planner": "Converts designs into actionable implementation tasks",
            "Workflow Controller": "Manages the iterative development process and phase transitions",
            "Core Engine": "Central processing engine for the feature planning system",
            "Document Manager": "Handles document creation, versioning, and storage",
            "Validation System": "Comprehensive validation framework for all system components",
        }

        return descriptions.get(
            component,
            f"Core component responsible for {component.lower()} functionality",
        )

    def _generate_component_purpose(self, component: str) -> str:
        """Generate purpose statement for a component."""
        purposes = {
            "Requirements Validator": "Ensures INCOSE compliance and quality standards",
            "Design Generator": "Creates detailed technical designs from requirements",
            "Spec Manager": "Manages specification documents and their lifecycle",
            "EARS Engine": "Validates and formats requirements using EARS patterns",
            "Task Planner": "Converts designs into actionable implementation tasks",
            "Workflow Controller": "Manages the iterative development process",
            "Core Engine": "Provides central processing capabilities",
            "Document Manager": "Handles document operations and versioning",
            "Validation System": "Validates system components and data",
        }

        return purposes.get(component, f"Manages {component.lower()} operations")

    def _generate_interface_code(self, component: str) -> str:
        """Generate interface code for a component."""
        class_name = component.replace(" ", "")

        interfaces = {
            "Requirements Validator": f"""class {class_name}:
    def validate_requirements(self, requirements: List[Requirement]) -> ValidationResult
    def check_incose_compliance(self, requirement: str) -> List[QualityIssue]
    def validate_glossary(self, terms: Dict[str, str]) -> bool""",
            "Design Generator": f"""class {class_name}:
    def generate_design(self, requirements: List[Requirement]) -> str
    def create_architecture(self, components: List[str]) -> str
    def define_interfaces(self, components: List[str]) -> str""",
            "Spec Manager": f"""class {class_name}:
    def create_spec(self, feature_name: str) -> bool
    def load_spec(self, feature_name: str) -> Dict[str, Any]
    def update_document(self, doc_type: str, content: str) -> bool""",
            "EARS Engine": f"""class {class_name}:
    def validate_pattern(self, requirement: str) -> EARSPattern
    def format_requirement(self, text: str) -> str
    def check_compliance(self, requirements: List[str]) -> ValidationResult""",
            "Task Planner": f"""class {class_name}:
    def generate_tasks(self, design: str) -> List[Task]
    def create_dependencies(self, tasks: List[Task]) -> Dict[str, List[str]]
    def validate_completeness(self, tasks: List[Task]) -> bool""",
            "Workflow Controller": f"""class {class_name}:
    def get_current_phase(self) -> WorkflowPhase
    def transition_phase(self, to_phase: WorkflowPhase) -> bool
    def request_approval(self, phase: WorkflowPhase) -> bool""",
        }

        return interfaces.get(
            component,
            f"""class {class_name}:
    def process(self, input_data: Any) -> Any
    def validate(self, data: Any) -> bool""",
        )

    def _generate_key_methods(self, component: str) -> List[str]:
        """Generate key methods description for a component."""
        methods = {
            "Requirements Validator": [
                "INCOSE rule validation with specific error reporting",
                "Glossary term consistency checking",
                "Requirement completeness analysis",
            ],
            "Design Generator": [
                "Architecture diagram generation from requirements",
                "Interface specification creation",
                "Data model definition and relationships",
            ],
            "Spec Manager": [
                "Automatic directory structure creation",
                "Document versioning and backup",
                "Cross-reference validation",
            ],
            "EARS Engine": [
                "Pattern recognition for six EARS types",
                "Automatic formatting suggestions",
                "Clause ordering validation",
            ],
            "Task Planner": [
                "Task extraction from design documents",
                "Dependency analysis and ordering",
                "Requirement traceability mapping",
            ],
            "Workflow Controller": [
                "Phase transition management",
                "User approval handling",
                "Feedback processing and iteration support",
            ],
        }

        return methods.get(
            component,
            ["Core processing functionality", "Data validation and integrity"],
        )

    def _generate_data_model_code(self, entity: str) -> str:
        """Generate data model code for an entity."""
        models = {
            "Requirement": """@dataclass
class Requirement:
    id: str
    user_story: str
    acceptance_criteria: List[str]
    ears_pattern: EARSPattern
    referenced_terms: List[str]
    validation_status: ValidationStatus""",
            "Design Document": """@dataclass
class DesignDocument:
    overview: str
    architecture: str
    components: List[str]
    interfaces: Dict[str, str]
    data_models: List[str]
    error_handling: str
    testing_strategy: str""",
            "Task": """@dataclass
class Task:
    id: str
    title: str
    description: str
    requirements_refs: List[str]
    dependencies: List[str]
    is_optional: bool
    status: TaskStatus
    sub_tasks: List['Task']""",
            "Validation Result": """@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    pattern: Optional[EARSPattern]""",
        }

        return models.get(
            entity,
            f"""@dataclass
class {entity.replace(' ', '')}:
    id: str
    name: str
    data: Dict[str, Any]
    created_at: str
    updated_at: str""",
        )

    def _generate_overview(self, requirements: List[Requirement]) -> str:
        """Generate overview section from requirements."""
        overview = []

        # Extract system purpose from first requirement
        if requirements:
            first_req = requirements[0]
            overview.append(
                f"This system addresses the need for {first_req.user_story.lower()}."
            )
            overview.append("")

        # Add component summary
        components = self._extract_components(requirements)
        overview.append(f"The system consists of {len(components)} main components:")
        for component in components:
            overview.append(
                f"- **{component}**: {self._generate_component_purpose(component)}"
            )

        return "\n".join(overview)

    def _extract_entities(self, requirements: List[Requirement]) -> List[str]:
        """Extract data entities from requirements."""
        entities = set()

        # Common entity patterns
        entity_keywords = {
            "requirement": "Requirement",
            "design": "Design Document",
            "task": "Task",
            "validation": "Validation Result",
            "specification": "Specification",
            "document": "Document",
        }

        # Extract from requirements text
        for req in requirements:
            text = (req.user_story + " " + " ".join(req.acceptance_criteria)).lower()
            for keyword, entity in entity_keywords.items():
                if keyword in text:
                    entities.add(entity)

        # Add core entities if none found
        if not entities:
            entities.update(["Requirement", "Design Document", "Task"])

        return sorted(list(entities))

    def add_research_finding(
        self, topic: str, finding: str, source: str, relevance: str, impact: str
    ) -> None:
        """
        Add research finding to inform design decisions.

        Args:
            topic: Research topic area
            finding: Key research finding
            source: Source of the research
            relevance: How it relates to the current design
            impact: Impact on design decisions
        """
        research = ResearchFinding(
            topic=topic,
            finding=finding,
            source=source,
            relevance=relevance,
            impact=impact,
        )
        self.research_findings.append(research)

    def add_technical_decision(
        self,
        decision: str,
        rationale: str,
        alternatives: List[str],
        trade_offs: str,
        requirements_refs: List[str],
    ) -> None:
        """
        Record technical decision with rationale.

        Args:
            decision: The technical decision made
            rationale: Reasoning behind the decision
            alternatives: Alternative options considered
            trade_offs: Trade-offs and implications
            requirements_refs: Related requirements
        """
        tech_decision = TechnicalDecision(
            decision=decision,
            rationale=rationale,
            alternatives=alternatives,
            trade_offs=trade_offs,
            requirements_refs=requirements_refs,
        )
        self.technical_decisions.append(tech_decision)

    def incorporate_research_findings(self, requirements: List[Requirement]) -> str:
        """
        Generate research findings section for design document.

        Args:
            requirements: Requirements to correlate with research

        Returns:
            Research findings documentation
        """
        if not self.research_findings:
            return ""

        research_doc = []
        research_doc.append("## Research Findings\n")
        research_doc.append(
            "The following research findings inform the design decisions:\n"
        )

        for finding in self.research_findings:
            research_doc.append(f"### {finding.topic}\n")
            research_doc.append(f"**Finding**: {finding.finding}\n")
            research_doc.append(f"**Source**: {finding.source}\n")
            research_doc.append(f"**Relevance**: {finding.relevance}\n")
            research_doc.append(f"**Design Impact**: {finding.impact}\n")

        return "\n".join(research_doc)

    def document_technical_decisions(self, requirements: List[Requirement]) -> str:
        """
        Generate technical decisions section for design document.

        Args:
            requirements: Requirements that influenced decisions

        Returns:
            Technical decisions documentation
        """
        if not self.technical_decisions:
            # Generate default decisions based on requirements
            self._generate_default_decisions(requirements)

        decisions_doc = []
        decisions_doc.append("## Technical Decisions\n")
        decisions_doc.append("Key technical decisions and their rationale:\n")

        for i, decision in enumerate(self.technical_decisions, 1):
            decisions_doc.append(f"### Decision {i}: {decision.decision}\n")
            decisions_doc.append(f"**Rationale**: {decision.rationale}\n")

            if decision.alternatives:
                decisions_doc.append("**Alternatives Considered**:")
                for alt in decision.alternatives:
                    decisions_doc.append(f"- {alt}")
                decisions_doc.append("")

            decisions_doc.append(f"**Trade-offs**: {decision.trade_offs}\n")

            if decision.requirements_refs:
                req_refs = ", ".join(decision.requirements_refs)
                decisions_doc.append(f"**Related Requirements**: {req_refs}\n")

        return "\n".join(decisions_doc)

    def _generate_default_decisions(self, requirements: List[Requirement]) -> None:
        """Generate default technical decisions based on requirements."""
        # Architecture pattern decision
        self.add_technical_decision(
            decision="Modular Component Architecture",
            rationale="Requirements indicate need for multiple specialized components with clear separation of concerns",
            alternatives=["Monolithic architecture", "Microservices architecture"],
            trade_offs="Increased complexity but better maintainability and testability",
            requirements_refs=[req.id for req in requirements[:2]],
        )

        # Validation strategy decision
        self.add_technical_decision(
            decision="Multi-layer Validation Strategy",
            rationale="Requirements emphasize quality and compliance, requiring validation at multiple levels",
            alternatives=["Single validation layer", "No validation"],
            trade_offs="Higher development effort but ensures quality and compliance",
            requirements_refs=[
                req.id for req in requirements if "validation" in req.user_story.lower()
            ],
        )

        # Workflow management decision
        self.add_technical_decision(
            decision="State-based Workflow Management",
            rationale="Requirements specify iterative process with explicit approval gates",
            alternatives=["Linear workflow", "Event-driven workflow"],
            trade_offs="More complex state management but better user control",
            requirements_refs=[
                req.id for req in requirements if "workflow" in req.user_story.lower()
            ],
        )

    def generate_error_handling_strategy(self, requirements: List[Requirement]) -> str:
        """
        Generate error handling strategy documentation.

        Args:
            requirements: Requirements to analyze for error scenarios

        Returns:
            Error handling strategy documentation
        """
        error_doc = []
        error_doc.append("## Error Handling\n")

        # Validation errors
        error_doc.append("### Validation Errors")
        validation_errors = self._identify_validation_errors(requirements)
        for error in validation_errors:
            error_doc.append(f"- **{error['type']}**: {error['description']}")
        error_doc.append("")

        # Workflow errors
        error_doc.append("### Workflow Errors")
        workflow_errors = self._identify_workflow_errors(requirements)
        for error in workflow_errors:
            error_doc.append(f"- **{error['type']}**: {error['description']}")
        error_doc.append("")

        # Recovery strategies
        error_doc.append("### Recovery Strategies")
        recovery_strategies = self._generate_recovery_strategies(requirements)
        for strategy in recovery_strategies:
            error_doc.append(f"- **{strategy['scenario']}**: {strategy['strategy']}")
        error_doc.append("")

        return "\n".join(error_doc)

    def _identify_validation_errors(
        self, requirements: List[Requirement]
    ) -> List[Dict[str, str]]:
        """Identify potential validation errors from requirements."""
        errors = [
            {
                "type": "EARS Pattern Violations",
                "description": "Provide specific correction suggestions with pattern examples",
            },
            {
                "type": "INCOSE Rule Violations",
                "description": "Highlight problematic phrases with alternative suggestions",
            },
            {
                "type": "Missing Glossary Terms",
                "description": "Auto-detect undefined technical terms and prompt for definitions",
            },
            {
                "type": "Incomplete Requirements",
                "description": "Identify coverage gaps and missing acceptance criteria",
            },
        ]
        return errors

    def _identify_workflow_errors(
        self, requirements: List[Requirement]
    ) -> List[Dict[str, str]]:
        """Identify potential workflow errors from requirements."""
        errors = [
            {
                "type": "Phase Transition Failures",
                "description": "Prevent progression without explicit user approval",
            },
            {
                "type": "Document Inconsistencies",
                "description": "Flag mismatches between requirements, design, and tasks",
            },
            {
                "type": "Task Generation Failures",
                "description": "Ensure all requirements are covered by implementation tasks",
            },
        ]
        return errors

    def _generate_recovery_strategies(
        self, requirements: List[Requirement]
    ) -> List[Dict[str, str]]:
        """Generate recovery strategies for error scenarios."""
        strategies = [
            {
                "scenario": "Automatic Backup",
                "strategy": "Preserve previous document versions during iterations",
            },
            {
                "scenario": "Rollback Capability",
                "strategy": "Return to previous approved states when validation fails",
            },
            {
                "scenario": "Incremental Validation",
                "strategy": "Check compliance at each document modification",
            },
        ]
        return strategies

    def _generate_unit_testing_strategy(
        self, requirements: List[Requirement]
    ) -> List[str]:
        """Generate unit testing strategy based on requirements."""
        tests = [
            "EARS pattern recognition accuracy for all six pattern types",
            "INCOSE rule validation correctness with edge cases",
            "Document generation completeness and format validation",
            "Workflow state transitions and validation logic",
        ]

        # Add requirement-specific tests
        for req in requirements:
            if "validation" in req.user_story.lower():
                tests.append(f"Validation logic for requirement {req.id}")
            if "generation" in req.user_story.lower():
                tests.append(f"Document generation for requirement {req.id}")

        return tests

    def _generate_integration_testing_strategy(
        self, requirements: List[Requirement]
    ) -> List[str]:
        """Generate integration testing strategy based on requirements."""
        tests = [
            "End-to-end spec creation workflow from requirements to tasks",
            "Cross-document consistency validation between phases",
            "User interaction flow testing with approval mechanisms",
            "File system integration verification with Kiro tools",
        ]

        # Add workflow-specific tests
        for req in requirements:
            if "workflow" in req.user_story.lower():
                tests.append(f"Workflow integration for requirement {req.id}")

        return tests

    def _generate_validation_testing_strategy(
        self, requirements: List[Requirement]
    ) -> List[str]:
        """Generate validation testing strategy based on requirements."""
        tests = [
            "Real-world feature specification scenarios",
            "Complex requirement handling with multiple EARS patterns",
            "Multi-iteration workflow testing with feedback cycles",
            "Error recovery and rollback testing",
        ]

        # Add requirement-specific validation tests
        for req in requirements:
            if (
                "quality" in req.user_story.lower()
                or "compliance" in req.user_story.lower()
            ):
                tests.append(f"Quality compliance validation for requirement {req.id}")

        return tests
