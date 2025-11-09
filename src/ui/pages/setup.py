"""Setup Page - Create or load scenarios."""
import streamlit as st


def render():
    """Render the setup page."""
    st.title("🏁 Setup")
    st.markdown("Create a new scenario or load an existing one.")

    # Check if we need to show confirmation dialogs
    if st.session_state.get("show_switch_confirmation"):
        render_switch_confirmation()
        return

    tab1, tab2 = st.tabs(["Create New Scenario", "Load Existing Scenario"])

    with tab1:
        render_create_scenario()

    with tab2:
        render_load_scenario()


def check_existing_work():
    """
    Check if switching scenarios will lose work.
    Returns True if should proceed, False if need confirmation.
    """
    current_scenario = st.session_state.get("scenario")

    # No scenario loaded, proceed
    if not current_scenario:
        return True

    # No scores yet, proceed
    if len(current_scenario.scores) == 0:
        return True

    # Has work in progress, need confirmation
    return False


def render_switch_confirmation():
    """Render confirmation dialog for switching scenarios."""
    current_scenario = st.session_state.scenario
    pending_action = st.session_state.get("pending_action")

    # Calculate progress
    total_cells = len(current_scenario.criteria) * len(current_scenario.options)
    scored = len(current_scenario.scores)
    pct = (scored / total_cells * 100) if total_cells > 0 else 0

    st.warning(
        f"""
### ⚠️ Switch Scenario?

You have work in progress:
- **Current scenario:** {current_scenario.title}
- **Progress:** {scored} of {total_cells} cells scored ({pct:.0f}%)

Your current work is **automatically saved**. You can reload this scenario later from the "Load Existing Scenario" tab.
        """.strip()
    )

    st.markdown("")  # Spacing

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Cancel", use_container_width=True, key="cancel_switch"):
            # Clear confirmation flags
            st.session_state.show_switch_confirmation = False
            if "pending_action" in st.session_state:
                del st.session_state.pending_action
            st.rerun()

    with col2:
        if st.button("Switch Scenario", type="primary", use_container_width=True, key="confirm_switch"):
            # Execute the pending action
            if pending_action:
                if pending_action["type"] == "create":
                    execute_create_scenario(
                        pending_action["title"],
                        pending_action["options"]
                    )
                elif pending_action["type"] == "load":
                    execute_load_scenario(pending_action["scenario_id"])

            # Clear confirmation flags
            st.session_state.show_switch_confirmation = False
            if "pending_action" in st.session_state:
                del st.session_state.pending_action


def render_create_scenario():
    """Render the create new scenario form."""
    st.subheader("Create New Scenario")

    with st.form("create_scenario_form"):
        title = st.text_input(
            "Scenario Title",
            placeholder="e.g., Endpoint Selection for Phase 3 Trial",
            help="Enter a descriptive title for your scenario",
        )

        st.markdown("**Options to Evaluate**")
        st.caption("Enter one option per line (e.g., different endpoints, interventions, or alternatives)")

        options_text = st.text_area(
            "Options",
            placeholder="Option 1\nOption 2\nOption 3",
            height=150,
            label_visibility="collapsed",
        )

        submit = st.form_submit_button("Create Scenario", type="primary", use_container_width=True)

        if submit:
            # Validate inputs
            if not title or not title.strip():
                st.error("⚠️ Please enter a scenario title")
                return

            # Parse options
            options = [opt.strip() for opt in options_text.split("\n") if opt.strip()]

            if len(options) < 2:
                st.error("⚠️ Please enter at least 2 options (one per line)")
                return

            # Check if we need confirmation before switching
            if check_existing_work():
                # No work to lose, create immediately
                execute_create_scenario(title.strip(), options)
            else:
                # Show confirmation dialog
                st.session_state.show_switch_confirmation = True
                st.session_state.pending_action = {
                    "type": "create",
                    "title": title.strip(),
                    "options": options
                }
                st.rerun()


def execute_create_scenario(title: str, options: list):
    """Execute scenario creation after confirmation (if needed)."""
    try:
        scenario = st.session_state.scenario_service.create(
            title=title,
            options=options,
        )

        st.session_state.scenario = scenario
        st.success(f"✅ Scenario '{title}' created successfully!")
        st.info(f"Loaded {len(scenario.criteria)} criteria and {len(scenario.options)} options")

        # Auto-navigate to unified scoring
        st.session_state.current_page = "unified_scoring"
        st.rerun()

    except Exception as e:
        st.error(f"⚠️ Error creating scenario: {str(e)}")


def render_load_scenario():
    """Render the load existing scenario interface."""
    st.subheader("Load Existing Scenario")

    # List existing scenarios
    scenarios = st.session_state.scenario_service.list_scenarios()

    if not scenarios:
        st.info("No saved scenarios found. Create a new scenario to get started.")
        return

    st.markdown(f"**{len(scenarios)} scenarios available**")

    # Display scenarios as cards
    for idx, scenario_meta in enumerate(scenarios):
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{scenario_meta['title']}**")
                st.caption(
                    f"ID: {scenario_meta['id']} | "
                    f"Modified: {scenario_meta.get('modified', 'Unknown')}"
                )

            with col2:
                if st.button("Load", key=f"load_{idx}", use_container_width=True):
                    # Check if we need confirmation before switching
                    if check_existing_work():
                        # No work to lose, load immediately
                        execute_load_scenario(scenario_meta["id"])
                    else:
                        # Show confirmation dialog
                        st.session_state.show_switch_confirmation = True
                        st.session_state.pending_action = {
                            "type": "load",
                            "scenario_id": scenario_meta["id"]
                        }
                        st.rerun()

            st.divider()


def execute_load_scenario(scenario_id: str):
    """Execute scenario loading after confirmation (if needed)."""
    try:
        scenario = st.session_state.scenario_service.open(scenario_id)
        st.session_state.scenario = scenario
        st.success(f"✅ Loaded scenario: {scenario.title}")
        st.session_state.current_page = "unified_scoring"
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Error loading scenario: {str(e)}")
