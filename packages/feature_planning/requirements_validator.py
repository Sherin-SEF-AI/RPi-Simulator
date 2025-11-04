"""
Requirements Validator for INCOSE compliance.

This module ensures requirements meet INCOSE quality standards
and maintains glossary consistency.
"""

import re
from typing import Dict, List, Optional, Set

from .base import BaseValidator, QualityIssue, ValidationResult
from .config import get_config


class RequirementsValidator(BaseValidator):
    """
    Validates requirements against INCOSE quality rules.

    Ensures requirements use active voice, avoid vague terms,
    and maintain measurability and consistency.
    """

    def __init__(self) -> None:
        """Initialize Requirements Validator with INCOSE rules."""
        self.config = get_config()
        self.incose_rules = self.config.get_incose_rules()

        # Vague terms to detect
        self.vague_terms = {
            "quickly",
            "fast",
            "slow",
            "adequate",
            "sufficient",
            "appropriate",
            "reasonable",
            "easy",
            "simple",
            "complex",
            "good",
            "bad",
            "better",
            "worse",
            "optimal",
            "efficient",
            "robust",
            "reliable",
            "secure",
            "safe",
            "high",
            "low",
            "many",
            "few",
            "some",
            "several",
            "various",
            "multiple",
        }

        # Compound vague terms (hyphenated or multi-word)
        self.compound_vague_terms = [
            "user-friendly",
            "user friendly",
            "cost-effective",
            "cost effective",
            "state-of-the-art",
            "state of the art",
            "real-time",
            "real time",
        ]

        # Escape clauses to detect
        self.escape_clauses = {
            "where possible",
            "if possible",
            "when feasible",
            "if feasible",
            "as appropriate",
            "as needed",
            "when necessary",
            "if required",
            "to the extent possible",
            "where applicable",
            "if applicable",
            "as much as possible",
            "when practical",
            "if practical",
        }

        # Passive voice indicators
        self.passive_indicators = {"is", "are", "was", "were", "been", "being", "be"}

        # Negative statement patterns
        self.negative_patterns = [
            r"\bshall\s+not\b",
            r"\bwill\s+not\b",
            r"\bmust\s+not\b",
            r"\bcannot\b",
            r"\bshould\s+not\b",
        ]

    def validate(self, content: str) -> ValidationResult:
        """
        Validate requirement against INCOSE quality rules.

        Args:
            content: Requirement text to validate

        Returns:
            ValidationResult with quality issues and suggestions
        """
        issues = self.check_incose_rules(content)
        suggestions = self.get_suggestions(content)

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=[issue.description for issue in issues],
            suggestions=suggestions,
        )

    def get_suggestions(self, content: str) -> List[str]:
        """
        Get quality improvement suggestions for requirement.

        Args:
            content: Requirement text to analyze

        Returns:
            List of improvement suggestions
        """
        suggestions = []
        issues = self.check_incose_rules(content)

        for issue in issues:
            suggestions.append(issue.suggestion)

        return suggestions

    def check_incose_rules(self, requirement: str) -> List[QualityIssue]:
        """
        Check requirement against all INCOSE quality rules.

        Args:
            requirement: Requirement text to check

        Returns:
            List of quality issues found
        """
        issues = []

        # Check active voice
        issues.extend(self._check_active_voice(requirement))

        # Check for vague terms
        issues.extend(self._check_vague_terms(requirement))

        # Check for escape clauses
        issues.extend(self._check_escape_clauses(requirement))

        # Check for negative statements
        issues.extend(self._check_negative_statements(requirement))

        # Check for single thought
        issues.extend(self._check_single_thought(requirement))

        # Check measurability
        issues.extend(self._check_measurability(requirement))

        return issues

    def _check_active_voice(self, requirement: str) -> List[QualityIssue]:
        """Check if requirement uses active voice."""
        issues = []

        # Look for passive voice patterns
        text_lower = requirement.lower()

        # Pattern: "be" + past participle (common passive voice)
        passive_pattern = r"\b(?:is|are|was|were|be|been|being)\s+\w+ed\b"
        if re.search(passive_pattern, text_lower):
            issues.append(
                QualityIssue(
                    rule="active_voice",
                    description="Requirement appears to use passive voice",
                    suggestion="Rewrite using active voice: specify who performs the action",
                    severity="error",
                )
            )

        # Check for "shall be" constructions which are often passive
        if re.search(r"\bshall\s+be\s+\w+ed\b", text_lower):
            issues.append(
                QualityIssue(
                    rule="active_voice",
                    description="'SHALL be [verb]ed' construction suggests passive voice",
                    suggestion="Use active voice: 'THE [system] SHALL [action]'",
                    severity="error",
                )
            )

        return issues

    def _check_vague_terms(self, requirement: str) -> List[QualityIssue]:
        """Check for vague or subjective terms."""
        issues = []

        # Check individual words
        words = set(re.findall(r"\b\w+\b", requirement.lower()))
        found_vague = words.intersection(self.vague_terms)
        for term in found_vague:
            issues.append(
                QualityIssue(
                    rule="no_vague_terms",
                    description=f"Vague term detected: '{term}'",
                    suggestion=f"Replace '{term}' with specific, measurable criteria",
                    severity="warning",
                )
            )

        # Check compound vague terms
        requirement_lower = requirement.lower()
        for compound_term in self.compound_vague_terms:
            if compound_term in requirement_lower:
                issues.append(
                    QualityIssue(
                        rule="no_vague_terms",
                        description=f"Vague term detected: '{compound_term}'",
                        suggestion=f"Replace '{compound_term}' with specific, measurable criteria",
                        severity="warning",
                    )
                )

        return issues

    def _check_escape_clauses(self, requirement: str) -> List[QualityIssue]:
        """Check for escape clauses that weaken requirements."""
        issues = []
        text_lower = requirement.lower()

        for clause in self.escape_clauses:
            if clause in text_lower:
                issues.append(
                    QualityIssue(
                        rule="no_escape_clauses",
                        description=f"Escape clause detected: '{clause}'",
                        suggestion=f"Remove '{clause}' and specify exact conditions",
                        severity="error",
                    )
                )

        return issues

    def _check_negative_statements(self, requirement: str) -> List[QualityIssue]:
        """Check for negative requirements (SHALL NOT)."""
        issues = []

        for pattern in self.negative_patterns:
            if re.search(pattern, requirement, re.IGNORECASE):
                issues.append(
                    QualityIssue(
                        rule="no_negatives",
                        description="Negative requirement detected (SHALL NOT, etc.)",
                        suggestion="Rewrite as positive requirement specifying what the system SHALL do",
                        severity="warning",
                    )
                )

        return issues

    def _check_single_thought(self, requirement: str) -> List[QualityIssue]:
        """Check if requirement expresses single thought."""
        issues = []

        # Count AND/OR conjunctions that might indicate multiple thoughts
        and_count = len(re.findall(r"\band\b", requirement, re.IGNORECASE))
        or_count = len(re.findall(r"\bor\b", requirement, re.IGNORECASE))

        # More than 2 ANDs or any ORs might indicate multiple thoughts
        if and_count > 2:
            issues.append(
                QualityIssue(
                    rule="single_thought",
                    description=f"Multiple 'AND' clauses detected ({and_count})",
                    suggestion="Consider splitting into separate requirements",
                    severity="error",
                )
            )

        if or_count > 0:
            issues.append(
                QualityIssue(
                    rule="single_thought",
                    description=f"'OR' clauses detected ({or_count})",
                    suggestion="Split alternatives into separate requirements",
                    severity="error",
                )
            )

        return issues

    def _check_measurability(self, requirement: str) -> List[QualityIssue]:
        """Check if requirement includes measurable criteria."""
        issues = []

        # Look for measurable indicators (numbers, units, percentages)
        has_numbers = bool(re.search(r"\d+", requirement))
        has_units = bool(
            re.search(
                r"\b(?:seconds?|minutes?|hours?|days?|ms|kb|mb|gb|%|percent)\b",
                requirement,
                re.IGNORECASE,
            )
        )
        has_quantifiers = bool(
            re.search(
                r"\b(?:all|every|each|within|less than|greater than|at least|at most)\b",
                requirement,
                re.IGNORECASE,
            )
        )

        # If requirement contains performance/quality terms but no measurable criteria
        performance_terms = {
            "performance",
            "speed",
            "time",
            "response",
            "throughput",
            "capacity",
            "accuracy",
            "precision",
        }
        words = set(re.findall(r"\b\w+\b", requirement.lower()))

        if words.intersection(performance_terms) and not (
            has_numbers or has_units or has_quantifiers
        ):
            issues.append(
                QualityIssue(
                    rule="measurable",
                    description="Performance requirement lacks measurable criteria",
                    suggestion="Add specific quantities, timeframes, or success conditions",
                    severity="warning",
                )
            )

        return issues

    def validate_glossary(self, terms: Dict[str, str]) -> ValidationResult:
        """
        Validate glossary terms and definitions.

        Args:
            terms: Dictionary of terms and their definitions

        Returns:
            Validation result for glossary
        """
        issues = []
        suggestions = []

        if not terms:
            issues.append("Empty glossary provided")
            suggestions.append(
                "Add definitions for technical terms used in requirements"
            )
            return ValidationResult(
                is_valid=False, issues=issues, suggestions=suggestions
            )

        # Check each term and definition
        for term, definition in terms.items():
            term_issues = self._validate_glossary_term(term, definition)
            issues.extend([issue.description for issue in term_issues])
            suggestions.extend([issue.suggestion for issue in term_issues])

        # Check for circular definitions
        circular_issues = self._check_circular_definitions(terms)
        issues.extend([issue.description for issue in circular_issues])
        suggestions.extend([issue.suggestion for issue in circular_issues])

        return ValidationResult(
            is_valid=len(issues) == 0, issues=issues, suggestions=suggestions
        )

    def _validate_glossary_term(self, term: str, definition: str) -> List[QualityIssue]:
        """Validate individual glossary term and definition."""
        issues = []

        # Check term format
        if not term.strip():
            issues.append(
                QualityIssue(
                    rule="glossary_term_format",
                    description="Empty term in glossary",
                    suggestion="Provide a valid term name",
                    severity="error",
                )
            )

        # Check for proper term naming (should be clear and specific)
        if len(term.strip()) < 2:
            issues.append(
                QualityIssue(
                    rule="glossary_term_format",
                    description=f"Term '{term}' is too short",
                    suggestion="Use descriptive term names (at least 2 characters)",
                    severity="warning",
                )
            )

        # Check definition quality
        if not definition.strip():
            issues.append(
                QualityIssue(
                    rule="glossary_definition",
                    description=f"Empty definition for term '{term}'",
                    suggestion="Provide a clear, concise definition",
                    severity="error",
                )
            )
        elif len(definition.strip()) < 10:
            issues.append(
                QualityIssue(
                    rule="glossary_definition",
                    description=f"Definition for '{term}' is too brief",
                    suggestion="Provide more detailed definition (at least 10 characters)",
                    severity="warning",
                )
            )

        # Check if definition starts with the term itself (circular)
        if definition.lower().startswith(term.lower()):
            issues.append(
                QualityIssue(
                    rule="glossary_definition",
                    description=f"Definition for '{term}' appears circular",
                    suggestion="Define the term without using the term itself",
                    severity="warning",
                )
            )

        # Check for vague definitions
        definition_words = set(re.findall(r"\b\w+\b", definition.lower()))
        vague_in_definition = definition_words.intersection(self.vague_terms)
        if vague_in_definition:
            issues.append(
                QualityIssue(
                    rule="glossary_definition",
                    description=f"Vague terms in definition of '{term}': {', '.join(vague_in_definition)}",
                    suggestion="Use specific, precise language in definitions",
                    severity="warning",
                )
            )

        return issues

    def _check_circular_definitions(self, terms: Dict[str, str]) -> List[QualityIssue]:
        """Check for circular references in glossary definitions."""
        issues = []

        for term, definition in terms.items():
            # Check if this term's definition references other terms in the glossary
            definition_words = set(re.findall(r"\b\w+\b", definition.lower()))
            other_terms = {t.lower() for t in terms.keys() if t.lower() != term.lower()}

            referenced_terms = definition_words.intersection(other_terms)

            # For each referenced term, check if it references back
            for ref_term in referenced_terms:
                # Find the actual term key (case-sensitive)
                actual_ref_term = next(
                    (t for t in terms.keys() if t.lower() == ref_term), None
                )
                if actual_ref_term:
                    ref_definition = terms[actual_ref_term]
                    ref_def_words = set(re.findall(r"\b\w+\b", ref_definition.lower()))

                    if term.lower() in ref_def_words:
                        issues.append(
                            QualityIssue(
                                rule="glossary_circular",
                                description=f"Circular reference between '{term}' and '{actual_ref_term}'",
                                suggestion="Rewrite definitions to avoid circular references",
                                severity="warning",
                            )
                        )

        return issues

    def detect_technical_terms(
        self, requirements_text: str, existing_glossary: Optional[Dict[str, str]] = None
    ) -> Set[str]:
        """
        Automatically detect technical terms that should be in glossary.

        Args:
            requirements_text: Text of all requirements
            existing_glossary: Current glossary terms (optional)

        Returns:
            Set of detected technical terms
        """
        if existing_glossary is None:
            existing_glossary = {}

        detected_terms = set()

        # Look for capitalized terms that might be system names
        system_names = re.findall(
            r"\bTHE\s+([A-Z][a-zA-Z_]+)\s+SHALL\b", requirements_text
        )
        detected_terms.update(system_names)

        # Look for technical acronyms (2-5 uppercase letters)
        acronyms = re.findall(r"\b[A-Z]{2,5}\b", requirements_text)
        detected_terms.update(acronyms)

        # Look for compound technical terms (words with underscores or CamelCase)
        compound_terms = re.findall(
            r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b", requirements_text
        )
        detected_terms.update(compound_terms)

        underscore_terms = re.findall(r"\b\w+_\w+\b", requirements_text)
        detected_terms.update(underscore_terms)

        # Filter out terms already in glossary (case-insensitive)
        existing_lower = {term.lower() for term in existing_glossary.keys()}
        detected_terms = {
            term for term in detected_terms if term.lower() not in existing_lower
        }

        # Filter out common words that aren't technical terms
        common_words = {
            "THE",
            "SHALL",
            "WHEN",
            "WHERE",
            "WHILE",
            "IF",
            "THEN",
            "AND",
            "OR",
        }
        detected_terms = {term for term in detected_terms if term not in common_words}

        return detected_terms

    def check_glossary_consistency(
        self, requirements_text: str, glossary: Dict[str, str]
    ) -> ValidationResult:
        """
        Check consistency between requirements and glossary.

        Args:
            requirements_text: Text of all requirements
            glossary: Current glossary

        Returns:
            Validation result for consistency
        """
        issues = []
        suggestions = []

        # Detect terms that should be in glossary but aren't
        missing_terms = self.detect_technical_terms(requirements_text, glossary)
        if missing_terms:
            issues.append(
                f"Technical terms not in glossary: {', '.join(sorted(missing_terms))}"
            )
            suggestions.append(
                "Add definitions for technical terms used in requirements"
            )

        # Check if glossary terms are actually used in requirements
        requirements_lower = requirements_text.lower()
        unused_terms = []
        for term in glossary.keys():
            if term.lower() not in requirements_lower:
                unused_terms.append(term)

        if unused_terms:
            issues.append(
                f"Glossary terms not used in requirements: {', '.join(unused_terms)}"
            )
            suggestions.append(
                "Remove unused terms or ensure they are referenced in requirements"
            )

        # Check for inconsistent term usage (different capitalizations)
        for term in glossary.keys():
            # Find all variations of this term in requirements
            variations = re.findall(
                rf"\b{re.escape(term)}\b", requirements_text, re.IGNORECASE
            )
            unique_variations = set(variations)

            if len(unique_variations) > 1:
                issues.append(
                    f"Inconsistent capitalization of '{term}': {', '.join(unique_variations)}"
                )
                suggestions.append(
                    f"Use consistent capitalization for '{term}' throughout requirements"
                )

        return ValidationResult(
            is_valid=len(issues) == 0, issues=issues, suggestions=suggestions
        )

    def ensure_completeness(self, requirements: List[str]) -> ValidationResult:
        """
        Ensure requirements set is complete and consistent.

        Args:
            requirements: List of requirements to check

        Returns:
            Completeness validation result
        """
        issues = []
        suggestions = []

        if not requirements:
            issues.append("No requirements provided")
            suggestions.append("Add at least one requirement")
            return ValidationResult(
                is_valid=False, issues=issues, suggestions=suggestions
            )

        # Check for duplicate requirements
        seen_requirements = set()
        for i, req in enumerate(requirements):
            normalized = re.sub(r"\s+", " ", req.strip().lower())
            if normalized in seen_requirements:
                issues.append(f"Duplicate requirement detected at position {i+1}")
                suggestions.append("Remove or consolidate duplicate requirements")
            seen_requirements.add(normalized)

        # Check for requirements without SHALL
        for i, req in enumerate(requirements):
            if "shall" not in req.lower():
                issues.append(f"Requirement {i+1} missing 'SHALL' keyword")
                suggestions.append(
                    "All requirements should use 'SHALL' to indicate mandatory behavior"
                )

        # Check for consistent terminology
        all_text = " ".join(requirements).lower()
        system_terms = re.findall(r"\bthe\s+(\w+)\s+shall\b", all_text)
        if len(set(system_terms)) > 3:
            suggestions.append(
                "Consider using consistent system names across requirements"
            )

        return ValidationResult(
            is_valid=len(issues) == 0, issues=issues, suggestions=suggestions
        )
