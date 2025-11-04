"""
EARS Engine for requirement validation and formatting.

This module implements the EARS (Easy Approach to Requirements Syntax)
pattern recognition and validation system.
"""

from typing import List, Optional

from .base import BaseValidator, EARSPattern, ValidationResult
from .config import get_config


class EARSEngine(BaseValidator):
    """
    EARS Engine for validating and formatting requirements using EARS patterns.

    Provides pattern recognition for all six EARS types and automatic
    formatting suggestions for non-compliant requirements.
    """

    def __init__(self) -> None:
        """Initialize EARS Engine with configuration."""
        self.config = get_config()
        self.patterns = self.config.get_ears_patterns()

    def validate(self, content: str) -> ValidationResult:
        """
        Validate requirement against EARS patterns.

        Args:
            content: Requirement text to validate

        Returns:
            ValidationResult with pattern match and compliance status
        """
        content = content.strip()

        if not content:
            return ValidationResult(
                is_valid=False,
                issues=["Empty requirement"],
                suggestions=["Provide requirement text"],
                pattern=None,
            )

        # Check for EARS pattern match
        detected_pattern = self.validate_pattern(content)

        if detected_pattern:
            # Validate clause ordering for complex patterns
            clause_issues = self._validate_clause_ordering(content, detected_pattern)

            if clause_issues:
                return ValidationResult(
                    is_valid=False,
                    issues=clause_issues,
                    suggestions=self._get_clause_ordering_suggestions(detected_pattern),
                    pattern=detected_pattern,
                )

            return ValidationResult(
                is_valid=True, issues=[], suggestions=[], pattern=detected_pattern
            )
        else:
            return ValidationResult(
                is_valid=False,
                issues=["No EARS pattern detected"],
                suggestions=self.get_suggestions(content),
                pattern=None,
            )

    def get_suggestions(self, content: str) -> List[str]:
        """
        Get formatting suggestions for non-compliant requirements.

        Args:
            content: Requirement text to analyze

        Returns:
            List of formatting suggestions
        """
        suggestions = []
        content = content.strip().upper()

        # Check for partial matches and suggest corrections
        if "SHALL" not in content:
            suggestions.append("Add 'SHALL' to make it a proper requirement")

        if not content.startswith(("THE ", "WHEN ", "WHILE ", "IF ", "WHERE ")):
            suggestions.append(
                "Start with EARS trigger word: THE, WHEN, WHILE, IF, or WHERE"
            )

        # Suggest specific patterns based on content analysis
        if any(word in content for word in ["WHEN", "OCCURS", "HAPPENS", "TRIGGERS"]):
            suggestions.append(
                "Consider Event-driven pattern: 'WHEN <trigger>, THE <system> SHALL <response>'"
            )

        if any(word in content for word in ["WHILE", "DURING", "AS LONG AS"]):
            suggestions.append(
                "Consider State-driven pattern: 'WHILE <condition>, THE <system> SHALL <response>'"
            )

        if any(word in content for word in ["IF", "ERROR", "FAIL", "EXCEPTION"]):
            suggestions.append(
                "Consider Unwanted event pattern: 'IF <condition>, THEN THE <system> SHALL <response>'"
            )

        if any(word in content for word in ["WHERE", "OPTIONAL", "FEATURE", "MODE"]):
            suggestions.append(
                "Consider Optional feature pattern: 'WHERE <option>, THE <system> SHALL <response>'"
            )

        if not suggestions:
            suggestions.append(
                "Use Ubiquitous pattern: 'THE <system> SHALL <response>' for always-active behavior"
            )

        return suggestions

    def _validate_clause_ordering(
        self, content: str, pattern: EARSPattern
    ) -> List[str]:
        """
        Validate clause ordering for complex EARS patterns.

        Args:
            content: Requirement text to validate
            pattern: Detected EARS pattern

        Returns:
            List of clause ordering issues
        """
        issues = []

        if pattern == EARSPattern.COMPLEX:
            # Check proper ordering: WHERE → WHILE → WHEN/IF → THE → SHALL
            content_upper = content.upper()

            # Find positions of key clauses
            where_pos = content_upper.find("WHERE")
            while_pos = content_upper.find("WHILE")
            when_pos = content_upper.find("WHEN")
            if_pos = content_upper.find("IF")
            the_pos = content_upper.find("THE")
            shall_pos = content_upper.find("SHALL")

            # Determine trigger position (WHEN or IF)
            trigger_pos = -1
            if when_pos >= 0 and if_pos >= 0:
                trigger_pos = min(when_pos, if_pos)
                issues.append("Use either WHEN or IF, not both")
            elif when_pos >= 0:
                trigger_pos = when_pos
            elif if_pos >= 0:
                trigger_pos = if_pos

            # Validate ordering
            positions = []
            if where_pos >= 0:
                positions.append(("WHERE", where_pos))
            if while_pos >= 0:
                positions.append(("WHILE", while_pos))
            if trigger_pos >= 0:
                trigger_word = "WHEN" if when_pos == trigger_pos else "IF"
                positions.append((trigger_word, trigger_pos))
            if the_pos >= 0:
                positions.append(("THE", the_pos))
            if shall_pos >= 0:
                positions.append(("SHALL", shall_pos))

            # Check if positions are in correct order
            positions.sort(key=lambda x: x[1])
            expected_order = ["WHERE", "WHILE", "WHEN", "IF", "THE", "SHALL"]

            for i in range(len(positions) - 1):
                current_clause = positions[i][0]
                next_clause = positions[i + 1][0]

                current_idx = (
                    expected_order.index(current_clause)
                    if current_clause in expected_order
                    else -1
                )
                next_idx = (
                    expected_order.index(next_clause)
                    if next_clause in expected_order
                    else -1
                )

                if current_idx >= 0 and next_idx >= 0 and current_idx > next_idx:
                    issues.append(
                        f"Clause '{current_clause}' should come before '{next_clause}'"
                    )

        return issues

    def _get_clause_ordering_suggestions(self, pattern: EARSPattern) -> List[str]:
        """
        Get suggestions for proper clause ordering.

        Args:
            pattern: EARS pattern type

        Returns:
            List of ordering suggestions
        """
        if pattern == EARSPattern.COMPLEX:
            return [
                "Use proper clause order: WHERE → WHILE → WHEN/IF → THE → SHALL",
                "Example: 'WHERE debug enabled, WHILE system running, WHEN error occurs, THE Logger SHALL record trace'",
            ]

        return []

    def _parse_user_story(self, user_story: str) -> Optional[tuple]:
        """
        Parse user story into role, feature, and benefit components.

        Args:
            user_story: User story text

        Returns:
            Tuple of (role, feature, benefit) or None if invalid format
        """
        import re

        # Pattern to match: "As a [role], I want [feature], so that [benefit]"
        pattern = r"As\s+a\s+(.+?),\s*I\s+want\s+(.+?),\s*so\s+that\s+(.+)"
        match = re.search(pattern, user_story, re.IGNORECASE)

        if match:
            return (
                match.group(1).strip(),
                match.group(2).strip(),
                match.group(3).strip(),
            )

        return None

    def _extract_system_name(self, feature: str) -> Optional[str]:
        """Extract system name from feature description."""
        # Look for common system indicators
        feature_lower = feature.lower()

        if "system" in feature_lower:
            return "System"
        elif "application" in feature_lower or "app" in feature_lower:
            return "Application"
        elif "database" in feature_lower:
            return "Database"
        elif "interface" in feature_lower or "ui" in feature_lower:
            return "Interface"
        elif "api" in feature_lower:
            return "API"

        return None

    def _extract_action(self, feature: str) -> str:
        """Extract user action from feature description."""
        feature_lower = feature.lower()

        if "click" in feature_lower:
            return "clicks the button"
        elif "submit" in feature_lower:
            return "submits the form"
        elif "enter" in feature_lower or "input" in feature_lower:
            return "enters data"
        elif "select" in feature_lower:
            return "selects an option"
        elif "upload" in feature_lower:
            return "uploads a file"

        return "performs the action"

    def _extract_condition(self, feature: str) -> str:
        """Extract condition from feature description."""
        feature_lower = feature.lower()

        if "logged in" in feature_lower or "authenticated" in feature_lower:
            return "authenticated"
        elif "authorized" in feature_lower:
            return "authorized"
        elif "connected" in feature_lower:
            return "connected"

        return "in the specified state"

    def _extract_error_condition(self, feature: str) -> str:
        """Extract error condition from feature description."""
        feature_lower = feature.lower()

        if "invalid" in feature_lower:
            return "invalid data is provided"
        elif "timeout" in feature_lower:
            return "timeout occurs"
        elif "error" in feature_lower:
            return "an error occurs"
        elif "fail" in feature_lower:
            return "operation fails"

        return "an error condition is detected"

    def _extract_option(self, feature: str) -> str:
        """Extract optional feature condition."""
        feature_lower = feature.lower()

        if "advanced" in feature_lower:
            return "advanced mode is enabled"
        elif "premium" in feature_lower:
            return "premium subscription is active"
        elif "debug" in feature_lower:
            return "debug mode is enabled"
        elif "admin" in feature_lower:
            return "admin privileges are granted"

        return "optional feature is enabled"

    def _generate_response(self, feature: str) -> str:
        """Generate appropriate system response based on feature."""
        feature_lower = feature.lower()

        if "save" in feature_lower or "store" in feature_lower:
            return "save the data securely"
        elif "display" in feature_lower or "show" in feature_lower:
            return "display the requested information"
        elif "validate" in feature_lower:
            return "validate the input data"
        elif "process" in feature_lower:
            return "process the request"
        elif "send" in feature_lower or "notify" in feature_lower:
            return "send the notification"

        return "perform the requested operation"

    def _generate_error_response(self, feature: str) -> str:
        """Generate appropriate error response."""
        return "display an appropriate error message and maintain system stability"

    def _is_truly_complex(self, requirement: str) -> bool:
        """
        Check if a requirement is truly complex (has multiple clauses).

        Args:
            requirement: Requirement text to analyze

        Returns:
            True if requirement has multiple EARS clauses
        """
        content_upper = requirement.upper()

        # Count the number of EARS clause keywords
        clause_count = 0

        if "WHERE" in content_upper:
            clause_count += 1
        if "WHILE" in content_upper:
            clause_count += 1
        if "WHEN" in content_upper:
            clause_count += 1
        if "IF" in content_upper:
            clause_count += 1

        # A truly complex requirement should have at least 2 conditional clauses
        # plus the mandatory THE...SHALL structure
        return clause_count >= 2

    def validate_pattern(self, requirement: str) -> Optional[EARSPattern]:
        """
        Identify which EARS pattern a requirement follows.

        Args:
            requirement: Requirement text to analyze

        Returns:
            Detected EARS pattern or None if no match
        """
        requirement = requirement.strip()

        # First check if it's truly complex (has multiple clauses)
        if self._is_truly_complex(requirement):
            if "complex" in self.patterns:
                pattern_config = self.patterns["complex"]
                if pattern_config.compiled_pattern.match(requirement):
                    return EARSPattern.COMPLEX

        # Check simple patterns
        simple_patterns = [
            "event_driven",
            "state_driven",
            "unwanted_event",
            "optional_feature",
            "ubiquitous",
        ]

        for pattern_name in simple_patterns:
            if pattern_name in self.patterns:
                pattern_config = self.patterns[pattern_name]
                if pattern_config.compiled_pattern.match(requirement):
                    return EARSPattern(pattern_name)

        return None

    def format_requirement(self, user_story: str) -> List[str]:
        """
        Generate EARS-compliant acceptance criteria from user story.

        Args:
            user_story: User story to convert

        Returns:
            List of formatted acceptance criteria
        """
        if not user_story.strip():
            return ["Cannot format empty user story"]

        # Extract key components from user story
        story_parts = self._parse_user_story(user_story)
        if not story_parts:
            return [
                "Invalid user story format. Use: 'As a [role], I want [feature], so that [benefit]'"
            ]

        role, feature, benefit = story_parts

        # Generate EARS-compliant acceptance criteria based on feature analysis
        criteria = []

        # Determine system name from context or use generic
        system_name = self._extract_system_name(feature) or "System"

        # Generate different types of criteria based on feature keywords
        feature_lower = feature.lower()

        # Event-driven criteria for user actions
        if any(
            word in feature_lower
            for word in ["click", "submit", "enter", "select", "upload"]
        ):
            action = self._extract_action(feature)
            criteria.append(
                f"WHEN {role} {action}, THE {system_name} SHALL {self._generate_response(feature)}"
            )

        # State-driven criteria for conditions
        if any(
            word in feature_lower
            for word in ["logged in", "authenticated", "authorized", "connected"]
        ):
            condition = self._extract_condition(feature)
            criteria.append(
                f"WHILE {role} is {condition}, THE {system_name} SHALL {self._generate_response(feature)}"
            )

        # Unwanted event criteria for error handling
        if any(
            word in feature_lower for word in ["error", "fail", "invalid", "timeout"]
        ):
            error_condition = self._extract_error_condition(feature)
            criteria.append(
                f"IF {error_condition}, THEN THE {system_name} SHALL {self._generate_error_response(feature)}"
            )

        # Optional feature criteria
        if any(
            word in feature_lower
            for word in ["optional", "advanced", "premium", "mode"]
        ):
            option = self._extract_option(feature)
            criteria.append(
                f"WHERE {option}, THE {system_name} SHALL {self._generate_response(feature)}"
            )

        # Default ubiquitous criteria
        if not criteria:
            criteria.append(
                f"THE {system_name} SHALL {self._generate_response(feature)}"
            )

        # Add validation criteria
        criteria.append(
            f"THE {system_name} SHALL validate all input data before processing"
        )

        return criteria

    def check_compliance(self, requirements: List[str]) -> ValidationResult:
        """
        Check multiple requirements for EARS compliance.

        Args:
            requirements: List of requirements to validate

        Returns:
            Overall validation result
        """
        if not requirements:
            return ValidationResult(
                is_valid=False,
                issues=["No requirements provided"],
                suggestions=["Provide at least one requirement to validate"],
            )

        all_issues = []
        all_suggestions = []
        valid_count = 0
        detected_patterns = []

        for i, requirement in enumerate(requirements):
            result = self.validate(requirement)

            if result.is_valid:
                valid_count += 1
                if result.pattern:
                    detected_patterns.append(result.pattern)
            else:
                # Add requirement index to issues for clarity
                indexed_issues = [
                    f"Requirement {i+1}: {issue}" for issue in result.issues
                ]
                all_issues.extend(indexed_issues)

                indexed_suggestions = [
                    f"Requirement {i+1}: {suggestion}"
                    for suggestion in result.suggestions
                ]
                all_suggestions.extend(indexed_suggestions)

        # Check for pattern diversity (good practice)
        unique_patterns = set(detected_patterns)
        if len(unique_patterns) == 1 and len(requirements) > 3:
            all_suggestions.append(
                "Consider using different EARS patterns for variety and completeness"
            )

        # Overall compliance assessment
        compliance_rate = valid_count / len(requirements)
        is_compliant = compliance_rate >= 0.8  # 80% compliance threshold

        if not is_compliant:
            all_issues.append(
                f"Overall compliance: {compliance_rate:.1%} (minimum 80% required)"
            )

        return ValidationResult(
            is_valid=is_compliant,
            issues=all_issues,
            suggestions=all_suggestions,
            pattern=None,  # Not applicable for bulk validation
        )
