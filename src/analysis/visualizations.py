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

# FUFA Brand Color Palette
FUFA_COLORS = {
    'dark_blue': '#333d92',
    'light_blue': '#007bc1',
    'mid_blue': '#353b91',
    'red': '#e00024',
    'yellow': '#f8f400',
    'white': '#ffffff',
    'black': '#000000',
    'gray': '#CCCCCC',
}

# Chart color gradients - uses FUFA primaries with intermediate shades
FUFA_GRADIENT_3 = [FUFA_COLORS['dark_blue'], FUFA_COLORS['light_blue'], '#5B7DA3']
FUFA_GRADIENT_5 = ['#B8D4E8', '#8FA3C1', '#5B7DA3', FUFA_COLORS['light_blue'], FUFA_COLORS['dark_blue']]

# Enhanced gradients for creative chart styling
FUFA_GRADIENT_HOLLOW = ['#E8EFF6', '#5B7DA3', FUFA_COLORS['dark_blue']]  # For subtle backgrounds
FUFA_SEQUENTIAL = ['#D9E7F7', '#8FA3C1', '#5B7DA3', FUFA_COLORS['light_blue'], FUFA_COLORS['dark_blue']]  # Light to dark

def create_color_gradient(start_color: str, end_color: str, n_colors: int = 5) -> List[str]:
    """Generate smooth color gradient between two colors."""
    import matplotlib.colors as mc
    import matplotlib.cm as cm
    
    colors = []
    cmap = cm.get_cmap('RdYlBu_r')
    for i in np.linspace(0, 1, n_colors):
        colors.append(mc.rgb2hex(cmap(i)))
    return colors

try:
    from IPython.display import HTML
except ImportError:
    HTML = None  # Optional: for non-notebook environments

def apply_fufa_chart_theme(ax, remove_y_labels=False, remove_y_ticks=False, remove_x_labels=False):
    """Apply professional FUFA brand styling to chart axes with creative enhancements.
    
    Features:
    - Clean spine styling with subtle gridlines
    - Professional typography using system fonts
    - Optional axis removal for cleaner data-to-ink ratio
    - Subtle color palette that doesn't overwhelm data
    """
    # Spine styling - minimal but present
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#D0D0D0')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_color('#D0D0D0')
    ax.spines['bottom'].set_linewidth(0.8)
    
    # Grid - subtle, professional appearance
    ax.yaxis.grid(True, linestyle='-', alpha=0.15, color='#808080', linewidth=0.5)
    ax.set_axisbelow(True)
    
    # Axis management
    if remove_y_labels:
        ax.set_yticklabels([])
    if remove_y_ticks:
        ax.set_yticks([])
    if remove_x_labels:
        ax.set_xticklabels([])
    
    # Professional tick styling - not bold, just readable
    ax.tick_params(labelsize=8.5, colors='#404040')
    ax.xaxis.label.set_fontsize(9.5)
    ax.yaxis.label.set_fontsize(9.5)

def apply_professional_style(ax, title: str, xlabel: str = '', ylabel: str = ''):
    """
    Apply professional FUFA brand styling with creative enhancements.
    
    Uses selective bold (titles only), professional typography, and 
    improved contrast for readability while maintaining FUFA branding.
    
    Args:
        ax: Matplotlib axis object
        title: Plot title (will be bolded)
        xlabel: X-axis label (regular weight)
        ylabel: Y-axis label (regular weight)
    """
    apply_fufa_chart_theme(ax)
    
    # Title - bold and prominent
    ax.set_title(title, fontsize=13, fontweight='bold', pad=18, color=FUFA_COLORS['dark_blue'])
    
    # Axis labels - regular weight, darker color for contrast
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9.5, fontweight='400', color='#1F1F1F')
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9.5, fontweight='400', color='#1F1F1F')
    
    # Tick styling
    ax.tick_params(axis='x', labelsize=8.5, colors='#404040')
    ax.tick_params(axis='y', labelsize=8.5, colors='#404040')


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
    """Plot bar chart of matchdays analysed per club with creative FUFA styling.
    
    Features:
    - Narrower bars with white edges for cleaner appearance
    - Gradient colors for visual interest (dark blue primary)
    - Clear value annotations in circular badges
    - Professional typography with minimal text weight
    """
    config = __import__(
        "src.config.league_definitions", fromlist=["LEAGUE_CONFIG"]
    ).LEAGUE_CONFIG
    tiers = config[league.lower()]["usage_tiers"]

    data = matchdays_df.sort_values("unique_matchdays", ascending=False)

    def tier_color(val):
        if val >= tiers["high"]:
            return FUFA_COLORS['dark_blue']
        elif val >= tiers["medium"]:
            return FUFA_COLORS['light_blue']
        else:
            return FUFA_COLORS['red']

    colors = data["unique_matchdays"].map(tier_color).tolist()

    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    # Create bars with narrower width and hollow effect with edges
    bars = ax.bar(
        range(len(data)),
        data["unique_matchdays"],
        color=colors,
        edgecolor='white',
        linewidth=2,
        alpha=0.92,
        width=0.65  # Narrower bars
    )
    
    # Benchmark reference line - subtle gray
    max_days = config[league.lower()].get("max_matchdays", 22)
    ax.axhline(max_days, color="#A9A9A9", linestyle='--', linewidth=1, alpha=0.5)
    ax.text(
        -0.7, max_days + 0.4, f"Max ({max_days})", 
        color="#808080", fontsize=8, style='italic', fontweight='400'
    )

    apply_fufa_chart_theme(ax, remove_y_labels=True, remove_y_ticks=False)
    
    # Professional x-axis labels
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels(
        [name.upper() for name in data["club_for"]],
        rotation=45,
        ha='right',
        fontsize=9,
        fontweight='400'
    )
    
    ax.set_ylabel("Matchdays Submitted", fontsize=10, fontweight='400', color='#1F1F1F')
    ax.set_title("Data Submission Status by Club", fontsize=13, fontweight='bold', pad=18)
    
    # Value annotations - subtle but clear
    for i, (idx, value) in enumerate(zip(data.index, data["unique_matchdays"])):
        ax.text(
            i, value - 0.6,
            str(int(value)),
            ha="center", va="center",
            fontsize=10, fontweight='600',
            color="white",
            bbox=dict(
                boxstyle="circle,pad=0.3",
                edgecolor='none',
                facecolor=colors[i],
                alpha=0.95
            ),
        )

    plt.tight_layout()
    plt.show()


def plot_stacked_bar_coverage(
    coverage_df: pd.DataFrame,
    max_matchdays: int = 22,
    figsize: Tuple[int, int] = (12, 6),
) -> None:
    """Plot stacked bar chart with creative FUFA styling.
    
    Features:
    - Narrower bars with white edges for hollow effect
    - FUFA color hierarchy: dark blue (primary), light blue (secondary), red (gaps)
    - Professional typography and minimal visual clutter
    """
    data = coverage_df.sort_values("Analysed Matchdays", ascending=False).copy()

    required = ["Analysed Matchdays", "Pending", "Not Uploaded"]
    for col in required:
        if col not in data.columns:
            data[col] = 0

    colors = {
        "Analysed Matchdays": FUFA_COLORS['dark_blue'],
        "Pending": FUFA_COLORS['light_blue'],
        "Not Uploaded": FUFA_COLORS['red'],
    }

    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    x = np.arange(len(data))
    width = 0.65  # Narrower width

    # Stack bars with white edges for visual separation
    p1 = ax.bar(
        x, data["Analysed Matchdays"],
        width=width,
        color=colors["Analysed Matchdays"],
        label="Analysed",
        edgecolor='white', linewidth=2, alpha=0.95
    )
    p2 = ax.bar(
        x, data["Pending"],
        width=width,
        bottom=data["Analysed Matchdays"],
        color=colors["Pending"],
        label="Uploaded – Not Analysed",
        edgecolor='white', linewidth=2, alpha=0.95
    )
    p3 = ax.bar(
        x, data["Not Uploaded"],
        width=width,
        bottom=data["Analysed Matchdays"] + data["Pending"],
        color=colors["Not Uploaded"],
        label="Not Uploaded",
        edgecolor='white', linewidth=2, alpha=0.95
    )

    # Reference line - subtle
    ax.axhline(max_matchdays, color="#A9A9A9", linestyle='--', linewidth=1, alpha=0.5)
    ax.text(
        -0.7, max_matchdays + 0.5,
        f"Complete ({max_matchdays})",
        color="#808080", fontsize=8, style='italic', fontweight='400'
    )

    apply_fufa_chart_theme(ax)
    
    ax.set_xticks(x)
    ax.set_xticklabels([c.upper() for c in data["club_for"]], 
                       rotation=45, ha='right', fontsize=9, fontweight='400')
    ax.set_ylabel("Number of Matchdays", fontsize=10, fontweight='400', color='#1F1F1F')
    ax.set_xlabel("Club", fontsize=10, fontweight='400', color='#1F1F1F')
    ax.set_title("Matchday Coverage by Club", fontsize=13, fontweight='bold', pad=18)
    
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, 
             frameon=False, fontsize=9)

    plt.tight_layout()
    plt.show()

def plot_top_performers_bar(
    leaderboard_df: pd.DataFrame,
    metric: str,
    metric_name: str,
    figsize: Tuple[int, int] = (10, 8),
    color: str = None
):
    """Plot horizontal bar chart with creative FUFA styling.
    
    Features:
    - Horizontal bars for better readability of player names
    - Narrower bars with white edges for professional appearance
    - Clear value labels with professional typography
    """
    if color is None:
        color = FUFA_COLORS['dark_blue']
        
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    df_sorted = leaderboard_df.sort_values(metric, ascending=True).tail(15)  # Top 15
    
    bars = ax.barh(
        df_sorted['p_name'] + ' (' + df_sorted['player_club_'] + ')', 
        df_sorted[metric], 
        color=color, edgecolor='white', linewidth=2, alpha=0.92, height=0.65
    )
    
    for bar in bars:
        width = bar.get_width()
        val_str = f'{width:.0f}' if width > 10 else f'{width:.1f}'
        ax.text(
            width, bar.get_y() + bar.get_height()/2, 
            ' ' + val_str, 
            ha='left', va='center', fontweight='600', fontsize=9, 
            color=FUFA_COLORS['dark_blue']
        )
    
    apply_professional_style(ax, f"Top Performers – {metric_name}", metric_name, "")
    ax.invert_yaxis()
    plt.tight_layout()
    return fig

def plot_league_trend(
    trend_df: pd.DataFrame,
    metric: str,
    metric_name: str,
    figsize: Tuple[int, int] = (12, 6),
    color: str = None
):
    """
    Plot league-wide trend with professional styling.
    
    Features:
    - Clean line with hollow markers
    - Professional typography with subtle styling
    - Proper axis handling with readable labels
    """
    if color is None:
        color = FUFA_COLORS['dark_blue']
        
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    try:
        trend_df = trend_df.copy()
        import re
        trend_df['sort_key'] = trend_df['match_day'].apply(
            lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else 0
        )
        trend_df = trend_df.sort_values('sort_key')
    except Exception:
        pass
        
    ax.plot(
        trend_df['match_day'], trend_df[metric], 
        marker='o', linewidth=2.5, color=color,
        markersize=8, markerfacecolor='white', 
        markeredgecolor=color, markeredgewidth=2
    )
    
    apply_professional_style(ax, f"{metric_name} Trend", "Match Day", metric_name)
    ax.tick_params(axis='x', rotation=45, labelsize=9)
    
    plt.tight_layout()
    return fig

def plot_coverage_heatmap(
    grid_df: pd.DataFrame,
    figsize: Tuple[int, int] = (12, 8)
):
    """
    Plot heatmap with FUFA color scheme.
    
    Features:
    - Professional color mapping (red=missing, dark blue=analysed)
    - Clear cell borders for easy reading
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor='white')
    
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap(['#F5CCCC', FUFA_COLORS['dark_blue']])
    
    sns.heatmap(grid_df, cmap=cmap, cbar=False, linewidths=1, 
               linecolor='white', ax=ax, annot=False)
    
    ax.set_title("Matchday Coverage Analysis", fontsize=13, fontweight='bold', pad=18)
    ax.set_xlabel("Match Day", fontweight='400', color='#1F1F1F')
    ax.set_ylabel("Club", fontweight='400', color='#1F1F1F')
    plt.tight_layout()
    return fig

def plot_metric_histogram(
    df: pd.DataFrame,
    metric: str,
    metric_name: str,
    color: str = None
):
    """Plot metric distribution with creative styling.
    
    Features:
    - Light blue histogram with dark blue KDE overlay
    - Subtle mean line in accent red
    - Professional layout with removable elements
    """
    if color is None:
        color = FUFA_COLORS['light_blue']
        
    fig, ax = plt.subplots(figsize=(9, 6), facecolor='white')
    
    # Histogram with thin outline for definition
    n, bins, patches = ax.hist(
        df[metric].dropna(), bins=22, 
        color=color, alpha=0.75, 
        edgecolor=FUFA_COLORS['dark_blue'], linewidth=1
    )
    
    # KDE overlay in dark blue
    from scipy import stats as sp_stats
    kde = sp_stats.gaussian_kde(df[metric].dropna())
    x_range = np.linspace(df[metric].min(), df[metric].max(), 100)
    ax2 = ax.twinx()
    ax2.plot(x_range, kde(x_range), color=FUFA_COLORS['dark_blue'], linewidth=2.5)
    ax2.set_ylabel('')
    ax2.set_yticks([])
    
    # Mean reference line - subtle
    mean_val = df[metric].mean()
    ax.axvline(mean_val, color=FUFA_COLORS['red'], linestyle='--', 
              linewidth=1.5, alpha=0.6, label=f'Mean: {mean_val:.2f}')
    
    apply_professional_style(ax, f"{metric_name} Distribution", metric_name, "Frequency")
    ax.legend(fontsize=9, frameon=False, loc='upper right')
    plt.tight_layout()
    return fig

def plot_rolling_trend_grid(
    df: pd.DataFrame,
    metrics: Dict[str, str],
    window: int = 3
):
    """
    Plot 2x2 grid of rolling trends with professional styling.
    
    Features:
    - Rolling average with hollow markers
    - Light baseline with dark trend line
    - Clean grid layout with individual titles
    """
    import re
    def get_md_num(s):
        m = re.search(r'\d+', str(s))
        return int(m.group()) if m else 0
        
    daily = df.groupby('match_day')[list(metrics.keys())].mean().reset_index()
    daily['md_num'] = daily['match_day'].apply(get_md_num)
    daily = daily.sort_values('md_num')
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor='white')
    axes = axes.flatten()
    
    for i, (metric, name) in enumerate(metrics.items()):
        ax = axes[i]
        
        # Light baseline
        ax.plot(range(len(daily)), daily[metric], color='#D0D0D0', 
               alpha=0.5, label='Daily Avg', linewidth=1.5, linestyle='-')
        
        # Rolling trend with professional markers
        if len(daily) >= window:
            rolling = daily[metric].rolling(window=window, min_periods=1).mean()
            ax.plot(range(len(daily)), rolling, color=FUFA_COLORS['dark_blue'], 
                   linewidth=2.5, label=f'{window}-MD Rolling', 
                   marker='o', markersize=6, markerfacecolor='white', 
                   markeredgecolor=FUFA_COLORS['dark_blue'], markeredgewidth=1.5)
            
        apply_professional_style(ax, f"{name} Trend", "Match Day", name)
        ax.tick_params(axis='x', rotation=45, labelsize=8)
        ax.legend(fontsize=8, frameon=False, loc='best')
        
    plt.tight_layout()
    return fig

def plot_speed_zones_stacked(
    stats_df: pd.DataFrame,
    title: str = "Speed Zones by Position"
):
    """
    Plot 100% stacked bars with FUFA color gradient.
    
    Features:
    - Creative gradient from light to dark blue
    - Clear percentage labels on each segment
    - Narrower bars with white edges
    """
    fig, ax = plt.subplots(figsize=(11, 7), facecolor='white')
    
    stats_df.plot(
        kind='bar', stacked=True, ax=ax, 
        color=FUFA_GRADIENT_5, alpha=0.92, 
        width=0.65, edgecolor='white', linewidth=2
    )
    
    apply_professional_style(ax, title, "Position", "Percentage (%)")
    ax.set_ylim(0, 100)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=9, fontweight='400')
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False, fontsize=9)
    
    # Add percentage labels in center of each segment
    for container in ax.containers:
        ax.bar_label(container, fmt='%.0f%%', label_type='center', 
                    color='white', fontsize=8, fontweight='600')
        
    plt.tight_layout()
    return fig

def plot_context_comparison(
    context_df: pd.DataFrame,
    metric: str,
    metric_name: str,
    xlabel: str = "Context"
):
    """Plot context comparison with creative bar styling.
    
    Features:
    - Dark blue primary bars with white edges
    - Highlight max value in lighter blue
    - Clear value labels above each bar
    """
    fig, ax = plt.subplots(figsize=(9, 6), facecolor='white')
    
    bars = ax.bar(context_df.index, context_df[metric], color=FUFA_COLORS['dark_blue'], 
                 alpha=0.88, edgecolor='white', linewidth=2, width=0.6)
    
    # Highlight maximum in lighter blue
    max_val = context_df[metric].max()
    for bar in bars:
        if bar.get_height() == max_val:
            bar.set_color(FUFA_COLORS['light_blue'])
            
    # Professional value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + (max_val * 0.02),
               f'{height:.1f}',
               ha='center', va='bottom', fontsize=10, fontweight='600', 
               color=FUFA_COLORS['dark_blue'])
    
    apply_professional_style(ax, f"{metric_name} by {xlabel}", xlabel, metric_name)
    ax.set_xticklabels(context_df.index, fontsize=9, fontweight='400')
    plt.tight_layout()
    return fig


def plot_matchday_club_heatmap(
    grid_df: pd.DataFrame,
    figsize: Tuple[int, int] = (14, 8),
) -> None:
    """Plot heatmap with professional FUFA styling.
    
    Features:
    - Intuitive color scheme (red=missing, dark blue=analysed)
    - Clear cell borders for readability
    - Professional axis labels
    """
    import matplotlib.patches as mpatches

    clubs = grid_df.columns.tolist()
    matchdays = grid_df.index.tolist()

    color_map = {1: FUFA_COLORS['dark_blue'], 0: '#F5CCCC'}

    fig, ax = plt.subplots(figsize=figsize, facecolor='white')

    # Plot cells with white borders
    for y, md in enumerate(matchdays):
        for x, club in enumerate(clubs):
            val = grid_df.loc[md, club]
            color = color_map[val]
            rect = plt.Rectangle((x, y), 1, 1, facecolor=color, 
                                edgecolor="white", linewidth=1.5)
            ax.add_patch(rect)

    # Professional axis setup
    ax.set_xticks(np.arange(len(clubs)) + 0.5)
    ax.set_xticklabels([c.upper() for c in clubs], rotation=45, ha='right', 
                       fontsize=9, fontweight='400')
    ax.set_yticks(np.arange(len(matchdays)) + 0.5)
    ax.set_yticklabels([i.upper() for i in matchdays], fontsize=9, fontweight='400')

    ax.set_xlim(0, len(clubs))
    ax.set_ylim(0, len(matchdays))
    ax.invert_yaxis()

    ax.set_xlabel("Club", fontsize=10, fontweight='400', color='#1F1F1F')
    ax.set_ylabel("Match Day", fontsize=10, fontweight='400', color='#1F1F1F')
    ax.set_title("Matchdays Analysed per Club", fontsize=13, fontweight='bold', pad=18)

    # Clean legend
    handles = [
        mpatches.Patch(color=color_map[1], label="Analysed"),
        mpatches.Patch(color=color_map[0], label="Missing"),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.02, 1),
             frameon=False, fontsize=9)

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
    """Plot metric trend with professional styling.
    
    Features:
    - Clean line with hollow markers
    - Subtle std deviation shading
    - Professional typography throughout
    """
    mean_col = f"{metric}_mean"
    std_col = f"{metric}_std"

    if mean_col not in trend_df.columns:
        print(f"Error: {mean_col} not found in DataFrame")
        return

    fig, ax = plt.subplots(figsize=figsize, facecolor='white')

    # Std shading (subtle)
    if show_std and std_col in trend_df.columns:
        upper = trend_df[mean_col] + trend_df[std_col]
        lower = trend_df[mean_col] - trend_df[std_col]
        ax.fill_between(range(len(trend_df)), lower, upper, 
                       alpha=0.12, color=FUFA_COLORS['dark_blue'], label='±1 Std Dev')

    # Line plot with professional styling
    ax.plot(
        range(len(trend_df)), trend_df[mean_col],
        marker="o", linewidth=2.5, color=FUFA_COLORS['dark_blue'],
        label=f"{metric} (Mean)",
        markersize=8, markerfacecolor='white',
        markeredgecolor=FUFA_COLORS['dark_blue'], markeredgewidth=2
    )

    apply_professional_style(ax, f"{metric} Trend Over Season", "Match Day", metric)
    
    ax.set_xticks(range(len(trend_df)))
    ax.set_xticklabels(trend_df["match_day"], rotation=45, fontsize=9, fontweight='400')
    ax.legend(frameon=False, fontsize=9, loc='best')

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
    """Plot positional comparison with professional styling.
    
    Features:
    - Dark blue bars with white edges for each metric
    - Value labels above bars
    - Professional typography with selective bold
    - Clean grid layout
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
        1, len(metrics), figsize=(5.5 * len(metrics), 6), 
        sharey=False, facecolor='white'
    )
    if len(metrics) == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        bars = ax.bar(
            data_to_plot["Position"], data_to_plot[metric],
            color=FUFA_COLORS['dark_blue'], edgecolor='white', 
            linewidth=1.5, alpha=0.92, width=0.65
        )
        
        # Value labels above bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}', ha='center', va='bottom', 
                   fontsize=9, fontweight='600', color=FUFA_COLORS['dark_blue'])
        
        apply_professional_style(ax, metric, "Position", "Value")
        ax.set_xticklabels(data_to_plot["Position"], rotation=45, ha='right', 
                          fontsize=9, fontweight='400')

    plt.tight_layout()
    plt.show()