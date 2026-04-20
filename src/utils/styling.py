"""
Styling and formatting utilities for document generation and visualization.

Provides functions for creating styled pandas DataFrames, Word document formatting,
and consistent visualization styling across reports and notebooks.
"""

from typing import Optional, Dict, List, Tuple
import pandas as pd


# ============================================================================
# Color Palettes & Theme Constants
# ============================================================================

# Usage tier color palette (for club engagement visualization)
USAGE_TIER_COLORS = {
    "high": "#4596cf",  # Dark blue for high engagement (≥18 match days)
    "medium": "#ff7f0e",  # Orange for medium engagement (13-17 match days)
    "low": "#d62728",  # Red for low engagement (<13 match days)
}

# Softer color palette for stacked bar charts
STACKED_COLORS = {
    "Analysed": "#38759e",  # Softer blue
    "Pending": "#ee9d50",  # Softer orange
    "not_uploaded": "#f8373a",  # Softer red
}

# Accent colors for charts
CHART_COLORS = {
    "primary_line": "orange",
    "secondary_line": "gray",
    "accent_circle": "#FE912A",
    "grid": "#E0DCDD",
}

# ============================================================================
# Pandas DataFrame Styling Functions
# ============================================================================


def style_table_for_docs(
    df: pd.DataFrame, hide_index: bool = False, caption: Optional[str] = None
) -> "pd.io.formats.style.Styler":
    """
    Create a styled pandas DataFrame for document export (DOCX).

    Applies professional table styling with:
    - Black text and borders
    - Clean white background
    - Compact padding for smaller rows
    - Optional index hiding

    Args:
        df (pd.DataFrame): DataFrame to style
        hide_index (bool): Whether to hide the index column. Default False.
        caption (Optional[str]): Caption text for the table

    Returns:
        pd.io.formats.style.Styler: Styled DataFrame object (can be exported to DOCX)

    Example:
        >>> df = pd.DataFrame({'Club': ['A', 'B'], 'Score': [10, 20]})
        >>> styled = style_table_for_docs(df, hide_index=True, caption='Team Scores')
        >>> styled.to_html()  # or export to Word document
    """
    styled = df.style.set_properties(
        **{
            "color": "black",
            "background-color": "white",
            "border": "1px solid black",
            "text-align": "center",
            "padding": "2px",  # Reduces row height for compact display
        }
    ).set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("color", "black"),
                    ("border", "1px solid black"),
                    ("padding", "2px"),
                    ("background-color", "white"),
                ],
            },
            {
                "selector": "td",
                "props": [
                    ("color", "black"),
                    ("border", "1px solid black"),
                    ("padding", "2px"),
                ],
            },
            {
                "selector": "table",
                "props": [
                    ("border", "2px solid black"),
                    ("border-collapse", "collapse"),
                ],
            },
        ]
    )

    if hide_index:
        styled = styled.hide(axis="index")

    if caption:
        styled = styled.set_caption(caption)

    return styled


def style_metric_summary_table(
    df: pd.DataFrame, metric_type: str = "all", hide_index: bool = False
) -> "pd.io.formats.style.Styler":
    """
    Create a styled metric summary table with rounded values.

    Args:
        df (pd.DataFrame): Metric summary DataFrame
        metric_type (str): One of 'all', 'volume', or 'intensity' for context
        hide_index (bool): Whether to hide index

    Returns:
        pd.io.formats.style.Styler: Styled DataFrame
    """
    # Round numeric columns to 2 decimal places
    df_rounded = df.copy()
    numeric_cols = df_rounded.select_dtypes(include=["float64", "int64"]).columns
    df_rounded[numeric_cols] = df_rounded[numeric_cols].round(2)

    styled = style_table_for_docs(df_rounded, hide_index=hide_index)

    caption = f"Metric Summary ({metric_type.title()})"
    return styled.set_caption(caption)


# ============================================================================
# Chart Styling Functions
# ============================================================================


def get_figure_style() -> Dict:
    """
    Get consistent figure styling parameters for matplotlib.

    Returns:
        dict: Figure style parameters

    Example:
        >>> fig, ax = plt.subplots(**get_figure_style())
    """
    return {
        "figsize": (12, 6),
        "facecolor": "white",
    }


def apply_chart_theme(ax) -> None:
    """
    Apply consistent theme styling to a matplotlib axis.

    Removes unnecessary spines, adds gridlines, and sets professional colors.

    Args:
        ax: matplotlib axis object
    """
    # Define gray color for borders
    gray_color = "#808080"

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Style remaining spines
    ax.spines["bottom"].set_color(gray_color)
    ax.spines["left"].set_color(gray_color)

    # Add gridlines
    ax.yaxis.grid(True, linestyle="--", alpha=0.5, color=CHART_COLORS["grid"])
    ax.set_axisbelow(True)


def get_usage_tier_color(match_days: int, tier_thresholds: dict) -> str:
    """
    Get color for a club based on match day upload count.

    Args:
        match_days (int): Number of uploaded/analyzed match days
        tier_thresholds (dict): Thresholds with keys 'high', 'medium', 'low'
                               e.g., {'high': 18, 'medium': 13, 'low': 0}

    Returns:
        str: Hex color code

    Example:
        >>> thresholds = {'high': 18, 'medium': 13, 'low': 0}
        >>> get_usage_tier_color(20, thresholds)
        '#4596cf'  # High engagement

        >>> get_usage_tier_color(15, thresholds)
        '#ff7f0e'  # Medium engagement
    """
    if match_days >= tier_thresholds.get("high", 18):
        return USAGE_TIER_COLORS["high"]
    elif match_days >= tier_thresholds.get("medium", 13):
        return USAGE_TIER_COLORS["medium"]
    else:
        return USAGE_TIER_COLORS["low"]


def create_usage_tier_color_map(data: pd.Series, tier_thresholds: dict) -> List[str]:
    """
    Create a list of colors for each club based on usage tiers.

    Args:
        data (pd.Series): Series with match day counts indexed by club
        tier_thresholds (dict): Tier thresholds

    Returns:
        List[str]: List of hex color codes

    Example:
        >>> data = pd.Series({'Club A': 20, 'Club B': 15, 'Club C': 5})
        >>> colors = create_usage_tier_color_map(data, tier_thresholds)
    """
    return [get_usage_tier_color(val, tier_thresholds) for val in data.values]


# ============================================================================
# Text & Label Formatting
# ============================================================================


def format_metric_label(metric_name: str) -> str:
    """
    Convert metric column name to human-readable label.

    Args:
        metric_name (str): Internal metric name (e.g., 'player_load')

    Returns:
        str: Human-readable label (e.g., 'Player Load')

    Example:
        >>> format_metric_label('distance_per_min_mmin')
        'Distance Per Min Mmin'
    """
    return metric_name.replace("_", " ").title()


def format_club_name(club: str, uppercase: bool = False) -> str:
    """
    Format club name for display.

    Args:
        club (str): Club name
        uppercase (bool): Whether to uppercase (for titles)

    Returns:
        str: Formatted club name

    Example:
        >>> format_club_name('Capital FC')
        'Capital Fc'

        >>> format_club_name('Capital FC', uppercase=True)
        'CAPITAL FC'
    """
    if uppercase:
        return club.upper()
    return club.title()


# ============================================================================
# Word Document Formatting Helpers
# ============================================================================


def get_cell_color_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert hex color to RGB tuple for python-docx.

    Args:
        hex_color (str): Hex color string (e.g., '#FF0000')

    Returns:
        Tuple[int, int, int]: RGB tuple

    Example:
        >>> get_cell_color_rgb('#FF0000')
        (255, 0, 0)

        >>> get_cell_color_rgb('#4596cf')
        (69, 150, 207)
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


# ============================================================================
# Report Layout Helpers
# ============================================================================


def get_report_section_styles() -> Dict:
    """
    Get consistent styling parameters for report sections.

    Returns:
        dict: Section styling parameters
    """
    return {
        "heading_level": 1,
        "heading_size": 16,
        "subheading_size": 14,
        "body_size": 11,
        "line_spacing": 1.15,
    }


def create_position_group_abbreviations() -> Dict[str, str]:
    """
    Create abbreviations for position groups.

    Returns:
        dict: Position group to abbreviation mapping

    Example:
        >>> abbr = create_position_group_abbreviations()
        >>> abbr['defenders']
        'DEF'
    """
    return {
        "defenders": "DEF",
        "midfielder": "MID",
        "midfielders": "MID",
        "forward": "FWD",
        "forwards": "FWD",
        "goalkeeper": "GK",
        "goalkeepers": "GK",
    }
