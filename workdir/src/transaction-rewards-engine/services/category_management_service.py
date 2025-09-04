"""Category management service for multipliers and campaigns."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.base_service import BaseService
from shared.event_store import EventStore
from shared.config import Config
from ..repositories.transaction_repository import CategoryMultiplierRepository
from ..models.transaction import CategoryMultiplier
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid

class CategoryManagementService(BaseService):
    def __init__(self, event_store: EventStore, category_repo: CategoryMultiplierRepository):
        super().__init__("TRANSACTION-ENGINE", event_store)
        self.category_repo = category_repo
        
        # Initialize default multipliers if not exists
        self.category_repo.initialize_default_multipliers()
    
    def get_category_multipliers(self) -> Dict[str, Any]:
        """Get all category multipliers."""
        try:
            multipliers = self.category_repo.get_active_multipliers()
            
            return {
                'success': True,
                'multipliers': [m.to_dict() for m in multipliers],
                'total_count': len(multipliers)
            }
            
        except Exception as e:
            self.logger.log_error(None, 'GET_CATEGORY_MULTIPLIERS', str(e))
            return {
                'success': False,
                'error': 'Failed to retrieve category multipliers'
            }
    
    def update_category_multiplier(self, category: str, multiplier: float, 
                                 admin_user: str = 'SYSTEM') -> Dict[str, Any]:
        """Update multiplier for a category."""
        try:
            if multiplier < 1.0 or multiplier > 5.0:
                return {
                    'success': False,
                    'error': 'Multiplier must be between 1.0 and 5.0'
                }
            
            # Get existing multiplier or create new
            existing = self.category_repo.find_multiplier_by_category(category)
            if existing:
                old_multiplier = existing.multiplier
                existing.multiplier = multiplier
                existing.active = True
                self.category_repo.save_multiplier(existing)
            else:
                new_multiplier = CategoryMultiplier(
                    category=category,
                    multiplier=multiplier
                )
                self.category_repo.save_multiplier(new_multiplier)
                old_multiplier = 1.0
            
            # Publish category multiplier updated event
            self.publish_event('CategoryMultiplierUpdated', category, {
                'category': category,
                'previous_multiplier': old_multiplier,
                'new_multiplier': multiplier,
                'updated_by': admin_user,
                'effective_date': datetime.now().isoformat()
            })
            
            self.logger.log_business_event('INFO', None, 'MULTIPLIER_UPDATE', 'SUCCESS',
                                         f'{admin_user} updated {category} category multiplier from {old_multiplier}x to {multiplier}x')
            
            return {
                'success': True,
                'category': category,
                'old_multiplier': old_multiplier,
                'new_multiplier': multiplier,
                'message': f'Category {category} multiplier updated to {multiplier}x'
            }
            
        except Exception as e:
            self.logger.log_error(None, 'UPDATE_CATEGORY_MULTIPLIER', str(e))
            return {
                'success': False,
                'error': 'Failed to update category multiplier'
            }
    
    def create_promotional_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a promotional campaign with temporary multipliers."""
        try:
            required_fields = ['category', 'multiplier', 'start_date', 'end_date']
            self.validate_required_fields(campaign_data, required_fields)
            
            campaign_id = str(uuid.uuid4())
            
            # Create promotional multiplier
            promo_multiplier = CategoryMultiplier(
                category=campaign_data['category'],
                multiplier=float(campaign_data['multiplier']),
                start_date=campaign_data['start_date'],
                end_date=campaign_data['end_date'],
                campaign_id=campaign_id
            )
            
            self.category_repo.save_multiplier(promo_multiplier)
            
            # Publish campaign created event
            self.publish_event('PromotionalCampaignCreated', campaign_id, {
                'campaign_id': campaign_id,
                'category': campaign_data['category'],
                'multiplier': campaign_data['multiplier'],
                'start_date': campaign_data['start_date'],
                'end_date': campaign_data['end_date'],
                'created_by': campaign_data.get('created_by', 'SYSTEM')
            })
            
            self.logger.log_business_event('INFO', None, 'CAMPAIGN_CREATED', 'SUCCESS',
                                         f'Created promotional campaign for {campaign_data["category"]} category with {campaign_data["multiplier"]}x multiplier')
            
            return {
                'success': True,
                'campaign_id': campaign_id,
                'message': f'Promotional campaign created for {campaign_data["category"]} category'
            }
            
        except ValueError as e:
            self.logger.log_error(None, 'CREATE_CAMPAIGN', str(e))
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            self.logger.log_error(None, 'CREATE_CAMPAIGN', str(e))
            return {
                'success': False,
                'error': 'Failed to create promotional campaign'
            }
    
    def get_spending_insights(self, customer_id: str) -> Dict[str, Any]:
        """Get customer spending insights by category."""
        try:
            from ..repositories.transaction_repository import TransactionRepository
            transaction_repo = TransactionRepository()
            
            transactions = transaction_repo.find_transactions_by_customer(customer_id)
            
            # Aggregate spending by category
            category_spending = {}
            total_spending = 0.0
            total_points = 0
            
            for transaction in transactions:
                if transaction.status == 'COMPLETED':
                    category = transaction.category
                    amount = transaction.amount
                    points = transaction.points_earned
                    
                    if category not in category_spending:
                        category_spending[category] = {
                            'total_amount': 0.0,
                            'total_points': 0,
                            'transaction_count': 0,
                            'avg_multiplier': 0.0
                        }
                    
                    category_spending[category]['total_amount'] += amount
                    category_spending[category]['total_points'] += points
                    category_spending[category]['transaction_count'] += 1
                    category_spending[category]['avg_multiplier'] = (
                        category_spending[category]['total_points'] / 
                        category_spending[category]['total_amount']
                    )
                    
                    total_spending += amount
                    total_points += points
            
            # Calculate percentages and recommendations
            insights = []
            for category, data in category_spending.items():
                percentage = (data['total_amount'] / total_spending * 100) if total_spending > 0 else 0
                current_multiplier = self._get_category_multiplier(category)
                
                insights.append({
                    'category': category,
                    'total_spending': data['total_amount'],
                    'total_points': data['total_points'],
                    'transaction_count': data['transaction_count'],
                    'spending_percentage': round(percentage, 2),
                    'current_multiplier': current_multiplier,
                    'avg_transaction_size': data['total_amount'] / data['transaction_count']
                })
            
            # Sort by spending amount
            insights.sort(key=lambda x: x['total_spending'], reverse=True)
            
            return {
                'success': True,
                'customer_id': customer_id,
                'spending_insights': {
                    'total_spending': total_spending,
                    'total_points_earned': total_points,
                    'category_breakdown': insights,
                    'recommendations': self._generate_recommendations(insights)
                }
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'GET_SPENDING_INSIGHTS', str(e))
            return {
                'success': False,
                'error': 'Failed to generate spending insights'
            }
    
    def _get_category_multiplier(self, category: str) -> float:
        """Get current multiplier for a category."""
        multiplier_obj = self.category_repo.find_multiplier_by_category(category)
        if multiplier_obj and multiplier_obj.is_active():
            return multiplier_obj.multiplier
        
        return Config.DEFAULT_CATEGORY_MULTIPLIERS.get(category, 1.0)
    
    def _generate_recommendations(self, insights: List[Dict[str, Any]]) -> List[str]:
        """Generate spending recommendations based on insights."""
        recommendations = []
        
        # Find categories with high multipliers but low spending
        high_multiplier_categories = [
            insight for insight in insights 
            if insight['current_multiplier'] >= 2.0 and insight['spending_percentage'] < 20
        ]
        
        for category_insight in high_multiplier_categories[:2]:  # Top 2 recommendations
            recommendations.append(
                f"Consider increasing spending in {category_insight['category']} category "
                f"({category_insight['current_multiplier']}x multiplier) to maximize rewards"
            )
        
        # Recommend tier advancement if close
        total_spending = sum(insight['total_spending'] for insight in insights)
        next_tier_threshold = None
        
        if total_spending < Config.TIER_THRESHOLDS['SILVER']:
            next_tier_threshold = Config.TIER_THRESHOLDS['SILVER']
            next_tier = 'SILVER'
        elif total_spending < Config.TIER_THRESHOLDS['GOLD']:
            next_tier_threshold = Config.TIER_THRESHOLDS['GOLD']
            next_tier = 'GOLD'
        elif total_spending < Config.TIER_THRESHOLDS['PLATINUM']:
            next_tier_threshold = Config.TIER_THRESHOLDS['PLATINUM']
            next_tier = 'PLATINUM'
        
        if next_tier_threshold:
            remaining = next_tier_threshold - total_spending
            if remaining <= next_tier_threshold * 0.2:  # Within 20% of next tier
                recommendations.append(
                    f"You're only ₹{remaining:,.0f} away from {next_tier} tier! "
                    f"Reach it for {Config.get_tier_multiplier(next_tier)}x base multiplier"
                )
        
        return recommendations