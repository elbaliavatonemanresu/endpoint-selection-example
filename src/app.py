"""CTTI Endpoint Selection Facilitator - Main Application Entry Point."""
import streamlit as st
from pathlib import Path

from src.ui.theme.tokens_loader import TokensLoader
from src.services.scenario_service import ScenarioService
from src.services.scoring_service import ScoringService
from src.services.weights_service import WeightsService
from src.services.analysis_service import AnalysisService
from src.services.export_service import ExportService


def init_session_state():
    """Initialize session state variables."""
    if "scenario" not in st.session_state:
        st.session_state.scenario = None

    if "scenario_service" not in st.session_state:
        st.session_state.scenario_service = ScenarioService()

    if "scoring_service" not in st.session_state:
        st.session_state.scoring_service = ScoringService()

    if "weights_service" not in st.session_state:
        st.session_state.weights_service = WeightsService()

    if "analysis_service" not in st.session_state:
        st.session_state.analysis_service = AnalysisService()

    if "export_service" not in st.session_state:
        st.session_state.export_service = ExportService()

    if "current_page" not in st.session_state:
        st.session_state.current_page = "setup"

    if "actor" not in st.session_state:
        st.session_state.actor = "facilitator"


def apply_theme():
    """Apply CTTI theme using design tokens."""
    tokens = TokensLoader.load()

    # Custom CSS for CTTI branding
    st.markdown(
        f"""
        <style>
        /* Main colors */
        :root {{
            --ctti-primary: {tokens.color.primary};
            --ctti-secondary: {tokens.color.secondary};
            --ctti-accent: {tokens.color.accent};
            --ctti-error: {tokens.color.error};
        }}

        /* Header styling */
        .main-header {{
            background-color: var(--ctti-primary);
            color: white;
            padding: {tokens.space.md};
            border-radius: {tokens.border.radius.md};
            margin-bottom: {tokens.space.lg};
        }}

        /* Card styling */
        .stCard {{
            border: {tokens.border.width} solid {tokens.color.border};
            border-radius: {tokens.border.radius.md};
            padding: {tokens.space.md};
            box-shadow: {tokens.elevation.card};
        }}

        /* Button styling */
        .stButton>button {{
            border-radius: {tokens.border.radius.sm};
            font-family: {tokens.font.family};
        }}

        /* Progress indicator */
        .progress-bar {{
            background-color: var(--ctti-accent);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_page_module(page_name: str):
    """Dynamically import page module."""
    try:
        if page_name == "setup":
            from src.ui.pages import setup
            return setup
        elif page_name == "unified_scoring":
            from src.ui.pages import unified_scoring
            return unified_scoring
        elif page_name == "review_analysis":
            from src.ui.pages import review_analysis
            return review_analysis
        elif page_name == "finalize_export":
            from src.ui.pages import finalize_export
            return finalize_export
    except ImportError:
        return None


def main():
    """Main application entry point."""
    # Configure page
    st.set_page_config(
        page_title="CTTI Endpoint Selection Facilitator",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    init_session_state()

    # Apply theme
    apply_theme()

    # Display header
    st.markdown(
        '<div class="main-header"><h1>CTTI Endpoint Selection Facilitator</h1></div>',
        unsafe_allow_html=True,
    )

    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")

        pages = {
            "setup": "🏁 Setup",
            "unified_scoring": "🎯 Scoring & Weights",
            "review_analysis": "📈 Review & Analysis",
            "finalize_export": "📄 Finalize & Export",
        }

        # Show scenario info if loaded
        if st.session_state.scenario:
            st.info(f"**Scenario:** {st.session_state.scenario.title}")

            # Show progress
            progress = st.session_state.scenario_service.progress(st.session_state.scenario)
            st.progress(progress["percent_complete"] / 100)
            st.caption(
                f"Progress: {progress['scored_cells']}/{progress['total_cells']} cells "
                f"({progress['percent_complete']:.1f}%)"
            )

            if progress["weights_locked"]:
                st.warning("⚠️ Weights Locked")

        st.divider()

        # Navigation buttons
        for page_key, page_label in pages.items():
            if st.button(page_label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()

    # Load and render current page
    page_module = get_page_module(st.session_state.current_page)

    if page_module and hasattr(page_module, "render"):
        page_module.render()
    else:
        st.warning(
            f"Page '{st.session_state.current_page}' is not yet implemented. "
            f"Please select another page from the sidebar."
        )


if __name__ == "__main__":
    main()
