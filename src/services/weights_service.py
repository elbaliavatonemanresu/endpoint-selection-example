"""Weights Service for managing criterion weights."""
from typing import List

from src.domain.models import Scenario, Criterion
from src.domain.errors import LockedError, StateError, NotFoundError, ValidationError
from src.domain.policies import can_lock_weights, can_unlock_weights
from src.services.audit_service import AuditService


class WeightsService:
    """Service for criterion weight management."""

    def __init__(self):
        """Initialize the weights service."""
        self.audit_service = AuditService()

    def lock_weights(self, scenario: Scenario, actor: str) -> Scenario:
        """
        Lock weights to prevent further changes.

        Args:
            scenario: The scenario
            actor: Who is locking the weights

        Returns:
            Updated scenario with weights locked

        Raises:
            StateError: If weights are already locked
        """
        if not can_lock_weights(scenario):
            raise StateError("Weights are already locked")

        # Update scenario
        updated = scenario.model_copy(update={"weightsLocked": True})

        # Log audit event
        updated = self.audit_service.log_weights_locked(updated, actor)

        return updated

    def unlock_weights(self, scenario: Scenario, actor: str, reason: str) -> Scenario:
        """
        Unlock weights to allow changes.

        Args:
            scenario: The scenario
            actor: Who is unlocking the weights
            reason: Reason for unlocking

        Returns:
            Updated scenario with weights unlocked

        Raises:
            StateError: If weights are already unlocked
        """
        if not can_unlock_weights(scenario):
            raise StateError("Weights are already unlocked")

        # Update scenario
        updated = scenario.model_copy(update={"weightsLocked": False})

        # Log audit event
        updated = self.audit_service.log_weights_unlocked(updated, actor, reason)

        return updated

    def set_weight(
        self,
        scenario: Scenario,
        criterion_id: str,
        weight: int,
        actor: str,
        reason: str,
    ) -> Scenario:
        """
        Set the weight of a criterion.

        Args:
            scenario: The scenario
            criterion_id: ID of the criterion to update
            weight: New weight value (must be >= 0)
            actor: Who is making the change
            reason: Reason for the change

        Returns:
            Updated scenario with new weight

        Raises:
            LockedError: If weights are locked
            NotFoundError: If criterion doesn't exist
            ValidationError: If weight is negative
        """
        # Check if weights are locked
        if scenario.weightsLocked:
            raise LockedError("Cannot change weights: weights are locked")

        # Validate weight
        if weight < 0:
            raise ValidationError("Weight must be non-negative")

        # Find the criterion
        criterion_index = None
        old_criterion = None
        for i, c in enumerate(scenario.criteria):
            if c.id == criterion_id:
                criterion_index = i
                old_criterion = c
                break

        if criterion_index is None:
            raise NotFoundError(f"Criterion with id '{criterion_id}' not found")

        # Get old weight for audit
        old_weight = old_criterion.weight

        # Create updated criterion
        updated_criterion = old_criterion.model_copy(update={"weight": weight})

        # Create new criteria list with updated criterion
        new_criteria = list(scenario.criteria)
        new_criteria[criterion_index] = updated_criterion

        # Update scenario
        updated = scenario.model_copy(update={"criteria": new_criteria})

        # Log audit event
        updated = self.audit_service.log_weight_change(
            updated, actor, criterion_id, old_weight, weight, reason
        )

        return updated

    def get_total_weight(self, scenario: Scenario) -> int:
        """
        Calculate the total weight of all criteria.

        Args:
            scenario: The scenario

        Returns:
            Sum of all criterion weights
        """
        return sum(c.weight for c in scenario.criteria)
