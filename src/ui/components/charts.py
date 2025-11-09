"""Chart components using Altair with CTTI theming."""
import altair as alt
import pandas as pd
from typing import List, Dict, Any

from src.ui.theme.tokens_loader import TokensLoader


def get_ctti_colors() -> Dict[str, str]:
    """Get CTTI color scheme from design tokens."""
    tokens = TokensLoader.load()
    return {
        "primary": tokens.color.primary,
        "secondary": tokens.color.secondary,
        "accent": tokens.color.accent,
        "error": tokens.color.error,
        "text_primary": tokens.color.text.primary,
        "text_secondary": tokens.color.text.secondary,
        "background": tokens.color.background,
        "surface": tokens.color.surface,
    }


def create_leaderboard_chart(leaderboard_data: List[Dict[str, Any]]) -> alt.Chart:
    """
    Create a horizontal bar chart for the leaderboard.

    Args:
        leaderboard_data: List of dicts with keys: name, total, rank, normalized

    Returns:
        Altair Chart object
    """
    if not leaderboard_data:
        # Return empty chart
        return alt.Chart(pd.DataFrame()).mark_bar()

    colors = get_ctti_colors()

    # Convert to DataFrame
    df = pd.DataFrame(leaderboard_data)

    # Sort by total descending (highest first)
    df = df.sort_values("total", ascending=False).reset_index(drop=True)

    # Calculate delta to runner-up for labels
    if len(df) >= 2:
        runner_up_score = df.iloc[1]["total"]
        df["delta_label"] = df["total"].apply(
            lambda x: f"+{x - runner_up_score}" if x > runner_up_score else ""
        )
    else:
        df["delta_label"] = ""

    # Create horizontal bar chart
    chart = (
        alt.Chart(df)
        .mark_bar(color=colors["primary"])
        .encode(
            x=alt.X("total:Q", title="Total Score", scale=alt.Scale(domain=[0, df["total"].max() * 1.1])),
            y=alt.Y("name:N", title="Option", sort="-x"),
            tooltip=[
                alt.Tooltip("name:N", title="Option"),
                alt.Tooltip("total:Q", title="Total Score"),
                alt.Tooltip("rank:Q", title="Rank"),
                alt.Tooltip("normalized:Q", title="Normalized (%)", format=".1f"),
            ],
        )
        .properties(height=max(300, len(df) * 50), width=600, title="Leaderboard")
    )

    # Add text labels with delta
    text = (
        alt.Chart(df)
        .mark_text(align="left", dx=5, color=colors["text_primary"], fontSize=12)
        .encode(
            x="total:Q",
            y=alt.Y("name:N", sort="-x"),
            text="delta_label:N",
        )
    )

    return chart + text


def create_contributions_chart(
    contributions_data: Dict[str, Any], selected_options: List[str]
) -> alt.Chart:
    """
    Create a stacked bar chart showing criterion contributions.

    Args:
        contributions_data: Dict with structure from AnalysisService.contributions()
        selected_options: List of option IDs to compare

    Returns:
        Altair Chart object
    """
    if not selected_options or not contributions_data:
        return alt.Chart(pd.DataFrame()).mark_bar()

    colors = get_ctti_colors()

    # Build data for stacked bar chart
    rows = []
    for criterion_id, criterion_info in contributions_data["criteria"].items():
        for option_id in selected_options:
            contribution = contributions_data[option_id].get(criterion_id, 0)
            option_name = contributions_data[option_id].get("name", option_id)

            rows.append(
                {
                    "criterion": criterion_info["name"],
                    "option": option_name,
                    "contribution": contribution,
                    "weight": criterion_info["weight"],
                }
            )

    df = pd.DataFrame(rows)

    # Sort by weight (descending) to show most important criteria first
    criterion_order = (
        df.groupby("criterion")["weight"].first().sort_values(ascending=False).index.tolist()
    )

    # Create stacked bar chart
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("contribution:Q", title="Contribution to Score", stack="zero"),
            y=alt.Y(
                "option:N",
                title="Option",
                sort=alt.EncodingSortField(field="contribution", op="sum", order="descending"),
            ),
            color=alt.Color(
                "criterion:N",
                title="Criterion",
                sort=criterion_order,
                scale=alt.Scale(scheme="blues"),
            ),
            tooltip=[
                alt.Tooltip("option:N", title="Option"),
                alt.Tooltip("criterion:N", title="Criterion"),
                alt.Tooltip("contribution:Q", title="Contribution", format=".1f"),
                alt.Tooltip("weight:Q", title="Weight"),
            ],
        )
        .properties(
            height=max(200, len(selected_options) * 60),
            width=600,
            title="Contributions by Criterion",
        )
    )

    return chart


def create_delta_chart(delta_data: Dict[str, Any]) -> alt.Chart:
    """
    Create a lollipop chart showing delta to winner.

    Args:
        delta_data: Dict with structure from AnalysisService.delta_to_winner()

    Returns:
        Altair Chart object
    """
    if not delta_data or "winner" not in delta_data:
        return alt.Chart(pd.DataFrame()).mark_circle()

    colors = get_ctti_colors()

    # Extract data
    winner_id = delta_data["winner"]
    rows = []

    for key, value in delta_data.items():
        if key == "winner":
            continue

        if isinstance(value, dict) and "delta" in value:
            rows.append(
                {
                    "option": value.get("name", key),
                    "delta": value["delta"],
                    "total": value["total"],
                    "is_winner": key == winner_id,
                }
            )

    df = pd.DataFrame(rows)

    # Sort by delta (ascending - smallest gap first)
    df = df.sort_values("delta", ascending=True).reset_index(drop=True)

    # Mark top 3 gaps (excluding winner which has delta=0)
    df["highlight"] = False
    non_winner_df = df[df["delta"] > 0]
    if len(non_winner_df) >= 3:
        top_3_indices = non_winner_df.nlargest(3, "delta").index
        df.loc[top_3_indices, "highlight"] = True
    elif len(non_winner_df) > 0:
        df.loc[non_winner_df.index, "highlight"] = True

    # Create base chart for lines
    base = alt.Chart(df).encode(
        x=alt.X("delta:Q", title="Gap to Winner (points)"),
        y=alt.Y("option:N", title="Option", sort=alt.EncodingSortField(field="delta", order="ascending")),
    )

    # Lines (stems of lollipops)
    lines = base.mark_rule(color=colors["text_secondary"], opacity=0.5).encode(
        x2=alt.value(0)  # Lines from 0 to delta value
    )

    # Circles (heads of lollipops)
    circles = base.mark_circle(size=100).encode(
        color=alt.condition(
            alt.datum.highlight == True,
            alt.value(colors["error"]),  # Highlight top 3 in error color (red)
            alt.value(colors["secondary"]),  # Others in secondary color
        ),
        opacity=alt.condition(
            alt.datum.highlight == True,
            alt.value(1.0),  # Full opacity for highlighted
            alt.value(0.4),  # Muted for others
        ),
        tooltip=[
            alt.Tooltip("option:N", title="Option"),
            alt.Tooltip("delta:Q", title="Gap to Winner", format=".1f"),
            alt.Tooltip("total:Q", title="Total Score", format=".1f"),
        ],
    )

    chart = (lines + circles).properties(
        height=max(300, len(df) * 40), width=600, title="Gap to Winner"
    )

    return chart
