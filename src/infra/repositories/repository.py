"""Abstract repository interface for scenario persistence."""
from abc import ABC, abstractmethod
from typing import List

from src.domain.models import Scenario


class Repository(ABC):
    """Abstract base class for scenario repositories."""

    @abstractmethod
    def save(self, scenario: Scenario) -> None:
        """
        Save a scenario to the repository.

        Args:
            scenario: The scenario to save

        Raises:
            IOError: If save operation fails
        """
        pass

    @abstractmethod
    def load(self, scenario_id: str) -> Scenario:
        """
        Load a scenario from the repository.

        Args:
            scenario_id: The ID of the scenario to load

        Returns:
            The loaded scenario

        Raises:
            NotFoundError: If scenario with given ID doesn't exist
            IOError: If load operation fails
        """
        pass

    @abstractmethod
    def exists(self, scenario_id: str) -> bool:
        """
        Check if a scenario exists in the repository.

        Args:
            scenario_id: The ID of the scenario to check

        Returns:
            True if scenario exists, False otherwise
        """
        pass

    @abstractmethod
    def list(self) -> List[str]:
        """
        List all scenario IDs in the repository.

        Returns:
            List of scenario IDs
        """
        pass

    @abstractmethod
    def delete(self, scenario_id: str) -> None:
        """
        Delete a scenario from the repository.

        Args:
            scenario_id: The ID of the scenario to delete

        Raises:
            NotFoundError: If scenario with given ID doesn't exist
            IOError: If delete operation fails
        """
        pass
