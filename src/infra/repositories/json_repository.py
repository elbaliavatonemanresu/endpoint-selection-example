"""JSON file-based repository implementation."""
import json
import re
from pathlib import Path
from typing import List

from src.domain.models import Scenario
from src.domain.errors import NotFoundError, ValidationError
from src.infra.repositories.repository import Repository


class JsonRepository(Repository):
    """Repository implementation that stores scenarios as JSON files."""

    def __init__(self, base_path: Path | str):
        """
        Initialize the JSON repository.

        Args:
            base_path: Base directory for storing scenario JSON files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, scenario_id: str) -> Path:
        """
        Get the file path for a scenario ID.

        Args:
            scenario_id: The scenario ID to get the path for

        Returns:
            Path object for the scenario file

        Raises:
            ValidationError: If scenario_id contains invalid characters
        """
        # Validate scenario_id to prevent path traversal attacks
        if not scenario_id or not scenario_id.strip():
            raise ValidationError("scenario_id cannot be empty")

        # Check for path traversal attempts
        if '..' in scenario_id or '/' in scenario_id or '\\' in scenario_id:
            raise ValidationError(f"Invalid scenario_id: contains path separators")

        # Only allow alphanumeric characters, underscores, and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', scenario_id):
            raise ValidationError(f"scenario_id contains invalid characters: {scenario_id}")

        return self.base_path / f"{scenario_id}.json"

    def save(self, scenario: Scenario) -> None:
        """
        Save a scenario to a JSON file using atomic write.

        Args:
            scenario: The scenario to save

        Raises:
            IOError: If save operation fails
        """
        file_path = self._get_file_path(scenario.id)
        temp_path = file_path.with_suffix(".tmp")

        try:
            # Write to temporary file first
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(
                    scenario.model_dump(mode="json"),
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            # Atomic rename
            temp_path.replace(file_path)

        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise IOError(f"Failed to save scenario {scenario.id}: {e}")

    def load(self, scenario_id: str) -> Scenario:
        """
        Load a scenario from a JSON file.

        Args:
            scenario_id: The ID of the scenario to load

        Returns:
            The loaded scenario

        Raises:
            NotFoundError: If scenario file doesn't exist
            IOError: If load operation fails
        """
        file_path = self._get_file_path(scenario_id)

        if not file_path.exists():
            raise NotFoundError(f"Scenario with id '{scenario_id}' not found")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Scenario.model_validate(data)
        except json.JSONDecodeError as e:
            raise IOError(f"Invalid JSON in scenario file {scenario_id}: {e}")
        except Exception as e:
            raise IOError(f"Failed to load scenario {scenario_id}: {e}")

    def exists(self, scenario_id: str) -> bool:
        """
        Check if a scenario file exists.

        Args:
            scenario_id: The ID of the scenario to check

        Returns:
            True if scenario exists, False otherwise
        """
        return self._get_file_path(scenario_id).exists()

    def list(self) -> List[str]:
        """
        List all scenario IDs in the repository.

        Returns:
            List of scenario IDs (without .json extension)
        """
        if not self.base_path.exists():
            return []

        json_files = self.base_path.glob("*.json")
        return [f.stem for f in json_files]

    def delete(self, scenario_id: str) -> None:
        """
        Delete a scenario file.

        Args:
            scenario_id: The ID of the scenario to delete

        Raises:
            NotFoundError: If scenario doesn't exist
            IOError: If delete operation fails
        """
        file_path = self._get_file_path(scenario_id)

        if not file_path.exists():
            raise NotFoundError(f"Scenario with id '{scenario_id}' not found")

        try:
            file_path.unlink()
        except Exception as e:
            raise IOError(f"Failed to delete scenario {scenario_id}: {e}")
