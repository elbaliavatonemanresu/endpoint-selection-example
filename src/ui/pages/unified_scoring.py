"""Unified Scoring Page - Edit all weights and scores in one table."""
import streamlit as st
from src.ui.components.unified_scoring_table import render_unified_scoring_table
from src.services.scenario_service import ScenarioService


def render():
    """Render the unified scoring page."""
    st.title("🎯 Scoring & Weights")

    # Check if scenario is loaded
    if not st.session_state.scenario:
        st.warning("⚠️ No scenario loaded. Please go to Setup to create or load a scenario.")
        return

    scenario = st.session_state.scenario
    weights_service = st.session_state.weights_service
    scoring_service = st.session_state.scoring_service
    scenario_service = st.session_state.scenario_service

    # Show scenario title
    st.markdown(f"**Scenario:** {scenario.title}")

    # Lock/Unlock weights button
    col1, col2, col3 = st.columns([2, 2, 6])

    with col1:
        if scenario.weightsLocked:
            if st.button("🔓 Unlock Weights", use_container_width=True):
                # Show dialog to get reason
                st.session_state.show_unlock_dialog = True
        else:
            if st.button("🔒 Lock Weights", use_container_width=True):
                try:
                    updated = weights_service.lock_weights(scenario, actor="user")
                    st.session_state.scenario = updated
                    scenario_service.save(updated)
                    st.success("✓ Weights locked", icon="🔒")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error locking weights: {str(e)}")

    with col2:
        if scenario.weightsLocked:
            st.caption("🔒 Locked")
        else:
            st.caption("🔓 Unlocked")

    # Handle unlock dialog
    if st.session_state.get("show_unlock_dialog", False):
        with st.form("unlock_weights_form"):
            st.markdown("### Unlock Weights")
            reason = st.text_input(
                "Reason for unlocking",
                placeholder="e.g., Need to adjust weights based on new information",
                help="Brief explanation for audit trail (required)",
            )

            col_cancel, col_unlock = st.columns(2)

            with col_cancel:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_unlock_dialog = False
                    st.rerun()

            with col_unlock:
                if st.form_submit_button("Unlock", type="primary", use_container_width=True):
                    if not reason.strip():
                        st.error("⚠️ Reason is required")
                    else:
                        try:
                            updated = weights_service.unlock_weights(scenario, actor="user", reason=reason)
                            st.session_state.scenario = updated
                            scenario_service.save(updated)
                            st.session_state.show_unlock_dialog = False
                            st.success("✓ Weights unlocked", icon="🔓")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error unlocking weights: {str(e)}")

    st.divider()

    # Discussion Mode toggle
    col_toggle1, col_toggle2 = st.columns([3, 7])

    with col_toggle1:
        # Initialize discussion_mode if not set
        if "discussion_mode" not in st.session_state:
            st.session_state.discussion_mode = True

        discussion_mode = st.toggle(
            "💬 Discussion Mode",
            value=st.session_state.discussion_mode,
            help="ON: Click cells to open modal with anchors & rationale | OFF: Quick keyboard entry (scores only)",
            key="discussion_mode_toggle"
        )

        # Update session state
        st.session_state.discussion_mode = discussion_mode

    with col_toggle2:
        if discussion_mode:
            st.caption("✓ Modals enabled for anchors & rationale")
        else:
            st.caption("⚡ Quick entry mode (keyboard input, no rationale)")

    st.markdown("")  # Spacing

    # Calculate and show progress with visual bar
    total_cells = len(scenario.criteria) * len(scenario.options)
    scored_cells = len(scenario.scores)
    progress_pct = (scored_cells / total_cells * 100) if total_cells > 0 else 0

    # Show progress bar and metrics
    col_prog1, col_prog2 = st.columns([3, 1])

    with col_prog1:
        st.progress(progress_pct / 100)

    with col_prog2:
        st.metric("Completion", f"{progress_pct:.0f}%")

    st.caption(f"{scored_cells} of {total_cells} cells scored")

    # Render the unified scoring table
    render_unified_scoring_table(
        scenario=scenario,
        on_weight_change=handle_weight_change,
        on_score_change=handle_score_change,
        discussion_mode=discussion_mode,
    )


def handle_weight_change(criterion_id: str, new_weight: int):
    """
    Handle weight change callback from the table.

    Args:
        criterion_id: ID of the criterion being updated
        new_weight: New weight value
    """
    scenario = st.session_state.scenario
    weights_service = st.session_state.weights_service
    scenario_service = st.session_state.scenario_service

    try:
        # Update weight with a default reason
        updated = weights_service.set_weight(
            scenario,
            criterion_id=criterion_id,
            weight=new_weight,
            actor="user",
            reason="Updated via unified scoring table",
        )

        # Save and update session state
        st.session_state.scenario = updated
        scenario_service.save(updated)

    except Exception as e:
        # Store error for display after rerun
        st.session_state.update_error = f"Error updating weight: {str(e)}"


def handle_score_change(option_id: str, criterion_id: str, raw: int, rationale: str | None):
    """
    Handle score change callback from the table.

    Args:
        option_id: ID of the option being scored
        criterion_id: ID of the criterion being scored
        raw: Raw score value (1-5)
        rationale: Optional rationale text
    """
    scenario = st.session_state.scenario
    scoring_service = st.session_state.scoring_service
    scenario_service = st.session_state.scenario_service

    try:
        # Update score
        updated = scoring_service.set_score(
            scenario,
            option_id=option_id,
            criterion_id=criterion_id,
            raw=raw,
            actor="user",
            rationale=rationale,
        )

        # Save and update session state
        st.session_state.scenario = updated
        scenario_service.save(updated)

    except Exception as e:
        # Store error for display after rerun
        st.session_state.update_error = f"Error updating score: {str(e)}"
