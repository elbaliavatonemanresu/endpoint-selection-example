"""File store with backup management for scenarios."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from src.domain.models import Scenario
from src.infra.repositories.json_repository import JsonRepository
from src.infra.storage.paths import StoragePaths


class FileStore:
    """File store with backup and hash management."""

    def __init__(self, base_path: Path | str):
        """
        Initialize the file store.

        Args:
            base_path: Base directory for storing scenarios
        """
        self.base_path = Path(base_path)
        self.repository = JsonRepository(base_path)
        StoragePaths.ensure_storage_paths(self.base_path)

    def save(self, scenario: Scenario, create_backup: bool = False) -> None:
        """
        Save a scenario, optionally creating a backup of existing file.

        Args:
            scenario: The scenario to save
            create_backup: If True, create backup before overwriting
        """
        # Create backup if requested and file exists
        if create_backup and self.repository.exists(scenario.id):
            self._create_backup(scenario.id)

        # Save the scenario
        self.repository.save(scenario)

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """
        List all scenarios with metadata.

        Returns:
            List of dicts with scenario info (id, title, modified time, etc.)
        """
        scenario_ids = self.repository.list()
        scenarios = []

        for scenario_id in scenario_ids:
            try:
                scenario = self.repository.load(scenario_id)
                scenarios.append(
                    {
                        "id": scenario.id,
                        "title": scenario.title,
                        "modifiedAt": scenario.modifiedAt,
                        "weightsLocked": scenario.weightsLocked,
                    }
                )
            except Exception:
                # Skip scenarios that can't be loaded
                continue

        # Sort by modified date, most recent first
        scenarios.sort(key=lambda s: s["modifiedAt"], reverse=True)
        return scenarios

    def _create_backup(self, scenario_id: str) -> None:
        """Create a timestamped backup of a scenario."""
        backup_dir = StoragePaths.get_backup_dir(self.base_path)
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Load current scenario
        scenario = self.repository.load(scenario_id)

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{scenario_id}_{timestamp}.json"
        backup_path = backup_dir / backup_filename

        # Save backup
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(scenario.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    def list_backups(self, scenario_id: str) -> List[Dict[str, Any]]:
        """
        List all backups for a scenario.

        Args:
            scenario_id: The scenario ID

        Returns:
            List of backup info dicts (filename, created time, etc.)
        """
        backup_dir = StoragePaths.get_backup_dir(self.base_path)

        if not backup_dir.exists():
            return []

        backups = []
        for backup_file in backup_dir.glob(f"{scenario_id}_*.json"):
            backups.append(
                {
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "created": datetime.fromtimestamp(backup_file.stat().st_mtime),
                }
            )

        # Sort by creation time, most recent first
        backups.sort(key=lambda b: b["created"], reverse=True)
        return backups

    def restore_from_backup(self, scenario_id: str, backup_filename: str) -> Scenario:
        """
        Restore a scenario from a backup file.

        Args:
            scenario_id: The scenario ID
            backup_filename: Name of the backup file

        Returns:
            The restored scenario
        """
        backup_dir = StoragePaths.get_backup_dir(self.base_path)
        backup_path = backup_dir / backup_filename

        with open(backup_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return Scenario.model_validate(data)

    def cleanup_old_backups(self, scenario_id: str, keep_count: int = 5) -> None:
        """
        Clean up old backups, keeping only the most recent ones.

        Args:
            scenario_id: The scenario ID
            keep_count: Number of most recent backups to keep
        """
        backups = self.list_backups(scenario_id)

        # Remove old backups beyond keep_count
        for backup in backups[keep_count:]:
            backup_path = Path(backup["path"])
            if backup_path.exists():
                backup_path.unlink()

    def get_scenario_hash(self, scenario: Scenario) -> str:
        """
        Generate a hash for scenario integrity verification.

        Args:
            scenario: The scenario to hash

        Returns:
            SHA256 hash of the scenario data
        """
        # Convert scenario to JSON string
        json_str = json.dumps(
            scenario.model_dump(mode="json"), sort_keys=True, ensure_ascii=False
        )

        # Generate SHA256 hash
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
