from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random

from ..models.analytics import GameElement, SocialActivity, EngagementMetric
from ...shared.event_store import EventStore
from ...shared.logging import get_logger

class GamificationService:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.logger = get_logger(__name__)
        self.customer_game_elements: Dict[str, List[GameElement]] = {}
        self.social_activities: Dict[str, List[SocialActivity]] = {}

    def initialize_customer_gamification(self, customer_id: str) -> Dict[str, Any]:
        """Initialize gamification elements for a new customer"""
        try:
            game_elements = []
            
            # Create initial badges
            starter_badges = [
                {
                    "element_type": "badge",
                    "name": "Welcome Warrior",
                    "description": "Complete your first transaction",
                    "points_value": 50,
                    "target_value": 1
                },
                {
                    "element_type": "badge", 
                    "name": "Spending Streak",
                    "description": "Make transactions for 7 consecutive days",
                    "points_value": 200,
                    "target_value": 7
                },
                {
                    "element_type": "achievement",
                    "name": "Big Spender",
                    "description": "Spend ₹10,000 in a single transaction",
                    "points_value": 500,
                    "target_value": 10000
                },
                {
                    "element_type": "challenge",
                    "name": "Monthly Explorer",
                    "description": "Shop in 5 different categories this month",
                    "points_value": 300,
                    "target_value": 5
                }
            ]
            
            for badge_data in starter_badges:
                element = GameElement(
                    customer_id=customer_id,
                    element_type=badge_data["element_type"],
                    name=badge_data["name"],
                    description=badge_data["description"],
                    points_value=badge_data["points_value"],
                    target_value=badge_data["target_value"]
                )
                game_elements.append(element)
            
            self.customer_game_elements[customer_id] = game_elements
            
            return {
                "success": True,
                "customer_id": customer_id,
                "initialized_elements": len(game_elements),
                "elements": [
                    {
                        "element_id": e.element_id,
                        "type": e.element_type,
                        "name": e.name,
                        "description": e.description,
                        "points_value": e.points_value,
                        "progress": e.progress,
                        "target_value": e.target_value,
                        "is_unlocked": e.is_unlocked
                    } for e in game_elements
                ]
            }

        except Exception as e:
            self.logger.error(f"Error initializing gamification: {e}")
            return {"success": False, "error": str(e)}

    def update_progress(self, customer_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update gamification progress based on customer events"""
        try:
            if customer_id not in self.customer_game_elements:
                self.initialize_customer_gamification(customer_id)
            
            elements = self.customer_game_elements[customer_id]
            unlocked_elements = []
            
            for element in elements:
                if element.is_unlocked:
                    continue
                
                # Update progress based on event type
                progress_updated = self._update_element_progress(element, event_data)
                
                if progress_updated and element.progress >= element.target_value:
                    element.is_unlocked = True
                    element.unlocked_at = datetime.now()
                    unlocked_elements.append(element)
                    
                    # Publish achievement event
                    self.event_store.publish_event({
                        "event_type": "gamification_achievement_unlocked",
                        "customer_id": customer_id,
                        "element_id": element.element_id,
                        "element_type": element.element_type,
                        "name": element.name,
                        "points_value": element.points_value,
                        "timestamp": datetime.now().isoformat()
                    })
            
            return {
                "success": True,
                "customer_id": customer_id,
                "unlocked_elements": [
                    {
                        "element_id": e.element_id,
                        "type": e.element_type,
                        "name": e.name,
                        "points_value": e.points_value,
                        "unlocked_at": e.unlocked_at.isoformat()
                    } for e in unlocked_elements
                ],
                "total_unlocked": len(unlocked_elements)
            }

        except Exception as e:
            self.logger.error(f"Error updating gamification progress: {e}")
            return {"success": False, "error": str(e)}

    def _update_element_progress(self, element: GameElement, event_data: Dict[str, Any]) -> bool:
        """Update individual element progress"""
        event_type = event_data.get("event_type", "")
        
        if element.element_type == "badge":
            if element.name == "Welcome Warrior" and event_type == "transaction_processed":
                element.progress = 1
                return True
            elif element.name == "Spending Streak" and event_type == "transaction_processed":
                # Simplified streak logic
                element.progress = min(element.progress + 1, element.target_value)
                return True
                
        elif element.element_type == "achievement":
            if element.name == "Big Spender" and event_type == "transaction_processed":
                amount = event_data.get("amount", 0)
                if amount >= element.target_value:
                    element.progress = element.target_value
                    return True
                    
        elif element.element_type == "challenge":
            if element.name == "Monthly Explorer" and event_type == "transaction_processed":
                # Track unique categories (simplified)
                element.progress = min(element.progress + 0.5, element.target_value)
                return True
        
        return False

    def get_customer_gamification_status(self, customer_id: str) -> Dict[str, Any]:
        """Get customer's gamification status"""
        try:
            if customer_id not in self.customer_game_elements:
                return {"success": False, "error": "Customer gamification not initialized"}
            
            elements = self.customer_game_elements[customer_id]
            
            unlocked_count = len([e for e in elements if e.is_unlocked])
            total_points_earned = sum(e.points_value for e in elements if e.is_unlocked)
            
            return {
                "success": True,
                "customer_id": customer_id,
                "summary": {
                    "total_elements": len(elements),
                    "unlocked_elements": unlocked_count,
                    "completion_rate": (unlocked_count / len(elements)) * 100,
                    "total_points_earned": total_points_earned
                },
                "elements": [
                    {
                        "element_id": e.element_id,
                        "type": e.element_type,
                        "name": e.name,
                        "description": e.description,
                        "points_value": e.points_value,
                        "progress": e.progress,
                        "target_value": e.target_value,
                        "progress_percentage": (e.progress / e.target_value) * 100,
                        "is_unlocked": e.is_unlocked,
                        "unlocked_at": e.unlocked_at.isoformat() if e.unlocked_at else None
                    } for e in elements
                ]
            }

        except Exception as e:
            self.logger.error(f"Error getting gamification status: {e}")
            return {"success": False, "error": str(e)}

    def record_social_activity(self, customer_id: str, activity_type: str, 
                             content: str, platform: str) -> Dict[str, Any]:
        """Record social engagement activity"""
        try:
            # Calculate engagement points based on activity type
            points_map = {
                "share": 10,
                "refer": 50,
                "review": 25,
                "like": 5,
                "comment": 15
            }
            
            engagement_points = points_map.get(activity_type, 0)
            
            activity = SocialActivity(
                customer_id=customer_id,
                activity_type=activity_type,
                content=content,
                platform=platform,
                engagement_points=engagement_points,
                is_verified=True  # Simplified verification
            )
            
            if customer_id not in self.social_activities:
                self.social_activities[customer_id] = []
            
            self.social_activities[customer_id].append(activity)
            
            # Publish social engagement event
            self.event_store.publish_event({
                "event_type": "social_engagement_recorded",
                "customer_id": customer_id,
                "activity_id": activity.activity_id,
                "activity_type": activity_type,
                "platform": platform,
                "engagement_points": engagement_points,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "activity_id": activity.activity_id,
                "engagement_points": engagement_points,
                "total_social_points": sum(a.engagement_points for a in self.social_activities[customer_id])
            }

        except Exception as e:
            self.logger.error(f"Error recording social activity: {e}")
            return {"success": False, "error": str(e)}

    def get_leaderboard(self, period: str = "monthly") -> Dict[str, Any]:
        """Get gamification leaderboard"""
        try:
            # Calculate scores for all customers
            customer_scores = {}
            
            for customer_id, elements in self.customer_game_elements.items():
                gamification_points = sum(e.points_value for e in elements if e.is_unlocked)
                social_points = sum(a.engagement_points for a in self.social_activities.get(customer_id, []))
                total_score = gamification_points + social_points
                
                customer_scores[customer_id] = {
                    "customer_id": customer_id,
                    "gamification_points": gamification_points,
                    "social_points": social_points,
                    "total_score": total_score,
                    "unlocked_achievements": len([e for e in elements if e.is_unlocked])
                }
            
            # Sort by total score
            leaderboard = sorted(customer_scores.values(), 
                               key=lambda x: x["total_score"], reverse=True)
            
            # Add rankings
            for i, entry in enumerate(leaderboard):
                entry["rank"] = i + 1
            
            return {
                "success": True,
                "period": period,
                "total_participants": len(leaderboard),
                "leaderboard": leaderboard[:10],  # Top 10
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error generating leaderboard: {e}")
            return {"success": False, "error": str(e)}

    def create_seasonal_challenge(self, challenge_name: str, description: str, 
                                target_value: float, points_value: int, 
                                duration_days: int = 30) -> Dict[str, Any]:
        """Create a seasonal challenge for all customers"""
        try:
            challenge_id = f"seasonal_{datetime.now().strftime('%Y%m%d')}_{random.randint(1000, 9999)}"
            
            # Add challenge to all existing customers
            customers_updated = 0
            for customer_id in self.customer_game_elements.keys():
                challenge = GameElement(
                    customer_id=customer_id,
                    element_type="seasonal_challenge",
                    name=challenge_name,
                    description=description,
                    points_value=points_value,
                    target_value=target_value
                )
                challenge.metadata = {
                    "challenge_id": challenge_id,
                    "expires_at": (datetime.now() + timedelta(days=duration_days)).isoformat()
                }
                
                self.customer_game_elements[customer_id].append(challenge)
                customers_updated += 1
            
            return {
                "success": True,
                "challenge_id": challenge_id,
                "challenge_name": challenge_name,
                "customers_updated": customers_updated,
                "duration_days": duration_days,
                "expires_at": (datetime.now() + timedelta(days=duration_days)).isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error creating seasonal challenge: {e}")
            return {"success": False, "error": str(e)}