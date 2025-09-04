from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import statistics

from ..models.analytics import CustomerAnalytics, SpendingPattern, EngagementMetric
from ...shared.event_store import EventStore
from ...shared.logging import get_logger

class AnalyticsEngine:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.logger = get_logger(__name__)
        self.customer_analytics: Dict[str, CustomerAnalytics] = {}

    def analyze_customer_behavior(self, customer_id: str) -> Dict[str, Any]:
        """Analyze customer behavior and generate insights"""
        try:
            # Get customer events
            events = self.event_store.get_customer_events(customer_id)
            
            if not events:
                return {"success": False, "error": "No customer data found"}

            # Calculate analytics
            analytics = self._calculate_customer_analytics(customer_id, events)
            self.customer_analytics[customer_id] = analytics

            # Generate insights
            insights = self._generate_insights(analytics, events)

            return {
                "success": True,
                "customer_id": customer_id,
                "analytics": {
                    "total_transactions": analytics.total_transactions,
                    "total_spending": analytics.total_spending,
                    "total_points_earned": analytics.total_points_earned,
                    "total_points_redeemed": analytics.total_points_redeemed,
                    "current_tier": analytics.current_tier,
                    "favorite_categories": analytics.favorite_categories,
                    "avg_transaction_value": analytics.avg_transaction_value,
                    "engagement_score": analytics.engagement_score,
                    "churn_risk": analytics.churn_risk,
                    "lifetime_value": analytics.lifetime_value
                },
                "insights": insights
            }

        except Exception as e:
            self.logger.error(f"Error analyzing customer behavior: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_customer_analytics(self, customer_id: str, events: List[Dict]) -> CustomerAnalytics:
        """Calculate comprehensive customer analytics"""
        analytics = CustomerAnalytics(customer_id=customer_id)
        
        transaction_events = [e for e in events if e.get("event_type") == "transaction_processed"]
        redemption_events = [e for e in events if e.get("event_type") in ["redemption_initiated", "cashback_completed"]]
        
        if transaction_events:
            analytics.total_transactions = len(transaction_events)
            analytics.total_spending = sum(e.get("amount", 0) for e in transaction_events)
            analytics.total_points_earned = sum(e.get("points_earned", 0) for e in transaction_events)
            analytics.avg_transaction_value = analytics.total_spending / analytics.total_transactions
            
            # Get last transaction date
            last_transaction = max(transaction_events, key=lambda x: x.get("timestamp", ""))
            analytics.last_transaction_date = datetime.fromisoformat(last_transaction["timestamp"])
            
            # Calculate favorite categories
            categories = [e.get("category", "other") for e in transaction_events]
            category_counts = {}
            for cat in categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            analytics.favorite_categories = sorted(category_counts.keys(), 
                                                 key=lambda x: category_counts[x], reverse=True)[:3]

        if redemption_events:
            analytics.total_points_redeemed = sum(e.get("points_used", 0) for e in redemption_events)

        # Calculate engagement score (0-100)
        analytics.engagement_score = self._calculate_engagement_score(events)
        
        # Calculate churn risk
        analytics.churn_risk = self._calculate_churn_risk(analytics)
        
        # Calculate lifetime value
        analytics.lifetime_value = analytics.total_spending * 0.1  # 10% margin assumption

        return analytics

    def _calculate_engagement_score(self, events: List[Dict]) -> float:
        """Calculate customer engagement score"""
        if not events:
            return 0.0
        
        # Recent activity weight
        recent_events = [e for e in events 
                        if datetime.fromisoformat(e.get("timestamp", "2020-01-01")) > 
                        datetime.now() - timedelta(days=30)]
        
        # Score components
        transaction_score = min(len(recent_events) * 5, 40)  # Max 40 points
        variety_score = len(set(e.get("event_type") for e in events)) * 10  # Max varies
        frequency_score = min(len(events) / 10, 30)  # Max 30 points
        
        total_score = transaction_score + variety_score + frequency_score
        return min(total_score, 100.0)

    def _calculate_churn_risk(self, analytics: CustomerAnalytics) -> str:
        """Calculate customer churn risk"""
        if not analytics.last_transaction_date:
            return "high"
        
        days_since_last = (datetime.now() - analytics.last_transaction_date).days
        
        if days_since_last > 90:
            return "high"
        elif days_since_last > 30:
            return "medium"
        else:
            return "low"

    def _generate_insights(self, analytics: CustomerAnalytics, events: List[Dict]) -> List[Dict[str, Any]]:
        """Generate actionable insights"""
        insights = []
        
        # Spending insights
        if analytics.avg_transaction_value > 1000:
            insights.append({
                "type": "spending_pattern",
                "title": "High-Value Customer",
                "description": f"Average transaction value of ₹{analytics.avg_transaction_value:.2f} indicates premium spending behavior",
                "recommendation": "Offer premium tier benefits and exclusive experiences"
            })
        
        # Engagement insights
        if analytics.engagement_score < 30:
            insights.append({
                "type": "engagement",
                "title": "Low Engagement",
                "description": "Customer shows low engagement with the program",
                "recommendation": "Send personalized offers and engagement campaigns"
            })
        
        # Churn risk insights
        if analytics.churn_risk == "high":
            insights.append({
                "type": "retention",
                "title": "Churn Risk",
                "description": "Customer hasn't transacted recently and may be at risk of churning",
                "recommendation": "Immediate retention campaign with attractive offers"
            })
        
        return insights

    def generate_spending_patterns(self, customer_id: str) -> Dict[str, Any]:
        """Generate spending pattern analysis"""
        try:
            events = self.event_store.get_customer_events(customer_id)
            transaction_events = [e for e in events if e.get("event_type") == "transaction_processed"]
            
            if not transaction_events:
                return {"success": False, "error": "No transaction data found"}

            patterns = []
            
            # Group by category
            category_data = {}
            for event in transaction_events:
                category = event.get("category", "other")
                if category not in category_data:
                    category_data[category] = []
                category_data[category].append({
                    "amount": event.get("amount", 0),
                    "date": datetime.fromisoformat(event.get("timestamp", "2020-01-01"))
                })

            # Analyze each category
            for category, transactions in category_data.items():
                monthly_spending = sum(t["amount"] for t in transactions) / max(1, len(set(t["date"].month for t in transactions)))
                
                pattern = SpendingPattern(
                    customer_id=customer_id,
                    category=category,
                    monthly_spending=monthly_spending,
                    transaction_frequency=len(transactions),
                    growth_rate=self._calculate_growth_rate(transactions),
                    prediction_confidence=0.8 if len(transactions) > 5 else 0.5
                )
                patterns.append(pattern)

            return {
                "success": True,
                "customer_id": customer_id,
                "patterns": [
                    {
                        "category": p.category,
                        "monthly_spending": p.monthly_spending,
                        "transaction_frequency": p.transaction_frequency,
                        "growth_rate": p.growth_rate,
                        "prediction_confidence": p.prediction_confidence
                    } for p in patterns
                ]
            }

        except Exception as e:
            self.logger.error(f"Error generating spending patterns: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_growth_rate(self, transactions: List[Dict]) -> float:
        """Calculate spending growth rate"""
        if len(transactions) < 2:
            return 0.0
        
        # Sort by date
        sorted_transactions = sorted(transactions, key=lambda x: x["date"])
        
        # Calculate monthly totals
        monthly_totals = {}
        for t in sorted_transactions:
            month_key = f"{t['date'].year}-{t['date'].month:02d}"
            monthly_totals[month_key] = monthly_totals.get(month_key, 0) + t["amount"]
        
        if len(monthly_totals) < 2:
            return 0.0
        
        # Calculate growth rate
        months = sorted(monthly_totals.keys())
        first_month = monthly_totals[months[0]]
        last_month = monthly_totals[months[-1]]
        
        if first_month == 0:
            return 0.0
        
        return ((last_month - first_month) / first_month) * 100

    def get_program_analytics(self) -> Dict[str, Any]:
        """Get overall program analytics"""
        try:
            all_events = self.event_store.get_all_events()
            
            # Calculate program metrics
            total_customers = len(set(e.get("customer_id") for e in all_events if e.get("customer_id")))
            total_transactions = len([e for e in all_events if e.get("event_type") == "transaction_processed"])
            total_revenue = sum(e.get("amount", 0) for e in all_events if e.get("event_type") == "transaction_processed")
            total_points_issued = sum(e.get("points_earned", 0) for e in all_events if e.get("event_type") == "transaction_processed")
            total_redemptions = len([e for e in all_events if e.get("event_type") == "redemption_initiated"])

            # Calculate engagement metrics
            avg_engagement = statistics.mean([a.engagement_score for a in self.customer_analytics.values()]) if self.customer_analytics else 0

            return {
                "success": True,
                "program_metrics": {
                    "total_customers": total_customers,
                    "total_transactions": total_transactions,
                    "total_revenue": total_revenue,
                    "total_points_issued": total_points_issued,
                    "total_redemptions": total_redemptions,
                    "avg_engagement_score": avg_engagement,
                    "redemption_rate": (total_redemptions / max(1, total_transactions)) * 100
                },
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting program analytics: {e}")
            return {"success": False, "error": str(e)}