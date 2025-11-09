"""Storage path utilities for CTTI scenarios."""
from pathlib import Path


class StoragePaths:
    """Utilities for managing storage paths."""

    @staticmethod
    def get_default_storage_path() -> Path:
        """
        Get the default storage path for scenarios.

        Returns:
            Path to default storage directory (user home/.ctti_scenarios/)
        """
        return Path.home() / ".ctti_scenarios"

    @staticmethod
    def get_backup_dir(base_path: Path) -> Path:
        """
        Get the backup directory path for a given base path.

        Args:
            base_path: Base storage path

        Returns:
            Path to backup directory
        """
        return base_path / "backups"

    @staticmethod
    def ensure_storage_paths(base_path: Path) -> None:
        """
        Ensure all required storage directories exist.

        Args:
            base_path: Base storage path
        """
        base_path.mkdir(parents=True, exist_ok=True)

        # Also create backup directory
        backup_dir = StoragePaths.get_backup_dir(base_path)
        backup_dir.mkdir(parents=True, exist_ok=True)
