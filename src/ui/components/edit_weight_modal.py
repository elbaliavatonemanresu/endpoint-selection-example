"""Weight editing modal component."""
import streamlit as st
from typing import Callable, Optional
from src.domain.models import Criterion


@st.dialog("Edit Weight")
def show_edit_weight_modal(
    criterion: Criterion,
    on_save: Callable[[int], None],
) -> None:
    """
    Show a modal dialog for editing a criterion weight.

    Args:
        criterion: The criterion whose weight is being edited
        on_save: Callback function called with the new weight value
    """
    st.markdown(f"### {criterion.name}")
    st.caption(f"Current weight: **{criterion.weight}**")

    # Number input for new weight
    new_weight = st.number_input(
        "New weight",
        min_value=0,
        value=criterion.weight,
        step=1,
        help="Weight must be 0 or greater",
    )

    # Show explanation
    st.info("Higher weights give this criterion more influence on the final scores.")

    # Buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Cancel", use_container_width=True):
            # Clear the modal trigger key
            if "edit_weight_criterion_id" in st.session_state:
                del st.session_state.edit_weight_criterion_id
            st.rerun()

    with col2:
        if st.button("Save", type="primary", use_container_width=True):
            if new_weight != criterion.weight:
                on_save(new_weight)
            # Clear the modal trigger key
            if "edit_weight_criterion_id" in st.session_state:
                del st.session_state.edit_weight_criterion_id
            st.rerun()
