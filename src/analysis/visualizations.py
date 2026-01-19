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
from io import BytesIO
# import matplotlib.ticker as ticker # Unused for now

# Configure default style
plt.style.use('seaborn-v0_8-whitegrid')

try:
    from IPython.display import HTML
except ImportError:
    HTML = None  # Optional: for non-notebook environments

def apply_professional_style(ax, title: str, xlabel: str, ylabel: str):
    """
    Apply a professional, clean style to a matplotlib axis.
    
    Args:
        ax: Matplotlib axis object
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
    """
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Clean up ticks
    ax.tick_params(axis='both', which='both', length=0)
    
    # Add light grid
    ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#cccccc')
    ax.set_axisbelow(True)
    
    # Set labels with nice fonts
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20, loc='left', color='#333333')
    ax.set_xlabel(xlabel, fontsize=10, fontweight='bold', color='#555555')
    ax.set_ylabel(ylabel, fontsize=10, fontweight='bold', color='#555555')
    
    # Customize tick labels
    ax.tick_params(axis='x', rotation=45, labelsize=9)
    ax.tick_params(axis='y', labelsize=9)


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


    ax.tick_params(axis='x', rotation=45, labelsize=9)
    ax.tick_params(axis='y', labelsize=9)

def plot_top_performers_bar(
    leaderboard_df: pd.DataFrame,
    metric: str,
    metric_name: str,
    figsize: Tuple[int, int] = (10, 8),
    color: str = "#1f77b4"
):
    """Plot horizontal bar chart of top performers."""
    fig, ax = plt.subplots(figsize=figsize)
    df_sorted = leaderboard_df.sort_values(metric, ascending=True)
    
    bars = ax.barh(df_sorted['p_name'] + ' (' + df_sorted['player_club_'] + ')', 
                  df_sorted[metric], 
                  color=color, alpha=0.8)
    
    for bar in bars:
        width = bar.get_width()
        val_str = f'{width:.0f}' if width > 10 else f'{width:.1f}'
        ax.text(width, bar.get_y() + bar.get_height()/2, 
                val_str, 
                ha='left', va='center', fontweight='bold', fontsize=9, color='#333333')
                
    apply_professional_style(ax, f"TopPlayers - {metric_name}", metric_name, "")
    plt.tight_layout()
    return fig

def plot_league_trend(
    trend_df: pd.DataFrame,
    metric: str,
    metric_name: str,
    figsize: Tuple[int, int] = (12, 6),
    color: str = "#ff7f0e"
):
    """
    Plot league-wide trend over matchdays.
    
    Args:
        trend_df: DataFrame with ['match_day', metric] (aggregated mean)
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Ensure correct ordering if match_day is string Md1, Md2...
    # helper to sort naturally
    try:
        trend_df = trend_df.copy()
        import re
        trend_df['sort_key'] = trend_df['match_day'].apply(lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else 0)
        trend_df = trend_df.sort_values('sort_key')
    except Exception:
        pass # Fallback
        
    ax.plot(trend_df['match_day'], trend_df[metric], marker='o', linewidth=2.5, color=color)
    ax.fill_between(trend_df['match_day'], trend_df[metric], alpha=0.1, color=color)
    
    apply_professional_style(ax, f"{metric_name} Trend", "Match Day", metric_name)
    ax.tick_params(axis='x', rotation=90)
    
    plt.tight_layout()
    return fig

def plot_coverage_heatmap(
    grid_df: pd.DataFrame,
    figsize: Tuple[int, int] = (12, 8)
):
    """
    Plot heatmap of matchday participation.
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Custom cmap: 0=light grey/red, 1=green
    cmap = sns.color_palette(["#f8d7da", "#d4edda"], as_cmap=True)
    # Or simple binary
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(['#eeeeee', '#28a745']) # Grey vs Green
    
    sns.heatmap(grid_df, cmap=cmap, cbar=False, linewidths=1, linecolor='white', ax=ax, annot=False)
    
    # Ax settings
    ax.set_title("Matchday Coverage Analysis", fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel("Match Day", fontweight='bold')
    ax.set_ylabel("Club", fontweight='bold')
    plt.tight_layout()
    return fig

def plot_metric_histogram(
    df: pd.DataFrame,
    metric: str,
    metric_name: str,
    color: str = "#17a2b8"
):
    """Plot distribution of a metric."""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    sns.histplot(df[metric].dropna(), kde=True, color=color, ax=ax, edgecolor='white')
    
    mean_val = df[metric].mean()
    ax.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.1f}')
    ax.legend()
    
    apply_professional_style(ax, f"Distribution of {metric_name}", metric_name, "Frequency")
    plt.tight_layout()
    return fig

def plot_rolling_trend_grid(
    df: pd.DataFrame,
    metrics: Dict[str, str], # metric_col -> display_name
    window: int = 3
):
    """
    Plot 2x2 grid of rolling averages for key metrics.
    """
    # Create aggregated daily stats
    # Sort by matchday first
    import re
    def get_md_num(s):
        m = re.search(r'\d+', str(s))
        return int(m.group()) if m else 0
        
    daily = df.groupby('match_day')[list(metrics.keys())].mean().reset_index()
    daily['md_num'] = daily['match_day'].apply(get_md_num)
    daily = daily.sort_values('md_num')
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for i, (metric, name) in enumerate(metrics.items()):
        ax = axes[i]
        
        # Raw line
        ax.plot(daily['match_day'], daily[metric], color='#cccccc', alpha=0.5, label='Daily Avg')
        
        # Rolling line
        if len(daily) >= window:
            rolling = daily[metric].rolling(window=window, min_periods=1).mean()
            ax.plot(daily['match_day'], rolling, color='#1f77b4', linewidth=2.5, label=f'{window}-MD Rolling')
            
        apply_professional_style(ax, f"{name} Trend", "", name)
        
        # Rotate x labels for all
        ax.tick_params(axis='x', rotation=90)
        
    plt.tight_layout()
    return fig

def plot_speed_zones_stacked(
    stats_df: pd.DataFrame,
    title: str = "Speed Zones by Position"
):
    """
    Plot 100% stacked bar chart for speed zones.
    stats_df: Index=Position, Cols=Zones (values are %)
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    stats_df.plot(kind='bar', stacked=True, ax=ax, colormap='viridis', alpha=0.9, width=0.8)
    
    apply_professional_style(ax, title, "Position", "Percentage (%)")
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add labels
    for c in ax.containers:
        ax.bar_label(c, fmt='%.0f%%', label_type='center', color='white', fontsize=8)
        
    plt.tight_layout()
    return fig

def plot_context_comparison(
    context_df: pd.DataFrame,
    metric: str,
    metric_name: str,
    xlabel: str = "Context"
):
    """From DataFrame index=Context, col=Metric"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    bars = ax.bar(context_df.index, context_df[metric], color='#6c757d', alpha=0.8)
    
    # Highlight max
    max_val = context_df[metric].max()
    for bar in bars:
        if bar.get_height() == max_val:
            bar.set_color('#28a745')
            
    # Labels
    ax.bar_label(bars, fmt='%.1f')
    
    apply_professional_style(ax, f"{metric_name} by {xlabel}", xlabel, metric_name)
    plt.tight_layout()
    return fig


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
