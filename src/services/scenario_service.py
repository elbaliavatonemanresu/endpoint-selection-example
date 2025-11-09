"""Scenario Service for creating and managing scenarios."""
import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.domain.models import Scenario, Option, Criterion, Settings
from src.domain.errors import ValidationError, NotFoundError
from src.infra.storage.file_store import FileStore


class ScenarioService:
    """Service for scenario lifecycle management."""

    def __init__(self, storage_path: Optional[Path | str] = None):
        """
        Initialize the scenario service.

        Args:
            storage_path: Optional custom storage path. If None, uses default.
        """
        if storage_path is None:
            from src.infra.storage.paths import StoragePaths

            storage_path = StoragePaths.get_default_storage_path()

        self.file_store = FileStore(storage_path)

    def create(
        self,
        title: str,
        options: List[str],
        custom_criteria: Optional[List[Criterion]] = None,
    ) -> Scenario:
        """
        Create a new scenario.

        Args:
            title: Scenario title
            options: List of option names
            custom_criteria: Optional custom criteria. If None, loads default CTTI criteria.

        Returns:
            New scenario instance

        Raises:
            ValidationError: If title is empty or no options provided
        """
        # Validate inputs
        if not title or not title.strip():
            raise ValidationError("Scenario title cannot be empty")

        if len(title) > 200:
            raise ValidationError("Scenario title must be 200 characters or less")

        if not options:
            raise ValidationError("At least one option is required")

        # Validate option names
        for i, opt_name in enumerate(options):
            if not opt_name or not opt_name.strip():
                raise ValidationError(f"Option {i+1} name cannot be empty")
            if len(opt_name) > 100:
                raise ValidationError(f"Option {i+1} name must be 100 characters or less")

        # Generate unique ID (12 characters for better collision resistance)
        scenario_id = str(uuid.uuid4())[:12]

        # Create options
        option_models = [
            Option(id=f"opt{i+1}", name=name) for i, name in enumerate(options)
        ]

        # Load criteria
        if custom_criteria is not None:
            criteria = custom_criteria
        else:
            criteria = self._load_default_criteria()

        # Create scenario
        scenario = Scenario(
            id=scenario_id,
            title=title,
            criteria=criteria,
            options=option_models,
            scores=[],
            settings=Settings(),
            audit=[],
        )

        return scenario

    def save(self, scenario: Scenario) -> None:
        """
        Save a scenario to storage.

        Args:
            scenario: The scenario to save
        """
        self.file_store.save(scenario)

    def open(self, scenario_id: str) -> Scenario:
        """
        Open an existing scenario.

        Args:
            scenario_id: The ID of the scenario to open

        Returns:
            Loaded scenario

        Raises:
            NotFoundError: If scenario doesn't exist
        """
        return self.file_store.repository.load(scenario_id)

    def progress(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Calculate scenario completion progress.

        Args:
            scenario: The scenario to analyze

        Returns:
            Dict with progress metrics:
            - total_cells: Total number of score cells
            - scored_cells: Number of cells with scores
            - percent_complete: Percentage complete
            - weights_locked: Whether weights are locked
        """
        total_cells = len(scenario.options) * len(scenario.criteria)
        scored_cells = len(scenario.scores)

        percent_complete = (scored_cells / total_cells * 100) if total_cells > 0 else 0.0

        return {
            "total_cells": total_cells,
            "scored_cells": scored_cells,
            "percent_complete": percent_complete,
            "weights_locked": scenario.weightsLocked,
        }

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """
        List all scenarios in storage.

        Returns:
            List of scenario metadata dicts
        """
        return self.file_store.list_scenarios()

    def exists(self, scenario_id: str) -> bool:
        """
        Check if a scenario exists.

        Args:
            scenario_id: The scenario ID to check

        Returns:
            True if exists, False otherwise
        """
        return self.file_store.repository.exists(scenario_id)

    def delete(self, scenario_id: str) -> None:
        """
        Delete a scenario.

        Args:
            scenario_id: The ID of the scenario to delete

        Raises:
            NotFoundError: If scenario doesn't exist
        """
        self.file_store.repository.delete(scenario_id)

    def _load_default_criteria(self) -> List[Criterion]:
        """
        Load default CTTI criteria from assets.

        Returns:
            List of default criteria

        Raises:
            IOError: If criteria file cannot be loaded
        """
        criteria_path = (
            Path(__file__).parent.parent.parent
            / "assets"
            / "criteria"
            / "ctti_default_criteria.json"
        )

        if not criteria_path.exists():
            raise IOError(f"Default criteria file not found: {criteria_path}")

        with open(criteria_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Parse criteria from JSON
        criteria = [Criterion.model_validate(c) for c in data["criteria"]]

        return criteria
