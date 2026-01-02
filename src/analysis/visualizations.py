"""
Visualization utilities for match analysis reports.

Provides functions to generate matplotlib plots and styled tables for
consistent use across analysis notebooks.
"""

from typing import Optional, Dict, List, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

try:
    from IPython.display import HTML
except ImportError:
    HTML = None  # Optional: for non-notebook environments


# ============================================================================
# Table Styling
# ============================================================================


def style_table_for_docs(
    df: pd.DataFrame,
    hide_index: bool = False,
    hide_columns: Optional[List[str]] = None,
) -> "Styler":
    """Apply consistent styling to DataFrames for document output.

    Creates clean, bordered tables with consistent formatting suitable
    for embedding in reports and notebooks.

    Args:
        df (pd.DataFrame): DataFrame to style
        hide_index (bool): Hide row index
        hide_columns (Optional[List[str]]): Columns to hide

    Returns:
        Styler: Styled DataFrame (use .to_html() or display in notebook)

    Example:
        >>> df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        >>> style_table_for_docs(df, hide_index=True)
    """
    styled = df.style.set_properties(
        **{
            "color": "black",
            "background-color": "white",
            "border": "1px solid black",
            "text-align": "center",
            "padding": "2px",
        }
    ).set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("color", "black"),
                    ("border", "1px solid black"),
                    ("padding", "2px"),
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

    if hide_columns:
        styled = styled.hide(axis="columns", subset=hide_columns)

    return styled


# ============================================================================
# Bar Charts & Comparisons
# ============================================================================


def plot_matchdays_per_club(
    matchdays_df: pd.DataFrame,
    league: str = "fwsl",
    figsize: Tuple[int, int] = (12, 6),
) -> None:
    """Plot bar chart of matchdays analysed per club with color coding.

    Args:
        matchdays_df (pd.DataFrame): From `matchdays_per_club(df)`
                                     Columns: [club_for, unique_matchdays]
        league (str): League identifier (for tier thresholds)
        figsize (Tuple[int, int]): Figure size
    """
    config = __import__(
        "src.config.league_definitions", fromlist=["LEAGUE_CONFIG"]
    ).LEAGUE_CONFIG
    tiers = config[league.lower()]["usage_tiers"]

    # Sort and assign colors
    data = matchdays_df.sort_values("unique_matchdays", ascending=False)

    def tier_color(val):
        if val >= tiers["high"]:
            return "#4596cf"  # dark blue
        elif val >= tiers["medium"]:
            return "#ff7f0e"  # orange
        else:
            return "#d62728"  # red

    colors = data["unique_matchdays"].map(tier_color).tolist()

    # Plot
    fig, ax = plt.subplots(figsize=figsize)
    sns.barplot(
        data=data,
        x="club_for",
        y="unique_matchdays",
        palette=colors,
        legend=False,
        ax=ax,
    )

    # Benchmark line
    max_days = config[league.lower()].get("max_matchdays", 22)
    ax.axhline(max_days, color="gray", linestyle="--", linewidth=1)
    ax.text(
        -0.5, max_days + 1, f"Maximum Matchdays ({max_days})", color="gray", fontsize=9
    )

    # Styling
    ax.set_xticklabels(
        [lbl.get_text().upper() for lbl in ax.get_xticklabels()],
        rotation=90,
        fontsize=9,
    )
    ax.set_xlabel("Club", fontsize=11)
    ax.set_ylabel("Number of Matchdays Uploaded", fontsize=11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_yticklabels([])
    ax.set_yticks([])

    # Annotations
    for i, value in enumerate(data["unique_matchdays"]):
        ax.text(
            i,
            value - 1.5,
            str(value),
            ha="center",
            va="bottom",
            fontsize=8,
            color="black",
            fontweight="bold",
            bbox=dict(
                boxstyle="circle,pad=0.22",
                edgecolor="#667898",
                facecolor="white",
                linewidth=1,
            ),
        )

    plt.tight_layout()
    plt.show()


def plot_stacked_bar_coverage(
    coverage_df: pd.DataFrame,
    max_matchdays: int = 22,
    figsize: Tuple[int, int] = (12, 6),
) -> None:
    """Plot stacked bar chart of coverage: Analysed / Pending / Not Uploaded.

    Args:
        coverage_df (pd.DataFrame): From `club_coverage_analysis(df, league)`
                                    Must have columns:
                                    [club_for, Analysed Matchdays, Pending, Not Uploaded]
        max_matchdays (int): Maximum possible matchdays
        figsize (Tuple[int, int]): Figure size
    """
    data = coverage_df.sort_values("Analysed Matchdays", ascending=False).copy()

    # Ensure columns exist
    required = ["Analysed Matchdays", "Pending", "Not Uploaded"]
    for col in required:
        if col not in data.columns:
            data[col] = 0

    colors = {
        "Analysed Matchdays": "#38759e",
        "Pending": "#ee9d50",
        "Not Uploaded": "#f8373a",
    }

    fig, ax = plt.subplots(figsize=figsize)
    x = np.arange(len(data))

    # Stack bars
    ax.bar(
        x,
        data["Analysed Matchdays"],
        color=colors["Analysed Matchdays"],
        label="Analysed",
    )
    ax.bar(
        x,
        data["Pending"],
        bottom=data["Analysed Matchdays"],
        color=colors["Pending"],
        label="Uploaded – Not Analysed",
    )
    ax.bar(
        x,
        data["Not Uploaded"],
        bottom=data["Analysed Matchdays"] + data["Pending"],
        color=colors["Not Uploaded"],
        label="Not Uploaded",
    )

    # Benchmark
    ax.axhline(max_matchdays, color="gray", linestyle="--", linewidth=1)
    ax.text(
        -0.5,
        max_matchdays + 1,
        f"Complete ({max_matchdays} matchdays)",
        color="gray",
        fontsize=9,
    )

    # Styling
    ax.set_xticks(x)
    ax.set_xticklabels([c.upper() for c in data["club_for"]], rotation=90, fontsize=9)
    ax.set_ylabel("Number of Matchdays", fontsize=11)
    ax.set_xlabel("Club", fontsize=11)
    ax.legend(
        loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.show()


# ============================================================================
# Heat Map: Matchday-Club Coverage
# ============================================================================


def plot_matchday_club_heatmap(
    grid_df: pd.DataFrame,
    figsize: Tuple[int, int] = (14, 8),
) -> None:
    """Plot heatmap of matchday-club coverage (green=analysed, red=missing).

    Args:
        grid_df (pd.DataFrame): From `matchday_club_coverage_grid(df)`
                                Binary grid (1=analysed, 0=missing)
        figsize (Tuple[int, int]): Figure size
    """
    import matplotlib.patches as mpatches

    clubs = grid_df.columns.tolist()
    matchdays = grid_df.index.tolist()

    color_map = {1: "#5cb85c", 0: "#d9534f"}  # green / red

    fig, ax = plt.subplots(figsize=figsize)

    # Plot cells
    for y, md in enumerate(matchdays):
        for x, club in enumerate(clubs):
            val = grid_df.loc[md, club]
            color = color_map[val]
            rect = plt.Rectangle((x, y), 1, 1, facecolor=color, edgecolor="white")
            ax.add_patch(rect)

    # Axes
    ax.set_xticks(np.arange(len(clubs)) + 0.5)
    ax.set_xticklabels([c.upper() for c in clubs], rotation=90, fontsize=9)
    ax.set_yticks(np.arange(len(matchdays)) + 0.5)
    ax.set_yticklabels([i.upper() for i in matchdays], fontsize=9)

    ax.set_xlim(0, len(clubs))
    ax.set_ylim(0, len(matchdays))
    ax.invert_yaxis()

    ax.set_xlabel("Club", fontsize=11)
    ax.set_ylabel("Match Day", fontsize=11)
    ax.set_title("Matchdays Analysed per Club", fontsize=13, fontweight="bold")

    # Legend
    handles = [
        mpatches.Patch(color=color_map[1], label="Analysed Matchday"),
        mpatches.Patch(color=color_map[0], label="Missing Matchday"),
    ]
    ax.legend(
        handles=handles,
        title="Color Map",
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        frameon=False,
    )

    plt.tight_layout()
    plt.show()


# ============================================================================
# Metric Trends Over Matchdays
# ============================================================================


def plot_metric_trend(
    trend_df: pd.DataFrame,
    metric: str,
    figsize: Tuple[int, int] = (12, 6),
    show_std: bool = True,
) -> None:
    """Plot trend of a metric across matchdays with optional std dev shading.

    Args:
        trend_df (pd.DataFrame): From `matchday_trend_metrics(df, metric)`
                                 Columns: [match_day, {metric}_mean, {metric}_std]
        metric (str): Metric name (used for labels)
        figsize (Tuple[int, int]): Figure size
        show_std (bool): Shade standard deviation bands
    """
    mean_col = f"{metric}_mean"
    std_col = f"{metric}_std"

    if mean_col not in trend_df.columns:
        print(f"Error: {mean_col} not found in DataFrame")
        return

    fig, ax = plt.subplots(figsize=figsize)

    # Line plot
    ax.plot(
        range(len(trend_df)),
        trend_df[mean_col],
        marker="o",
        linewidth=2,
        color="#1f77b4",
        label=f"{metric} (Mean)",
    )

    # Std shading
    if show_std and std_col in trend_df.columns:
        upper = trend_df[mean_col] + trend_df[std_col]
        lower = trend_df[mean_col] - trend_df[std_col]
        ax.fill_between(range(len(trend_df)), lower, upper, alpha=0.2, color="#1f77b4")

    # Styling
    ax.set_xticks(range(len(trend_df)))
    ax.set_xticklabels(trend_df["match_day"], rotation=45)
    ax.set_xlabel("Match Day", fontsize=11)
    ax.set_ylabel(metric, fontsize=11)
    ax.set_title(f"Trend: {metric} Over Season", fontsize=13, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()

    plt.tight_layout()
    plt.show()


# ============================================================================
# Positional Comparison
# ============================================================================


def plot_positional_metrics(
    position_df: pd.DataFrame,
    metrics: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (14, 8),
) -> None:
    """Plot positional comparison for selected metrics.

    Args:
        position_df (pd.DataFrame): From `positional_comparison_all_metrics(df)`
                                    Index: positions, Columns: metrics
        metrics (Optional[List[str]]): Specific metrics to plot.
                                       If None, plots all.
        figsize (Tuple[int, int]): Figure size
    """
    if metrics is None:
        metrics = position_df.columns.tolist()

    metrics = [m for m in metrics if m in position_df.columns]
    if not metrics:
        print("No metrics found to plot")
        return

    data_to_plot = position_df[metrics].reset_index()
    data_to_plot.columns = ["Position"] + metrics

    fig, axes = plt.subplots(
        1, len(metrics), figsize=(5 * len(metrics), 5), sharey=False
    )
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        data_to_plot.plot(x="Position", y=metric, kind="bar", ax=ax, legend=False)
        ax.set_title(metric, fontsize=12, fontweight="bold")
        ax.set_xlabel("Position")
        ax.set_ylabel("Mean Value")
        ax.grid(True, alpha=0.3, linestyle="--")
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    plt.tight_layout()
    plt.show()
