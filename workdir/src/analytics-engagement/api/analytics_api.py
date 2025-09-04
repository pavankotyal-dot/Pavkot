from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel

from ..services.analytics_engine import AnalyticsEngine
from ..services.recommendation_service import RecommendationService
from ..services.gamification_service import GamificationService
from ...shared.event_store import EventStore
from ...shared.logging import get_logger

# Pydantic models
class SocialActivityRequest(BaseModel):
    customer_id: str
    activity_type: str
    content: str
    platform: str

class SeasonalChallengeRequest(BaseModel):
    challenge_name: str
    description: str
    target_value: float
    points_value: int
    duration_days: int = 30

# Initialize services
event_store = EventStore()
analytics_engine = AnalyticsEngine(event_store)
recommendation_service = RecommendationService(event_store)
gamification_service = GamificationService(event_store)

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Engagement"])
logger = get_logger(__name__)

# Analytics endpoints
@router.get("/customer/{customer_id}/behavior")
async def analyze_customer_behavior(customer_id: str):
    """Analyze customer behavior and generate insights"""
    try:
        result = analytics_engine.analyze_customer_behavior(customer_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error analyzing customer behavior: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer/{customer_id}/spending-patterns")
async def get_spending_patterns(customer_id: str):
    """Get customer spending patterns"""
    try:
        result = analytics_engine.generate_spending_patterns(customer_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting spending patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/program/metrics")
async def get_program_analytics():
    """Get overall program analytics"""
    try:
        result = analytics_engine.get_program_analytics()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting program analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Recommendation endpoints
@router.get("/customer/{customer_id}/recommendations")
async def get_customer_recommendations(customer_id: str, active_only: bool = True):
    """Get personalized recommendations for customer"""
    try:
        # First analyze customer to generate fresh recommendations
        analytics_result = analytics_engine.analyze_customer_behavior(customer_id)
        
        if analytics_result["success"]:
            analytics_data = analytics_result["analytics"]
            from ..models.analytics import CustomerAnalytics
            
            # Create analytics object (simplified)
            customer_analytics = CustomerAnalytics(
                customer_id=customer_id,
                total_transactions=analytics_data["total_transactions"],
                total_spending=analytics_data["total_spending"],
                total_points_earned=analytics_data["total_points_earned"],
                total_points_redeemed=analytics_data["total_points_redeemed"],
                current_tier=analytics_data["current_tier"],
                favorite_categories=analytics_data["favorite_categories"],
                avg_transaction_value=analytics_data["avg_transaction_value"],
                engagement_score=analytics_data["engagement_score"],
                churn_risk=analytics_data["churn_risk"],
                lifetime_value=analytics_data["lifetime_value"]
            )
            
            # Generate recommendations
            rec_result = recommendation_service.generate_recommendations(customer_id, customer_analytics)
            
            if rec_result["success"]:
                return rec_result
            else:
                raise HTTPException(status_code=500, detail=rec_result["error"])
        else:
            # Return existing recommendations if analytics fails
            result = recommendation_service.get_customer_recommendations(customer_id, active_only)
            
            if result["success"]:
                return result
            else:
                raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations/{recommendation_id}/use")
async def mark_recommendation_used(recommendation_id: str):
    """Mark a recommendation as used"""
    try:
        result = recommendation_service.mark_recommendation_used(recommendation_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error marking recommendation as used: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/performance")
async def get_recommendation_performance():
    """Get recommendation system performance metrics"""
    try:
        result = recommendation_service.get_recommendation_performance()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting recommendation performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Gamification endpoints
@router.post("/customer/{customer_id}/gamification/initialize")
async def initialize_customer_gamification(customer_id: str):
    """Initialize gamification for a customer"""
    try:
        result = gamification_service.initialize_customer_gamification(customer_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error initializing gamification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customer/{customer_id}/gamification/status")
async def get_gamification_status(customer_id: str):
    """Get customer's gamification status"""
    try:
        result = gamification_service.get_customer_gamification_status(customer_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting gamification status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customer/{customer_id}/gamification/update")
async def update_gamification_progress(customer_id: str, event_data: Dict):
    """Update gamification progress based on customer activity"""
    try:
        result = gamification_service.update_progress(customer_id, event_data)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error updating gamification progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/social/activity")
async def record_social_activity(request: SocialActivityRequest):
    """Record social engagement activity"""
    try:
        result = gamification_service.record_social_activity(
            request.customer_id,
            request.activity_type,
            request.content,
            request.platform
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error recording social activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gamification/leaderboard")
async def get_leaderboard(period: str = "monthly"):
    """Get gamification leaderboard"""
    try:
        result = gamification_service.get_leaderboard(period)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gamification/seasonal-challenge")
async def create_seasonal_challenge(request: SeasonalChallengeRequest):
    """Create a seasonal challenge"""
    try:
        result = gamification_service.create_seasonal_challenge(
            request.challenge_name,
            request.description,
            request.target_value,
            request.points_value,
            request.duration_days
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error creating seasonal challenge: {e}")
        raise HTTPException(status_code=500, detail=str(e))