"""
Metric definitions and categories for Match-Analysis.

Defines computed metrics, their descriptions, units, and aggregation rules.
"""

# Performance metrics
DISTANCE_METRICS = {
    "total_distance_km": {
        "description": "Total distance covered in kilometers",
        "unit": "km",
        "aggregation": "sum",
    },
    "high_speed_distance_km": {
        "description": "Distance at high speed (>6.0 m/s)",
        "unit": "km",
        "aggregation": "sum",
    },
    "sprint_distance_km": {
        "description": "Distance at sprint speed (>7.0 m/s)",
        "unit": "km",
        "aggregation": "sum",
    },
}

ACCELERATION_METRICS = {
    "total_accel_events": {
        "description": "Total acceleration events",
        "unit": "count",
        "aggregation": "sum",
    },
    "total_decel_events": {
        "description": "Total deceleration events",
        "unit": "count",
        "aggregation": "sum",
    },
}

VELOCITY_METRICS = {
    "avg_velocity_ms": {
        "description": "Average velocity",
        "unit": "m/s",
        "aggregation": "mean",
    },
    "max_velocity_ms": {
        "description": "Maximum velocity reached",
        "unit": "m/s",
        "aggregation": "max",
    },
}

# Player load metrics
PLAYER_LOAD_METRICS = {
    "player_load": {
        "description": "Total player load (intensity measure)",
        "unit": "units",
        "aggregation": "sum",
    },
    "avg_player_load": {
        "description": "Average player load",
        "unit": "units",
        "aggregation": "mean",
    },
}

# All metrics grouped by category
METRIC_CATEGORIES = {
    "distance": DISTANCE_METRICS,
    "acceleration": ACCELERATION_METRICS,
    "velocity": VELOCITY_METRICS,
    "player_load": PLAYER_LOAD_METRICS,
}


def get_metric_info(metric_name: str) -> dict:
    """Get information about a specific metric.

    Args:
        metric_name (str): Name of the metric

    Returns:
        dict: Metric info or empty dict if not found
    """
    for category, metrics in METRIC_CATEGORIES.items():
        if metric_name in metrics:
            return metrics[metric_name]
    return {}


def get_category_metrics(category: str) -> dict:
    """Get all metrics in a category.

    Args:
        category (str): Category name

    Returns:
        dict: Metrics in that category or empty dict
    """
    return METRIC_CATEGORIES.get(category, {})
