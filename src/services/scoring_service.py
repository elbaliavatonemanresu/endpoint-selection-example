"""Scoring Service for managing option scores."""
from typing import Dict, Any, Optional

from src.domain.models import Scenario, Score
from src.domain.errors import ValidationError, NotFoundError
from src.services.audit_service import AuditService


class ScoringService:
    """Service for score management."""

    def __init__(self):
        """Initialize the scoring service."""
        self.audit_service = AuditService()

    def set_score(
        self,
        scenario: Scenario,
        option_id: str,
        criterion_id: str,
        raw: int,
        actor: str,
        rationale: Optional[str] = None,
    ) -> Scenario:
        """
        Set a score for an option on a criterion.

        Args:
            scenario: The scenario
            option_id: ID of the option
            criterion_id: ID of the criterion
            raw: Raw score value (1-5)
            actor: Who is setting the score
            rationale: Optional rationale

        Returns:
            Updated scenario

        Raises:
            ValidationError: If score is out of range
            NotFoundError: If option or criterion doesn't exist
        """
        # Validate score range
        if not 1 <= raw <= 5:
            raise ValidationError("Score must be between 1 and 5")

        # Validate option exists
        if not any(o.id == option_id for o in scenario.options):
            raise NotFoundError(f"Option with id '{option_id}' not found")

        # Validate criterion exists
        criterion = next((c for c in scenario.criteria if c.id == criterion_id), None)
        if criterion is None:
            raise NotFoundError(f"Criterion with id '{criterion_id}' not found")

        # Find existing score
        existing_score = None
        score_index = None
        for i, s in enumerate(scenario.scores):
            if s.optionId == option_id and s.criterionId == criterion_id:
                existing_score = s
                score_index = i
                break

        # Determine old value for audit
        old_value = existing_score.raw if existing_score else None

        # Create or update score
        new_score = Score(
            optionId=option_id,
            criterionId=criterion_id,
            raw=raw,
            rationale=rationale if rationale is not None else (existing_score.rationale if existing_score else None),
        )

        # Update scores list
        new_scores = list(scenario.scores)
        if score_index is not None:
            new_scores[score_index] = new_score
        else:
            new_scores.append(new_score)

        # Update scenario
        updated = scenario.model_copy(update={"scores": new_scores})

        # Log audit event
        updated = self.audit_service.log_score_change(
            updated, actor, option_id, criterion_id, old_value, raw
        )

        return updated

    def set_rationale(
        self,
        scenario: Scenario,
        option_id: str,
        criterion_id: str,
        rationale: str,
        actor: str,
    ) -> Scenario:
        """
        Set rationale for a score.

        Args:
            scenario: The scenario
            option_id: ID of the option
            criterion_id: ID of the criterion
            rationale: The rationale text
            actor: Who is setting the rationale

        Returns:
            Updated scenario

        Raises:
            ValidationError: If rationale is too long
        """
        # Validate rationale length
        if rationale and len(rationale) > 500:
            raise ValidationError("Rationale must be 500 characters or less")

        # Find existing score
        existing_score = None
        score_index = None
        for i, s in enumerate(scenario.scores):
            if s.optionId == option_id and s.criterionId == criterion_id:
                existing_score = s
                score_index = i
                break

        # If no score exists, create one with default value
        if existing_score is None:
            # Create a score with rationale but no raw value yet (default to 3)
            new_score = Score(
                optionId=option_id,
                criterionId=criterion_id,
                raw=3,  # Default middle value
                rationale=rationale,
            )
            new_scores = scenario.scores + [new_score]
        else:
            # Update existing score with new rationale
            new_score = existing_score.model_copy(update={"rationale": rationale})
            new_scores = list(scenario.scores)
            new_scores[score_index] = new_score

        # Update scenario
        updated = scenario.model_copy(update={"scores": new_scores})

        return updated

    def totals(self, scenario: Scenario) -> Dict[str, Dict[str, Any]]:
        """
        Calculate weighted totals for all options.

        Args:
            scenario: The scenario

        Returns:
            Dict mapping option_id to {total: int, normalized: float}
        """
        # Build a map of weights by criterion ID
        weights = {c.id: c.weight for c in scenario.criteria}

        # Calculate maximum possible score
        max_possible = sum(c.weight * 5 for c in scenario.criteria)

        # Calculate totals for each option
        totals = {}
        for option in scenario.options:
            option_total = 0

            # Sum weighted scores for this option
            for score in scenario.scores:
                if score.optionId == option.id:
                    weight = weights.get(score.criterionId, 0)
                    option_total += score.raw * weight

            # Calculate normalized score (0-100)
            normalized = (option_total / max_possible * 100) if max_possible > 0 else 0.0

            totals[option.id] = {
                "total": option_total,
                "normalized": normalized,
            }

        return totals
