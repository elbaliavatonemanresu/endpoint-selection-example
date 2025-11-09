"""Unified scoring table component showing all factors, weights, and scores."""
import streamlit as st
from typing import Dict, Any
from src.domain.models import Scenario, Criterion, Option, Score
from src.ui.components.edit_weight_modal import show_edit_weight_modal
from src.ui.components.edit_score_modal import show_edit_score_modal
from src.utils.criteria_loader import load_full_criteria_descriptions


def render_unified_scoring_table(
    scenario: Scenario,
    on_weight_change: callable,
    on_score_change: callable,
    discussion_mode: bool = True,
) -> None:
    """
    Render the unified scoring table with all factors, weights, and scores.

    Args:
        scenario: The current scenario
        on_weight_change: Callback(criterion_id, new_weight) for weight changes
        on_score_change: Callback(option_id, criterion_id, raw, rationale) for score changes
        discussion_mode: If True, use modals for editing; if False, use direct keyboard input
    """
    # Load full criteria descriptions from CSV for enhanced tooltips
    # Maps criterion ID to (high_anchor, low_anchor) tuple
    full_criteria_map = load_full_criteria_descriptions(scenario.criteria)

    # Check if we should open a modal (only in discussion mode)
    # Note: The modals themselves will clear these keys when closed
    if discussion_mode:
        if "edit_weight_criterion_id" in st.session_state:
            criterion_id = st.session_state.edit_weight_criterion_id
            criterion = next((c for c in scenario.criteria if c.id == criterion_id), None)
            if criterion:
                show_edit_weight_modal(
                    criterion=criterion,
                    on_save=lambda new_weight: on_weight_change(criterion_id, new_weight),
                )

        if "edit_score_option_id" in st.session_state and "edit_score_criterion_id" in st.session_state:
            option_id = st.session_state.edit_score_option_id
            criterion_id = st.session_state.edit_score_criterion_id

            option = next((o for o in scenario.options if o.id == option_id), None)
            criterion = next((c for c in scenario.criteria if c.id == criterion_id), None)

            if option and criterion:
                # Find current score
                current_score = next(
                    (s for s in scenario.scores if s.optionId == option_id and s.criterionId == criterion_id),
                    None
                )

                show_edit_score_modal(
                    criterion=criterion,
                    option=option,
                    current_score=current_score,
                    on_save=lambda raw, rationale: on_score_change(option_id, criterion_id, raw, rationale),
                    full_criteria_map=full_criteria_map,
                )

    # Build a score lookup map for quick access
    score_map = {}
    for score in scenario.scores:
        key = (score.optionId, score.criterionId)
        score_map[key] = score

    # Calculate weighted totals for each option
    totals = {}
    for option in scenario.options:
        total = 0
        for criterion in scenario.criteria:
            score = score_map.get((option.id, criterion.id))
            if score:
                total += score.raw * criterion.weight
        totals[option.id] = total

    # Calculate max possible score for normalization
    max_possible = sum(c.weight * 5 for c in scenario.criteria)

    # Create the table using custom HTML/CSS for better control
    # We'll use Streamlit columns to create a table-like layout

    # Add custom CSS for better table styling
    st.markdown("""
        <style>
        /* Compact button styling for table cells */
        .stButton button {
            font-size: 14px;
            padding: 0.3rem 0.6rem;
            min-height: 2rem;
        }

        /* Improve table layout */
        div[data-testid="column"] {
            padding: 0.2rem;
        }

        /* Better visual hierarchy */
        .stMarkdown h3 {
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Create container for the table with horizontal scroll
    with st.container():
        # Table header row
        header_cols = st.columns([3, 1] + [1] * len(scenario.options))

        with header_cols[0]:
            st.markdown("**Factor**")
        with header_cols[1]:
            st.markdown("**Weight**")
        for i, option in enumerate(scenario.options):
            with header_cols[i + 2]:
                st.markdown(f"**{option.name}**")

        st.markdown("---")

        # Data rows - one per criterion
        for criterion in scenario.criteria:
            row_cols = st.columns([3, 1] + [1] * len(scenario.options))

            # Factor name column with tooltip
            with row_cols[0]:
                # Get full descriptions if available, otherwise use short anchors
                full_anchors = full_criteria_map.get(criterion.id)
                if full_anchors:
                    high_text, low_text = full_anchors
                    tooltip_text = f"🔵 High (5): {high_text}\n\n🔴 Low (1): {low_text}"
                else:
                    # Fallback to short anchors from criterion object
                    tooltip_text = f"🔵 High (5): {criterion.anchors.hi}\n\n🔴 Low (1): {criterion.anchors.lo}"

                # Show criterion name with enhanced tooltip
                st.markdown(
                    f"{criterion.name}",
                    help=tooltip_text
                )

            # Weight column
            with row_cols[1]:
                weight_disabled = scenario.weightsLocked

                if discussion_mode:
                    # Discussion mode: Button that opens modal
                    button_label = f"{criterion.weight}"

                    if st.button(
                        button_label,
                        key=f"weight_{criterion.id}",
                        disabled=weight_disabled,
                        use_container_width=True,
                        help="Click to edit weight" if not weight_disabled else "Weights are locked",
                    ):
                        # Set state to open weight edit modal
                        st.session_state.edit_weight_criterion_id = criterion.id
                        st.rerun()
                else:
                    # Quick mode: Text input for keyboard entry only
                    weight_str = st.text_input(
                        "Weight",
                        value=str(criterion.weight),
                        key=f"weight_input_{criterion.id}",
                        disabled=weight_disabled,
                        label_visibility="collapsed",
                        placeholder="0+",
                        help="Enter weight (0 or higher)" if not weight_disabled else "Weights are locked",
                    )

                    # Validate and auto-save on change
                    if not weight_disabled and weight_str.strip():
                        try:
                            new_weight = int(weight_str)
                            if new_weight >= 0 and new_weight != criterion.weight:
                                on_weight_change(criterion.id, new_weight)
                        except ValueError:
                            pass  # Invalid input, ignore

            # Score columns - one per option
            for i, option in enumerate(scenario.options):
                with row_cols[i + 2]:
                    score = score_map.get((option.id, criterion.id))
                    current_score_value = score.raw if score else None
                    current_rationale = score.rationale if score else None

                    if discussion_mode:
                        # Discussion mode: Button that opens modal
                        if score:
                            # Show score with rationale indicator
                            has_rationale = current_rationale and len(current_rationale.strip()) > 0
                            button_label = f"{current_score_value}" + (" 💬" if has_rationale else "")
                            help_text = f"Score: {current_score_value}/5"
                            if has_rationale:
                                preview = current_rationale[:50] + "..." if len(current_rationale) > 50 else current_rationale
                                help_text += f"\nRationale: {preview}"
                        else:
                            # Empty cell
                            button_label = "—"
                            help_text = "Click to add score"

                        if st.button(
                            button_label,
                            key=f"score_{option.id}_{criterion.id}",
                            use_container_width=True,
                            help=help_text,
                        ):
                            # Set state to open score edit modal
                            st.session_state.edit_score_option_id = option.id
                            st.session_state.edit_score_criterion_id = criterion.id
                            st.rerun()
                    else:
                        # Quick mode: Text input for keyboard entry only
                        # Note: Preserve existing rationale even in quick mode
                        score_str = st.text_input(
                            "Score",
                            value=str(current_score_value) if current_score_value else "",
                            key=f"score_input_{option.id}_{criterion.id}",
                            label_visibility="collapsed",
                            placeholder="1-5",
                            help=f"Enter score 1-5 for {option.name}",
                        )

                        # Validate and auto-save on change
                        if score_str.strip():
                            try:
                                new_score = int(score_str)
                                if 1 <= new_score <= 5 and new_score != current_score_value:
                                    # Preserve existing rationale when updating in quick mode
                                    on_score_change(option.id, criterion.id, new_score, current_rationale)
                            except ValueError:
                                pass  # Invalid input, ignore

        # Totals row
        st.markdown("---")
        totals_cols = st.columns([3, 1] + [1] * len(scenario.options))

        with totals_cols[0]:
            st.markdown("**WEIGHTED TOTAL**")
        with totals_cols[1]:
            st.markdown("")  # Empty cell

        for i, option in enumerate(scenario.options):
            with totals_cols[i + 2]:
                total = totals.get(option.id, 0)
                # Check if option has any scores
                has_scores = any(s.optionId == option.id for s in scenario.scores)
                if has_scores:
                    st.markdown(f"**{total:.1f}**")
                else:
                    st.markdown("**—**")

    # Show legend
    if discussion_mode:
        st.caption("💡 Click any weight or score cell to edit | 💬 = has rationale")
    else:
        st.caption("💡 Type numbers directly into cells to edit | Rationale preserved | Toggle Discussion Mode to add/edit rationales")
