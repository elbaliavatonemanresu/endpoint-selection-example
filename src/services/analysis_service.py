"""Analysis Service for leaderboards, contributions, deltas, and sensitivity analysis."""
from typing import List, Dict, Any

from src.domain.models import Scenario
from src.domain.errors import NotFoundError


class AnalysisService:
    """Service for analyzing scenario results."""

    def leaderboard(self, scenario: Scenario) -> List[Dict[str, Any]]:
        """
        Generate leaderboard with rankings for all options.

        Args:
            scenario: The scenario to analyze

        Returns:
            List of dicts sorted by total (descending), each containing:
            - optionId: The option ID
            - name: The option name
            - total: Weighted total score
            - normalized: Normalized score (0-100)
            - rank: Rank (1-based, ties get same rank)
        """
        # Calculate totals for all options
        totals = self._calculate_totals(scenario)

        # Build leaderboard entries
        leaderboard = []
        for option in scenario.options:
            option_data = totals.get(option.id, {"total": 0, "normalized": 0.0})
            leaderboard.append(
                {
                    "optionId": option.id,
                    "name": option.name,
                    "total": option_data["total"],
                    "normalized": option_data["normalized"],
                }
            )

        # Sort by total descending
        leaderboard.sort(key=lambda x: x["total"], reverse=True)

        # Assign ranks (handle ties)
        current_rank = 1
        for i, entry in enumerate(leaderboard):
            if i > 0 and entry["total"] < leaderboard[i - 1]["total"]:
                current_rank = i + 1
            entry["rank"] = current_rank

        return leaderboard

    def contributions(
        self, scenario: Scenario, option_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate criterion-by-criterion contributions for specified options.

        Args:
            scenario: The scenario to analyze
            option_ids: List of option IDs to include in analysis

        Returns:
            Dict containing:
            - For each option_id: dict mapping criterion_id to weighted score
            - "criteria": metadata about criteria (name, weight)
        """
        # Build weights map
        weights = {c.id: c.weight for c in scenario.criteria}

        # Build result structure
        result: Dict[str, Any] = {}

        # Add criterion metadata
        result["criteria"] = {}
        for criterion in scenario.criteria:
            result["criteria"][criterion.id] = {
                "name": criterion.name,
                "weight": criterion.weight,
            }

        # Calculate contributions for each requested option
        for option_id in option_ids:
            contributions_map: Dict[str, int] = {}
            total = 0

            # Sum weighted scores by criterion
            for score in scenario.scores:
                if score.optionId == option_id:
                    weight = weights.get(score.criterionId, 0)
                    weighted_score = score.raw * weight
                    contributions_map[score.criterionId] = weighted_score
                    total += weighted_score

            # Add total to the contributions
            contributions_map["total"] = total
            result[option_id] = contributions_map

        return result

    def delta_to_winner(self, scenario: Scenario) -> Dict[str, Any]:
        """
        Calculate gaps between each option and the winner.

        Args:
            scenario: The scenario to analyze

        Returns:
            Dict containing:
            - "winner": ID of the winning option
            - For each option_id: dict with "total" and "delta" (gap to winner)
        """
        # Get totals for all options
        totals = self._calculate_totals(scenario)

        # Find winner (highest total)
        winner_id = None
        max_total = -1

        for option in scenario.options:
            option_total = totals.get(option.id, {"total": 0})["total"]
            if option_total > max_total:
                max_total = option_total
                winner_id = option.id

        # If all tied at 0, pick first option as winner
        if winner_id is None and scenario.options:
            winner_id = scenario.options[0].id
            max_total = 0

        # Calculate deltas
        result: Dict[str, Any] = {"winner": winner_id}

        for option in scenario.options:
            option_total = totals.get(option.id, {"total": 0})["total"]
            delta = max_total - option_total

            result[option.id] = {"total": option_total, "delta": delta}

        return result

    def sensitivity(
        self, scenario: Scenario, criterion_id: str, pct: float
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis by adjusting a criterion weight.

        Args:
            scenario: The scenario to analyze
            criterion_id: The criterion to adjust
            pct: Percentage change (e.g., 50.0 for +50%, -50.0 for -50%)

        Returns:
            Dict containing:
            - "criterionId": The adjusted criterion ID
            - "pct": The percentage change
            - "original": Original leaderboard
            - "adjusted": Leaderboard after weight adjustment

        Raises:
            NotFoundError: If criterion doesn't exist
        """
        # Validate criterion exists
        criterion = next((c for c in scenario.criteria if c.id == criterion_id), None)
        if criterion is None:
            raise NotFoundError(f"Criterion with id '{criterion_id}' not found")

        # Get original leaderboard
        original_leaderboard = self.leaderboard(scenario)

        # Calculate adjusted weight
        original_weight = criterion.weight
        weight_delta = original_weight * (pct / 100.0)
        adjusted_weight = original_weight + weight_delta

        # Ensure weight doesn't go negative (clamp to 0)
        adjusted_weight = max(0, adjusted_weight)

        # Create modified scenario with adjusted weight
        adjusted_criteria = []
        for c in scenario.criteria:
            if c.id == criterion_id:
                adjusted_criteria.append(c.model_copy(update={"weight": adjusted_weight}))
            else:
                adjusted_criteria.append(c)

        adjusted_scenario = scenario.model_copy(update={"criteria": adjusted_criteria})

        # Get adjusted leaderboard
        adjusted_leaderboard = self.leaderboard(adjusted_scenario)

        return {
            "criterionId": criterion_id,
            "pct": pct,
            "original": original_leaderboard,
            "adjusted": adjusted_leaderboard,
        }

    def _calculate_totals(self, scenario: Scenario) -> Dict[str, Dict[str, Any]]:
        """
        Calculate weighted totals for all options.

        Args:
            scenario: The scenario

        Returns:
            Dict mapping option_id to {total: int, normalized: float}
        """
        # Build weights map
        weights = {c.id: c.weight for c in scenario.criteria}

        # Calculate max possible score
        max_possible = sum(c.weight * 5 for c in scenario.criteria)

        # Calculate totals for each option
        totals: Dict[str, Dict[str, Any]] = {}

        for option in scenario.options:
            option_total = 0

            # Sum weighted scores
            for score in scenario.scores:
                if score.optionId == option.id:
                    weight = weights.get(score.criterionId, 0)
                    option_total += score.raw * weight

            # Calculate normalized score
            normalized = (option_total / max_possible * 100) if max_possible > 0 else 0.0

            totals[option.id] = {"total": option_total, "normalized": normalized}

        return totals
