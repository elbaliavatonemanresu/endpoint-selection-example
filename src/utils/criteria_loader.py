"""Utility to load full criteria descriptions from CSV."""
import csv
from pathlib import Path
from typing import Dict, List, Tuple
from src.domain.models import Criterion


def load_full_criteria_descriptions(criteria: List[Criterion]) -> Dict[str, Tuple[str, str]]:
    """
    Load full criteria descriptions and anchors from CSV, mapped by criterion ID.

    The CSV rows are in the same order as the criteria in the JSON, so we map by position.

    Args:
        criteria: List of Criterion objects from the scenario (used for ID mapping)

    Returns:
        Dict mapping criterion ID to (high_anchor, low_anchor) tuple with full text
    """
    csv_path = Path(__file__).parent.parent.parent / "full_criteria_descriptions.csv"

    criteria_map = {}

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            # Skip header rows
            next(reader, None)  # Row 1: Headers
            next(reader, None)  # Row 2: Empty
            next(reader, None)  # Row 3: Empty

            # Process rows in order, mapping by position to criterion IDs
            csv_rows = []
            for row in reader:
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    csv_rows.append(row)

            # Map each CSV row to corresponding criterion by position
            for idx, row in enumerate(csv_rows):
                if idx >= len(criteria):
                    break  # More CSV rows than criteria

                criterion_id = criteria[idx].id
                anchors_text = row[1].strip()

                # Parse anchors: "5 -- [high text]\n1 -- [low text]"
                lines = anchors_text.split('\n')
                high_anchor = ""
                low_anchor = ""

                for line in lines:
                    line = line.strip()
                    if line.startswith('5 –') or line.startswith('5 --'):
                        # Extract text after "5 – " or "5 -- "
                        high_anchor = line.split('–', 1)[1].strip() if '–' in line else line.split('--', 1)[1].strip()
                    elif line.startswith('1 –') or line.startswith('1 --'):
                        # Extract text after "1 – " or "1 -- "
                        low_anchor = line.split('–', 1)[1].strip() if '–' in line else line.split('--', 1)[1].strip()

                if high_anchor and low_anchor:
                    criteria_map[criterion_id] = (high_anchor, low_anchor)

    except FileNotFoundError:
        # If CSV not found, return empty dict (will fall back to short anchors)
        pass

    return criteria_map
