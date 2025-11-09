"""Score editing modal component."""
import streamlit as st
from typing import Callable, Optional, Dict, Tuple
from src.domain.models import Criterion, Option, Score


@st.dialog("Edit Score")
def show_edit_score_modal(
    criterion: Criterion,
    option: Option,
    current_score: Optional[Score],
    on_save: Callable[[int, Optional[str]], None],
    full_criteria_map: Optional[Dict[str, Tuple[str, str]]] = None,
) -> None:
    """
    Show a modal dialog for editing a score and rationale.

    Args:
        criterion: The criterion being scored
        option: The option being scored
        current_score: Current score object or None if not yet scored
        on_save: Callback function called with (raw_score, rationale)
        full_criteria_map: Optional dict mapping criterion ID to (high_anchor, low_anchor)
    """
    # Option name first - darker, smaller font, above criterion
    st.markdown(
        f'<p style="color: #1f1f1f; font-size: 0.875rem; font-weight: 600; margin-bottom: 0.25rem;">'
        f'Scoring for: {option.name}</p>',
        unsafe_allow_html=True
    )

    # Criterion name - large heading
    st.markdown(f"### {criterion.name}")

    # Score selector with large buttons and anchors underneath
    st.markdown("**Select Score:**")

    # Determine which anchor text to use
    if full_criteria_map and criterion.id in full_criteria_map:
        high_anchor, low_anchor = full_criteria_map[criterion.id]
    else:
        # Fallback to short anchors
        high_anchor = criterion.anchors.hi
        low_anchor = criterion.anchors.lo

    # Create 5 columns for score buttons
    cols = st.columns(5)

    # Get current raw score value
    current_raw = current_score.raw if current_score else None

    # Use session state to track the selected score in the modal
    modal_score_key = f"modal_score_{option.id}_{criterion.id}"
    if modal_score_key not in st.session_state:
        st.session_state[modal_score_key] = current_raw

    selected_score = st.session_state[modal_score_key]

    for i, col in enumerate(cols, start=1):
        with col:
            is_selected = (selected_score == i)
            button_type = "primary" if is_selected else "secondary"

            if st.button(
                str(i),
                key=f"modal_btn_{option.id}_{criterion.id}_{i}",
                type=button_type,
                use_container_width=True,
            ):
                st.session_state[modal_score_key] = i
                st.rerun()

            # Show anchor text under buttons 1 and 5
            if i == 1:
                st.markdown(
                    f'<div style="font-size: 0.75rem; color: #666; margin-top: 0.25rem; line-height: 1.2;">'
                    f'🔴 {low_anchor}</div>',
                    unsafe_allow_html=True
                )
            elif i == 5:
                st.markdown(
                    f'<div style="font-size: 0.75rem; color: #666; margin-top: 0.25rem; line-height: 1.2;">'
                    f'🔵 {high_anchor}</div>',
                    unsafe_allow_html=True
                )

    st.markdown("")  # Spacing

    # Rationale editor
    st.markdown("**Rationale (optional):**")
    current_rationale = current_score.rationale if current_score else ""

    rationale_text = st.text_area(
        "Rationale",
        value=current_rationale or "",
        max_chars=500,
        height=100,
        key=f"modal_rationale_{option.id}_{criterion.id}",
        help="Add context or justification for this score (max 500 characters)",
        label_visibility="collapsed",
    )

    # Show character count
    char_count = len(rationale_text)
    st.caption(f"{char_count}/500 characters")

    # Buttons
    st.markdown("")  # Spacing
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Cancel", use_container_width=True, key=f"modal_cancel_{option.id}_{criterion.id}"):
            # Clear all modal state keys
            if modal_score_key in st.session_state:
                del st.session_state[modal_score_key]
            if "edit_score_option_id" in st.session_state:
                del st.session_state.edit_score_option_id
            if "edit_score_criterion_id" in st.session_state:
                del st.session_state.edit_score_criterion_id
            st.rerun()

    with col2:
        # Disable save if no score is selected
        save_disabled = selected_score is None

        if st.button(
            "Save",
            type="primary",
            use_container_width=True,
            disabled=save_disabled,
            key=f"modal_save_{option.id}_{criterion.id}",
        ):
            if selected_score is not None:
                # Call the save callback
                final_rationale = rationale_text if rationale_text.strip() else None
                on_save(selected_score, final_rationale)

                # Clear all modal state keys
                if modal_score_key in st.session_state:
                    del st.session_state[modal_score_key]
                if "edit_score_option_id" in st.session_state:
                    del st.session_state.edit_score_option_id
                if "edit_score_criterion_id" in st.session_state:
                    del st.session_state.edit_score_criterion_id

                st.rerun()

    if save_disabled:
        st.warning("⚠️ Please select a score before saving.")
