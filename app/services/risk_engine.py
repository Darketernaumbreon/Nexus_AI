"""
Risk Engine

Standardizes risk classification across hazards.
Provides consistent HIGH/MEDIUM/LOW/NEGLIGIBLE classification.

Author: NEXUS-AI Team
"""

from typing import Tuple
from enum import Enum

from app.core.logging import get_logger

logger = get_logger("risk_engine")


class RiskLevel(str, Enum):
    """Risk level classification."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NEGLIGIBLE = "NEGLIGIBLE"


class ConfidenceLevel(str, Enum):
    """Confidence level for predictions."""
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


def classify_risk(probability: float) -> RiskLevel:
    """
    Classify risk level based on probability.
    
    Thresholds (calibrated for demo clarity):
        - HIGH: >= 0.6
        - MEDIUM: >= 0.3
        - LOW: >= 0.1
        - NEGLIGIBLE: < 0.1
    
    Args:
        probability: Model output probability [0, 1]
    
    Returns:
        RiskLevel enum
    """
    if probability >= 0.6:
        return RiskLevel.HIGH
    elif probability >= 0.3:
        return RiskLevel.MEDIUM
    elif probability >= 0.1:
        return RiskLevel.LOW
    else:
        return RiskLevel.NEGLIGIBLE


def get_confidence(
    data_quality: str = "good",
    weather_cached: bool = True
) -> ConfidenceLevel:
    """
    Determine prediction confidence based on data quality.
    
    Args:
        data_quality: Quality flag from input data
        weather_cached: Whether weather was from cache (more reliable)
    
    Returns:
        ConfidenceLevel enum
    """
    if data_quality == "good" and weather_cached:
        return ConfidenceLevel.HIGH
    elif data_quality == "good" or weather_cached:
        return ConfidenceLevel.MODERATE
    else:
        return ConfidenceLevel.LOW


def estimate_lead_time(
    probability: float,
    rainfall_trend: str = "increasing"
) -> int:
    """
    Estimate lead time (hours) for flood warning.
    
    Simple heuristic based on probability and weather trend.
    In production, use hydrological models.
    
    Args:
        probability: Flood probability
        rainfall_trend: "increasing", "stable", "decreasing"
    
    Returns:
        Estimated hours before event (0 if imminent)
    """
    if probability >= 0.8:
        base_hours = 6
    elif probability >= 0.6:
        base_hours = 12
    elif probability >= 0.3:
        base_hours = 24
    else:
        base_hours = 48
    
    # Adjust for trend
    if rainfall_trend == "increasing":
        base_hours = max(2, base_hours - 6)
    elif rainfall_trend == "decreasing":
        base_hours = base_hours + 6
    
    return base_hours
