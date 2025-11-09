"""Export Service for generating PDF reports."""
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.domain.models import Scenario
from src.services.scenario_service import ScenarioService
from src.services.analysis_service import AnalysisService
from src.infra.pdf.pdf_builder import PDFBuilder


class ExportService:
    """Service for exporting scenarios to PDF reports."""

    def __init__(self):
        """Initialize export service."""
        self.scenario_service = ScenarioService()
        self.analysis_service = AnalysisService()

    def build_pdf(
        self,
        scenario: Scenario,
        output_path: str,
        include_rationales: bool = True,
    ) -> str:
        """
        Generate a PDF report for a scenario.

        Args:
            scenario: The scenario to export
            output_path: Path where to save the PDF
            include_rationales: Whether to include rationales appendix

        Returns:
            Path to the generated PDF file

        Raises:
            ValueError: If scenario has no scores
        """
        if not scenario.scores:
            raise ValueError("Cannot export scenario with no scores")

        # Create PDF builder
        with PDFBuilder() as pdf:
            # Add sections
            self._add_cover_page(pdf, scenario)
            self._add_leaderboard_section(pdf, scenario)
            self._add_contributions_section(pdf, scenario)
            self._add_deltas_section(pdf, scenario)

            if include_rationales:
                self._add_rationale_appendix(pdf, scenario)

            self._add_metadata_footer(pdf, scenario)

            # Save PDF
            pdf.save(output_path)

        return output_path

    def _add_cover_page(self, pdf: PDFBuilder, scenario: Scenario):
        """Add cover page with scenario title and metadata."""
        pdf.add_page()

        # Add vertical spacing for visual balance
        pdf.add_spacing(100)

        # Title
        pdf.add_title(scenario.title)

        pdf.add_spacing(30)

        # Metadata
        pdf.add_body_text(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}")
        pdf.add_body_text(f"Scenario ID: {scenario.id}")

        pdf.add_spacing(20)

        # Weights status
        weights_status = "Locked ✓" if scenario.weightsLocked else "Unlocked"
        pdf.add_body_text(f"Weights: {weights_status}")

        # Options and criteria counts
        pdf.add_body_text(f"Options: {len(scenario.options)}")
        pdf.add_body_text(f"Criteria: {len(scenario.criteria)}")
        pdf.add_body_text(f"Scores: {len(scenario.scores)}")

        pdf.add_spacing(40)

        # CTTI branding
        pdf.add_small_text("CTTI Endpoint Selection Facilitator")

    def _add_leaderboard_section(self, pdf: PDFBuilder, scenario: Scenario):
        """Add leaderboard section with rankings table."""
        pdf.add_page()

        pdf.add_heading("Leaderboard")
        pdf.add_horizontal_line()
        pdf.add_spacing(10)

        # Get leaderboard data
        leaderboard = self.analysis_service.leaderboard(scenario)

        if not leaderboard:
            pdf.add_body_text("No leaderboard data available.")
            return

        # Prepare table data
        headers = ["Rank", "Option", "Total Score", "Normalized (%)"]
        rows = []

        for entry in leaderboard:
            rows.append(
                [
                    entry["rank"],
                    entry["name"],
                    f"{entry['total']:.1f}",
                    f"{entry['normalized']:.1f}%",
                ]
            )

        # Add table
        pdf.add_table(headers, rows, col_widths=[60, 250, 120, 120])

        pdf.add_spacing(20)

        # Winner summary
        winner = leaderboard[0]
        pdf.add_subheading(f"Winner: {winner['name']}")
        pdf.add_body_text(
            f"Total Score: {winner['total']:.1f} ({winner['normalized']:.1f}%)"
        )

    def _add_contributions_section(self, pdf: PDFBuilder, scenario: Scenario):
        """Add contributions analysis section."""
        pdf.add_page()

        pdf.add_heading("Contributions Analysis")
        pdf.add_horizontal_line()
        pdf.add_spacing(10)

        # Get leaderboard to identify winner and runner-up
        leaderboard = self.analysis_service.leaderboard(scenario)

        if len(leaderboard) < 2:
            pdf.add_body_text("Need at least 2 options for contributions analysis.")
            return

        winner_id = leaderboard[0]["optionId"]
        runner_up_id = leaderboard[1]["optionId"]

        # Get contributions
        contributions = self.analysis_service.contributions(
            scenario, [winner_id, runner_up_id]
        )

        pdf.add_body_text(
            f"Comparing: {leaderboard[0]['name']} (winner) vs {leaderboard[1]['name']} (runner-up)"
        )
        pdf.add_spacing(10)

        # Prepare table
        headers = [
            "Criterion",
            "Weight",
            leaderboard[0]["name"],
            leaderboard[1]["name"],
        ]
        rows = []

        for criterion_id, criterion_info in contributions["criteria"].items():
            winner_contrib = contributions[winner_id].get(criterion_id, 0)
            runner_up_contrib = contributions[runner_up_id].get(criterion_id, 0)

            rows.append(
                [
                    criterion_info["name"],
                    criterion_info["weight"],
                    f"{winner_contrib:.1f}",
                    f"{runner_up_contrib:.1f}",
                ]
            )

        # Add totals row
        rows.append(
            [
                "TOTAL",
                "—",
                f"{contributions[winner_id]['total']:.1f}",
                f"{contributions[runner_up_id]['total']:.1f}",
            ]
        )

        pdf.add_table(headers, rows, col_widths=[200, 80, 130, 130])

    def _add_deltas_section(self, pdf: PDFBuilder, scenario: Scenario):
        """Add delta-to-winner analysis section."""
        pdf.add_page()

        pdf.add_heading("Gap to Winner")
        pdf.add_horizontal_line()
        pdf.add_spacing(10)

        # Get deltas
        deltas = self.analysis_service.delta_to_winner(scenario)

        winner_id = deltas["winner"]
        winner_name = next(opt.name for opt in scenario.options if opt.id == winner_id)

        pdf.add_body_text(f"Winner: {winner_name}")
        pdf.add_spacing(10)

        # Prepare table
        headers = ["Option", "Total Score", "Gap to Winner"]
        rows = []

        for option in scenario.options:
            delta_info = deltas[option.id]
            status = "Winner" if option.id == winner_id else f"{delta_info['delta']:.1f}"

            rows.append([option.name, f"{delta_info['total']:.1f}", status])

        pdf.add_table(headers, rows)

    def _add_rationale_appendix(self, pdf: PDFBuilder, scenario: Scenario):
        """Add rationale appendix section."""
        pdf.add_page()

        pdf.add_heading("Rationale Appendix")
        pdf.add_horizontal_line()
        pdf.add_spacing(10)

        # Count rationales
        rationales_count = sum(1 for score in scenario.scores if score.rationale)

        if rationales_count == 0:
            pdf.add_body_text("No rationales have been entered.")
            return

        pdf.add_body_text(f"{rationales_count} rationale(s) provided:")
        pdf.add_spacing(10)

        # Group scores by option
        for option in scenario.options:
            option_rationales = [
                score
                for score in scenario.scores
                if score.optionId == option.id and score.rationale
            ]

            if not option_rationales:
                continue

            pdf.add_subheading(f"Option: {option.name}")
            pdf.add_spacing(5)

            for score in option_rationales:
                # Find criterion name
                criterion = next(
                    (c for c in scenario.criteria if c.id == score.criterionId), None
                )
                if not criterion:
                    continue

                pdf.add_body_text(f"• {criterion.name} (Score: {score.raw}/5)")
                pdf.add_body_text(f"  {score.rationale}")
                pdf.add_spacing(5)

            pdf.add_spacing(10)

    def _add_metadata_footer(self, pdf: PDFBuilder, scenario: Scenario):
        """Add metadata footer to the last page."""
        if pdf.current_page is None:
            return

        # Position at bottom of page
        footer_y = pdf.PAGE_HEIGHT - pdf.MARGIN_BOTTOM + 10

        # Add separator line
        pdf.add_horizontal_line(y=footer_y - 5)

        # Compute scenario hash directly
        import hashlib
        import json
        scenario_json = scenario.model_dump_json(indent=2)
        scenario_hash = hashlib.sha256(scenario_json.encode()).hexdigest()[:16]

        pdf.add_small_text(f"Scenario Hash: {scenario_hash}")
        pdf.current_y = footer_y + 10
        pdf.add_small_text(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        pdf.add_small_text(f"CTTI App v0.1.0")
