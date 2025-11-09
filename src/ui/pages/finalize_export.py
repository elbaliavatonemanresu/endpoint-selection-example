"""Finalize & Export Page."""
import streamlit as st
from datetime import datetime
from pathlib import Path

from src.services.export_service import ExportService
from src.infra.storage.paths import StoragePaths


def render():
    """Render the finalize and export page."""
    st.title("📄 Finalize & Export")

    if not st.session_state.scenario:
        st.warning("⚠️ No scenario loaded. Please go to Setup to create or load a scenario.")
        return

    scenario = st.session_state.scenario
    scenario_service = st.session_state.scenario_service

    # Get progress information
    progress = scenario_service.progress(scenario)

    st.markdown(
        "Review your scenario and export it to PDF. "
        "The PDF will include leaderboard, analysis, and optional rationales."
    )

    st.divider()

    # Scenario Summary Section
    st.subheader("📋 Scenario Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Scenario Title", scenario.title)

    with col2:
        st.metric("Options", len(scenario.options))

    with col3:
        st.metric("Criteria", len(scenario.criteria))

    # Progress metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Scoring Progress",
            f"{progress['percent_complete']:.1f}%",
            f"{progress['scored_cells']}/{progress['total_cells']} cells",
        )

    with col2:
        weights_status = "🔒 Locked" if progress["weights_locked"] else "🔓 Unlocked"
        st.metric("Weights Status", weights_status)

    with col3:
        # Count rationales
        rationale_count = sum(1 for score in scenario.scores if score.rationale)
        st.metric("Rationales", f"{rationale_count}/{len(scenario.scores)}")

    # Validation warnings
    st.divider()

    if progress["percent_complete"] < 100:
        st.warning(
            f"⚠️ **Incomplete scoring**: Only {progress['percent_complete']:.1f}% of cells are scored. "
            "Consider completing all scores before exporting."
        )

    if not progress["weights_locked"]:
        st.info(
            "💡 **Weights not locked**: Consider locking weights on the Weights Review page "
            "to indicate final consensus."
        )

    # Export options
    st.divider()
    st.subheader("📤 Export Options")

    # Include rationales checkbox
    include_rationales = st.checkbox(
        "Include rationales in PDF",
        value=True,
        help="Include detailed rationales for each score in an appendix section",
    )

    # Show rationale summary if checkbox is checked
    if include_rationales:
        if rationale_count == 0:
            st.info("ℹ️ No rationales have been entered. PDF will include an empty rationale section.")
        else:
            st.success(
                f"✅ {rationale_count} rationale(s) will be included in the PDF appendix "
                f"({rationale_count / len(scenario.scores) * 100:.1f}% of scores)"
            )

    # Export button
    st.divider()

    col1, col2 = st.columns([2, 1])

    with col1:
        export_button = st.button(
            "📄 Export to PDF",
            type="primary",
            use_container_width=True,
            help="Generate PDF report (Full implementation in M4)",
        )

    if export_button:
        # Check if scenario has scores
        if not scenario.scores:
            st.error("⚠️ Cannot export: No scores have been entered yet.")
            return

        try:
            # Generate file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{scenario.id}_{timestamp}.pdf"

            # Use storage path
            storage_path = StoragePaths.get_default_storage_path()
            exports_dir = Path(storage_path) / "exports"
            exports_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(exports_dir / filename)

            # Create export service and generate PDF
            with st.spinner("Generating PDF report..."):
                export_service = ExportService()
                result_path = export_service.build_pdf(
                    scenario,
                    output_path,
                    include_rationales=include_rationales
                )

            # Show success message
            st.success(
                f"✅ **Export complete!**\n\n"
                f"PDF report saved to:\n"
                f"`{result_path}`"
            )

            # Show file size
            file_size = Path(result_path).stat().st_size / 1024  # KB
            st.info(f"📄 File size: {file_size:.1f} KB")

            # Show what's included
            with st.expander("📋 What's included in the PDF"):
                st.markdown(
                    f"""
                    **Cover Page**
                    - Scenario title: {scenario.title}
                    - Date generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
                    - Weights locked: {"Yes" if progress["weights_locked"] else "No"}

                    **Leaderboard**
                    - Ranked options with scores
                    - Winner highlight

                    **Contributions Analysis**
                    - Criterion breakdown
                    - Winner vs runner-up comparison

                    **Delta to Winner**
                    - Gap analysis for all options

                    **Rationale Appendix** {"(Included)" if include_rationales else "(Excluded)"}
                    {f"- {rationale_count} rationales" if include_rationales and rationale_count > 0 else ""}

                    **Metadata Footer**
                    - Scenario ID: {scenario.id}
                    - Export timestamp
                    - App version
                    """
                )

        except Exception as e:
            st.error(f"⚠️ **Export failed**: {str(e)}")
            st.exception(e)

    # Navigation
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back to Review & Analysis", use_container_width=True):
            st.session_state.current_page = "review_analysis"
            st.rerun()

    with col2:
        if st.button("🏁 Back to Setup", use_container_width=True):
            st.session_state.current_page = "setup"
            st.rerun()
