from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random

from ..models.analytics import Recommendation, RecommendationType, CustomerAnalytics
from ...shared.event_store import EventStore
from ...shared.logging import get_logger

class RecommendationService:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.logger = get_logger(__name__)
        self.recommendations: Dict[str, List[Recommendation]] = {}

    def generate_recommendations(self, customer_id: str, analytics: CustomerAnalytics) -> Dict[str, Any]:
        """Generate personalized recommendations"""
        try:
            recommendations = []
            
            # Product recommendations based on spending patterns
            product_recs = self._generate_product_recommendations(customer_id, analytics)
            recommendations.extend(product_recs)
            
            # Redemption recommendations
            redemption_recs = self._generate_redemption_recommendations(customer_id, analytics)
            recommendations.extend(redemption_recs)
            
            # Category recommendations
            category_recs = self._generate_category_recommendations(customer_id, analytics)
            recommendations.extend(category_recs)
            
            # Offer recommendations
            offer_recs = self._generate_offer_recommendations(customer_id, analytics)
            recommendations.extend(offer_recs)
            
            # Store recommendations
            self.recommendations[customer_id] = recommendations
            
            return {
                "success": True,
                "customer_id": customer_id,
                "total_recommendations": len(recommendations),
                "recommendations": [
                    {
                        "recommendation_id": r.recommendation_id,
                        "type": r.recommendation_type.value,
                        "title": r.title,
                        "description": r.description,
                        "confidence_score": r.confidence_score,
                        "expected_value": r.expected_value,
                        "category": r.category,
                        "expires_at": r.expires_at.isoformat() if r.expires_at else None
                    } for r in recommendations
                ]
            }

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return {"success": False, "error": str(e)}

    def _generate_product_recommendations(self, customer_id: str, analytics: CustomerAnalytics) -> List[Recommendation]:
        """Generate product recommendations based on spending patterns"""
        recommendations = []
        
        # High-value customer recommendations
        if analytics.avg_transaction_value > 2000:
            recommendations.append(Recommendation(
                customer_id=customer_id,
                recommendation_type=RecommendationType.PRODUCT,
                title="Premium Electronics",
                description="Exclusive premium electronics with bonus points",
                confidence_score=0.85,
                expected_value=analytics.avg_transaction_value * 0.1,
                category="electronics",
                expires_at=datetime.now() + timedelta(days=30)
            ))
        
        # Category-based recommendations
        for category in analytics.favorite_categories[:2]:
            recommendations.append(Recommendation(
                customer_id=customer_id,
                recommendation_type=RecommendationType.PRODUCT,
                title=f"Trending {category.title()} Products",
                description=f"Popular {category} items with extra rewards",
                confidence_score=0.75,
                expected_value=analytics.avg_transaction_value * 0.05,
                category=category,
                expires_at=datetime.now() + timedelta(days=15)
            ))
        
        return recommendations

    def _generate_redemption_recommendations(self, customer_id: str, analytics: CustomerAnalytics) -> List[Recommendation]:
        """Generate redemption recommendations"""
        recommendations = []
        
        # Points balance based recommendations
        available_points = analytics.total_points_earned - analytics.total_points_redeemed
        
        if available_points >= 1000:
            recommendations.append(Recommendation(
                customer_id=customer_id,
                recommendation_type=RecommendationType.REDEMPTION,
                title="Cashback Opportunity",
                description=f"Convert {min(available_points, 2000)} points to cashback",
                confidence_score=0.9,
                expected_value=min(available_points, 2000) * 0.5,
                category="cashback",
                expires_at=datetime.now() + timedelta(days=60)
            ))
        
        # Tier-based redemption recommendations
        if analytics.current_tier in ["gold", "platinum"]:
            recommendations.append(Recommendation(
                customer_id=customer_id,
                recommendation_type=RecommendationType.REDEMPTION,
                title="Exclusive Travel Deals",
                description="Premium travel bookings with your tier benefits",
                confidence_score=0.8,
                expected_value=5000.0,
                category="travel",
                expires_at=datetime.now() + timedelta(days=45)
            ))
        
        return recommendations

    def _generate_category_recommendations(self, customer_id: str, analytics: CustomerAnalytics) -> List[Recommendation]:
        """Generate category-based recommendations"""
        recommendations = []
        
        # Suggest new categories based on profile
        all_categories = ["dining", "grocery", "fuel", "shopping", "travel", "entertainment"]
        unexplored_categories = [cat for cat in all_categories if cat not in analytics.favorite_categories]
        
        for category in unexplored_categories[:2]:
            recommendations.append(Recommendation(
                customer_id=customer_id,
                recommendation_type=RecommendationType.CATEGORY,
                title=f"Explore {category.title()} Rewards",
                description=f"Earn bonus points on {category} purchases this month",
                confidence_score=0.6,
                expected_value=500.0,
                category=category,
                expires_at=datetime.now() + timedelta(days=30)
            ))
        
        return recommendations

    def _generate_offer_recommendations(self, customer_id: str, analytics: CustomerAnalytics) -> List[Recommendation]:
        """Generate personalized offer recommendations"""
        recommendations = []
        
        # Engagement-based offers
        if analytics.engagement_score < 50:
            recommendations.append(Recommendation(
                customer_id=customer_id,
                recommendation_type=RecommendationType.OFFER,
                title="Welcome Back Bonus",
                description="Get 2x points on your next 3 transactions",
                confidence_score=0.95,
                expected_value=analytics.avg_transaction_value * 0.2,
                category="bonus",
                expires_at=datetime.now() + timedelta(days=14)
            ))
        
        # Tier advancement offers
        tier_thresholds = {"bronze": 50000, "silver": 200000, "gold": 500000}
        current_threshold = tier_thresholds.get(analytics.current_tier, 0)
        next_tier_spending = current_threshold - analytics.total_spending
        
        if 0 < next_tier_spending <= 10000:
            recommendations.append(Recommendation(
                customer_id=customer_id,
                recommendation_type=RecommendationType.OFFER,
                title="Tier Upgrade Opportunity",
                description=f"Spend ₹{next_tier_spending:.0f} more to reach the next tier",
                confidence_score=0.85,
                expected_value=next_tier_spending * 0.1,
                category="tier_upgrade",
                expires_at=datetime.now() + timedelta(days=30)
            ))
        
        return recommendations

    def get_customer_recommendations(self, customer_id: str, active_only: bool = True) -> Dict[str, Any]:
        """Get recommendations for a customer"""
        try:
            customer_recs = self.recommendations.get(customer_id, [])
            
            if active_only:
                customer_recs = [r for r in customer_recs if r.is_active and 
                               (not r.expires_at or r.expires_at > datetime.now())]
            
            return {
                "success": True,
                "customer_id": customer_id,
                "recommendations": [
                    {
                        "recommendation_id": r.recommendation_id,
                        "type": r.recommendation_type.value,
                        "title": r.title,
                        "description": r.description,
                        "confidence_score": r.confidence_score,
                        "expected_value": r.expected_value,
                        "category": r.category,
                        "is_active": r.is_active,
                        "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                        "created_at": r.created_at.isoformat()
                    } for r in customer_recs
                ]
            }

        except Exception as e:
            self.logger.error(f"Error getting customer recommendations: {e}")
            return {"success": False, "error": str(e)}

    def mark_recommendation_used(self, recommendation_id: str) -> Dict[str, Any]:
        """Mark a recommendation as used"""
        try:
            for customer_recs in self.recommendations.values():
                for rec in customer_recs:
                    if rec.recommendation_id == recommendation_id:
                        rec.is_active = False
                        rec.metadata["used_at"] = datetime.now().isoformat()
                        
                        return {
                            "success": True,
                            "recommendation_id": recommendation_id,
                            "status": "marked_as_used"
                        }
            
            return {"success": False, "error": "Recommendation not found"}

        except Exception as e:
            self.logger.error(f"Error marking recommendation as used: {e}")
            return {"success": False, "error": str(e)}

    def get_recommendation_performance(self) -> Dict[str, Any]:
        """Get recommendation system performance metrics"""
        try:
            total_recommendations = 0
            used_recommendations = 0
            total_expected_value = 0.0
            
            for customer_recs in self.recommendations.values():
                for rec in customer_recs:
                    total_recommendations += 1
                    total_expected_value += rec.expected_value
                    
                    if not rec.is_active and rec.metadata.get("used_at"):
                        used_recommendations += 1
            
            usage_rate = (used_recommendations / max(1, total_recommendations)) * 100
            
            return {
                "success": True,
                "performance_metrics": {
                    "total_recommendations": total_recommendations,
                    "used_recommendations": used_recommendations,
                    "usage_rate_percent": usage_rate,
                    "total_expected_value": total_expected_value,
                    "avg_expected_value": total_expected_value / max(1, total_recommendations)
                },
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting recommendation performance: {e}")
            return {"success": False, "error": str(e)}