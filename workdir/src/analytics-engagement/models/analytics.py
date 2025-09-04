from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid

class AnalyticsType(Enum):
    CUSTOMER_BEHAVIOR = "customer_behavior"
    SPENDING_PATTERN = "spending_pattern"
    REDEMPTION_TREND = "redemption_trend"
    ENGAGEMENT_METRIC = "engagement_metric"

class RecommendationType(Enum):
    PRODUCT = "product"
    CATEGORY = "category"
    REDEMPTION = "redemption"
    OFFER = "offer"

@dataclass
class CustomerAnalytics:
    customer_id: str
    total_transactions: int = 0
    total_spending: float = 0.0
    total_points_earned: int = 0
    total_points_redeemed: int = 0
    current_tier: str = "bronze"
    favorite_categories: List[str] = field(default_factory=list)
    avg_transaction_value: float = 0.0
    last_transaction_date: Optional[datetime] = None
    engagement_score: float = 0.0
    churn_risk: str = "low"
    lifetime_value: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class SpendingPattern:
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    category: str = ""
    monthly_spending: float = 0.0
    transaction_frequency: int = 0
    seasonal_trend: Dict[str, float] = field(default_factory=dict)
    growth_rate: float = 0.0
    prediction_confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Recommendation:
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    recommendation_type: RecommendationType = RecommendationType.PRODUCT
    title: str = ""
    description: str = ""
    confidence_score: float = 0.0
    expected_value: float = 0.0
    category: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class EngagementMetric:
    metric_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    metric_type: str = ""
    metric_value: float = 0.0
    measurement_date: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GameElement:
    element_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    element_type: str = ""  # badge, achievement, streak, challenge
    name: str = ""
    description: str = ""
    points_value: int = 0
    is_unlocked: bool = False
    unlocked_at: Optional[datetime] = None
    progress: float = 0.0
    target_value: float = 100.0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SocialActivity:
    activity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    activity_type: str = ""  # share, refer, review, like
    content: str = ""
    platform: str = ""
    engagement_points: int = 0
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)