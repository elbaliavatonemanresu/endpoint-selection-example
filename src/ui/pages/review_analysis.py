"""Review & Analysis Page."""
import streamlit as st
import pandas as pd

from src.ui.components.charts import (
    create_leaderboard_chart,
    create_contributions_chart,
    create_delta_chart,
)


def render():
    """Render the review and analysis page."""
    st.title("📈 Review & Analysis")

    if not st.session_state.scenario:
        st.warning("⚠️ No scenario loaded. Please go to Setup to create or load a scenario.")
        return

    scenario = st.session_state.scenario
    analysis_service = st.session_state.analysis_service

    # Check if there are any scores
    if not scenario.scores:
        st.warning("⚠️ No scores entered yet. Please complete scoring before viewing analysis.")
        if st.button("← Go to Overview"):
            st.session_state.current_page = "overview"
            st.rerun()
        return

    st.markdown("Analyze your scoring results with leaderboards, contributions, and sensitivity analysis.")

    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Leaderboard", "🔍 Contributions", "📉 Delta to Winner", "🔬 Sensitivity Analysis"]
    )

    with tab1:
        render_leaderboard(scenario, analysis_service)

    with tab2:
        render_contributions(scenario, analysis_service)

    with tab3:
        render_delta_to_winner(scenario, analysis_service)

    with tab4:
        render_sensitivity(scenario, analysis_service)

    st.divider()

    # Navigation
    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back to Overview", use_container_width=True):
            st.session_state.current_page = "overview"
            st.rerun()

    with col2:
        if st.button("Export to PDF →", type="primary", use_container_width=True):
            st.session_state.current_page = "finalize_export"
            st.rerun()


def render_leaderboard(scenario, analysis_service):
    """Render the leaderboard."""
    st.subheader("📊 Leaderboard")
    st.caption("Options ranked by total weighted score")

    leaderboard = analysis_service.leaderboard(scenario)

    # Display chart
    try:
        chart = create_leaderboard_chart(leaderboard)
        st.altair_chart(chart, use_container_width=True)
    except Exception as e:
        st.warning(f"Unable to render chart: {str(e)}")

    st.divider()

    # Build display data for table
    lb_data = []
    for entry in leaderboard:
        lb_data.append(
            {
                "Rank": entry["rank"],
                "Option": entry["name"],
                "Total Score": entry["total"],
                "Normalized (0-100)": f"{entry['normalized']:.1f}%",
            }
        )

    df = pd.DataFrame(lb_data)

    # Highlight winner
    def highlight_winner(row):
        if row["Rank"] == 1:
            return ["background-color: #d4edda"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df.style.apply(highlight_winner, axis=1), hide_index=True, use_container_width=True
    )

    # Winner summary
    winner = leaderboard[0]
    st.success(f"🏆 **Winner:** {winner['name']} with {winner['total']} points ({winner['normalized']:.1f}%)")


def render_contributions(scenario, analysis_service):
    """Render criterion contributions analysis."""
    st.subheader("🔍 Contributions Analysis")
    st.caption("Criterion-by-criterion breakdown for selected options")

    # Get leaderboard to identify winner and runner-up
    leaderboard = analysis_service.leaderboard(scenario)

    # Default to top 2
    default_options = [leaderboard[0]["optionId"], leaderboard[1]["optionId"]] if len(leaderboard) >= 2 else [leaderboard[0]["optionId"]]

    # Option selector
    option_names = {opt.id: opt.name for opt in scenario.options}
    selected_options = st.multiselect(
        "Select options to compare",
        options=[opt.id for opt in scenario.options],
        default=default_options,
        format_func=lambda x: option_names[x],
        max_selections=3,
    )

    if not selected_options:
        st.info("Select at least one option to view contributions")
        return

    # Get contributions
    contributions = analysis_service.contributions(scenario, selected_options)

    # Display chart
    try:
        chart = create_contributions_chart(contributions, selected_options)
        st.altair_chart(chart, use_container_width=True)
    except Exception as e:
        st.warning(f"Unable to render chart: {str(e)}")

    st.divider()

    # Build comparison table
    comp_data = []
    for criterion_id, criterion_info in contributions["criteria"].items():
        row = {
            "Criterion": criterion_info["name"],
            "Weight": criterion_info["weight"],
        }

        for opt_id in selected_options:
            opt_contrib = contributions[opt_id].get(criterion_id, 0)
            row[option_names[opt_id]] = opt_contrib

        comp_data.append(row)

    # Add totals row
    total_row = {"Criterion": "**TOTAL**", "Weight": "—"}
    for opt_id in selected_options:
        total_row[option_names[opt_id]] = contributions[opt_id]["total"]
    comp_data.append(total_row)

    df = pd.DataFrame(comp_data)
    st.dataframe(df, hide_index=True, use_container_width=True)


def render_delta_to_winner(scenario, analysis_service):
    """Render delta to winner analysis."""
    st.subheader("📉 Delta to Winner")
    st.caption("Gap between each option and the winning option")

    deltas = analysis_service.delta_to_winner(scenario)

    winner_id = deltas["winner"]
    winner_name = next(opt.name for opt in scenario.options if opt.id == winner_id)

    st.info(f"🏆 Winner: **{winner_name}**")

    # Display chart
    try:
        chart = create_delta_chart(deltas)
        st.altair_chart(chart, use_container_width=True)
    except Exception as e:
        st.warning(f"Unable to render chart: {str(e)}")

    st.divider()

    # Build delta table
    delta_data = []
    for option in scenario.options:
        delta_info = deltas[option.id]
        delta_data.append(
            {
                "Option": option.name,
                "Total Score": delta_info["total"],
                "Gap to Winner": delta_info["delta"],
                "Status": "🏆 Winner" if option.id == winner_id else f"△ {delta_info['delta']} behind",
            }
        )

    # Sort by delta (smallest first = winner first)
    df = pd.DataFrame(delta_data).sort_values("Gap to Winner")

    st.dataframe(df, hide_index=True, use_container_width=True)

    # Show largest gap
    if len(delta_data) > 1:
        max_delta = max(d["Gap to Winner"] for d in delta_data)
        st.metric("Largest Gap", f"{max_delta} points")


def render_sensitivity(scenario, analysis_service):
    """Render sensitivity analysis."""
    st.subheader("🔬 Sensitivity Analysis")
    st.caption("What-if analysis: See how changing a criterion weight affects the leaderboard")

    st.markdown(
        "Sensitivity analysis shows how the rankings would change if you "
        "adjusted a criterion's weight."
    )

    # Criterion selector
    criterion_options = {c.id: f"{c.name} (current weight: {c.weight})" for c in scenario.criteria}
    selected_criterion = st.selectbox(
        "Select criterion to adjust",
        options=list(criterion_options.keys()),
        format_func=lambda x: criterion_options[x],
    )

    # Percentage adjustment
    pct_change = st.slider(
        "Percentage change",
        min_value=-100,
        max_value=200,
        value=0,
        step=10,
        help="Positive = increase weight, Negative = decrease weight",
    )

    if pct_change == 0:
        st.info("💡 Adjust the percentage slider to see how rankings would change")
        return

    # Run sensitivity analysis
    try:
        sensitivity = analysis_service.sensitivity(scenario, selected_criterion, pct_change)

        # Show original vs adjusted
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Original Leaderboard**")
            orig_data = []
            for entry in sensitivity["original"]:
                orig_data.append(
                    {
                        "Rank": entry["rank"],
                        "Option": entry["name"],
                        "Score": entry["total"],
                    }
                )
            st.dataframe(pd.DataFrame(orig_data), hide_index=True)

        with col2:
            st.markdown(f"**Adjusted Leaderboard** ({pct_change:+}%)")
            adj_data = []
            for entry in sensitivity["adjusted"]:
                adj_data.append(
                    {
                        "Rank": entry["rank"],
                        "Option": entry["name"],
                        "Score": f"{entry['total']:.1f}",
                    }
                )
            st.dataframe(pd.DataFrame(adj_data), hide_index=True)

        # Check for rank changes
        orig_winner = sensitivity["original"][0]["optionId"]
        adj_winner = sensitivity["adjusted"][0]["optionId"]

        if orig_winner != adj_winner:
            orig_winner_name = next(opt.name for opt in scenario.options if opt.id == orig_winner)
            adj_winner_name = next(opt.name for opt in scenario.options if opt.id == adj_winner)
            st.warning(
                f"⚠️ **Winner changes!** {orig_winner_name} → {adj_winner_name}"
            )
        else:
            st.success("✅ Winner remains the same")

    except Exception as e:
        st.error(f"⚠️ Error running sensitivity analysis: {str(e)}")
