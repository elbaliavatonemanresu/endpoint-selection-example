"""Domain policies for state machines and business rules."""
from src.domain.models import Scenario, Settings


def can_lock_weights(scenario: Scenario) -> bool:
    """
    Check if weights can be locked.

    Args:
        scenario: The scenario to check

    Returns:
        True if weights can be locked (currently unlocked), False otherwise
    """
    return not scenario.weightsLocked


def can_unlock_weights(scenario: Scenario) -> bool:
    """
    Check if weights can be unlocked.

    Args:
        scenario: The scenario to check

    Returns:
        True if weights can be unlocked (currently locked), False otherwise
    """
    return scenario.weightsLocked


def is_rationale_required(settings: Settings) -> bool:
    """
    Check if rationale is required based on settings.

    Args:
        settings: The scenario settings

    Returns:
        True if rationale is required, False otherwise
    """
    return settings.rationalePolicy == "required"


def is_rationale_skippable(settings: Settings) -> bool:
    """
    Check if rationale can be skipped based on settings.

    Args:
        settings: The scenario settings

    Returns:
        True if rationale can be skipped, False if required
    """
    return settings.rationalePolicy in ["optional", "skippable"]
