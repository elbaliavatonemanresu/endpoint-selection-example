"""Audit Service for tracking scenario changes."""
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.domain.models import Scenario, AuditEvent


class AuditService:
    """Service for audit trail management."""

    def log_event(
        self,
        scenario: Scenario,
        actor: str,
        event_type: str,
        details: Dict[str, Any],
    ) -> Scenario:
        """
        Log an audit event to the scenario.

        Args:
            scenario: The scenario to log to
            actor: Who performed the action
            event_type: Type of event (e.g., "score_changed", "weight_changed")
            details: Additional event details

        Returns:
            Updated scenario with new audit event
        """
        event = AuditEvent(
            ts=datetime.now(),
            actor=actor,
            type=event_type,
            details=details,
        )

        # Create new audit list with event appended
        new_audit = scenario.audit + [event]

        # Return updated scenario
        return scenario.model_copy(update={"audit": new_audit})

    def get_history(
        self,
        scenario: Scenario,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> List[AuditEvent]:
        """
        Get audit history with optional filtering.

        Args:
            scenario: The scenario to query
            event_type: Optional filter by event type
            actor: Optional filter by actor

        Returns:
            List of audit events (in chronological order)
        """
        events = scenario.audit

        # Apply filters
        if event_type is not None:
            events = [e for e in events if e.type == event_type]

        if actor is not None:
            events = [e for e in events if e.actor == actor]

        return events

    def log_score_change(
        self,
        scenario: Scenario,
        actor: str,
        option_id: str,
        criterion_id: str,
        old_value: Optional[int],
        new_value: int,
    ) -> Scenario:
        """
        Log a score change event.

        Args:
            scenario: The scenario
            actor: Who made the change
            option_id: Option that was scored
            criterion_id: Criterion that was scored
            old_value: Previous score value (None if new)
            new_value: New score value

        Returns:
            Updated scenario with audit event
        """
        return self.log_event(
            scenario=scenario,
            actor=actor,
            event_type="score_changed",
            details={
                "optionId": option_id,
                "criterionId": criterion_id,
                "oldValue": old_value,
                "newValue": new_value,
            },
        )

    def log_weight_change(
        self,
        scenario: Scenario,
        actor: str,
        criterion_id: str,
        old_weight: int,
        new_weight: int,
        reason: str,
    ) -> Scenario:
        """
        Log a weight change event.

        Args:
            scenario: The scenario
            actor: Who made the change
            criterion_id: Criterion whose weight changed
            old_weight: Previous weight
            new_weight: New weight
            reason: Reason for the change

        Returns:
            Updated scenario with audit event
        """
        return self.log_event(
            scenario=scenario,
            actor=actor,
            event_type="weight_changed",
            details={
                "criterionId": criterion_id,
                "oldWeight": old_weight,
                "newWeight": new_weight,
                "reason": reason,
            },
        )

    def log_weights_locked(self, scenario: Scenario, actor: str) -> Scenario:
        """
        Log weights locked event.

        Args:
            scenario: The scenario
            actor: Who locked the weights

        Returns:
            Updated scenario with audit event
        """
        return self.log_event(
            scenario=scenario,
            actor=actor,
            event_type="weights_locked",
            details={},
        )

    def log_weights_unlocked(
        self, scenario: Scenario, actor: str, reason: str
    ) -> Scenario:
        """
        Log weights unlocked event.

        Args:
            scenario: The scenario
            actor: Who unlocked the weights
            reason: Reason for unlocking

        Returns:
            Updated scenario with audit event
        """
        return self.log_event(
            scenario=scenario,
            actor=actor,
            event_type="weights_unlocked",
            details={"reason": reason},
        )
