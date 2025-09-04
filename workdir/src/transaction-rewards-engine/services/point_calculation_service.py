"""Point calculation engine service."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.base_service import BaseService
from shared.event_store import EventStore
from shared.config import Config
from ..repositories.transaction_repository import PointBalanceRepository, CategoryMultiplierRepository, CustomerTierRepository
from typing import Dict, Any

class PointCalculationService(BaseService):
    def __init__(self, event_store: EventStore, point_repo: PointBalanceRepository,
                 category_repo: CategoryMultiplierRepository, tier_repo: CustomerTierRepository):
        super().__init__("TRANSACTION-ENGINE", event_store)
        self.point_repo = point_repo
        self.category_repo = category_repo
        self.tier_repo = tier_repo
    
    def calculate_points(self, customer_id: str, amount: float, category: str) -> Dict[str, Any]:
        """Calculate points for a transaction."""
        try:
            # Get category multiplier
            category_multiplier = self._get_category_multiplier(category)
            
            # Get tier multiplier
            tier_multiplier = self._get_tier_multiplier(customer_id)
            
            # Calculate base points (1 point per INR)
            base_points = int(amount * Config.POINTS_PER_INR)
            
            # Apply multipliers
            total_multiplier = category_multiplier * tier_multiplier
            final_points = int(base_points * total_multiplier)
            
            return {
                'success': True,
                'calculation': {
                    'base_amount': amount,
                    'base_points': base_points,
                    'category': category,
                    'category_multiplier': category_multiplier,
                    'tier_multiplier': tier_multiplier,
                    'total_multiplier': total_multiplier,
                    'final_points': final_points
                }
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'POINT_CALCULATION', str(e))
            return {
                'success': False,
                'error': 'Failed to calculate points'
            }
    
    def get_point_balance(self, customer_id: str) -> Dict[str, Any]:
        """Get customer point balance."""
        try:
            balance = self.point_repo.find_balance_by_customer(customer_id)
            if not balance:
                balance = self.point_repo.initialize_balance(customer_id)
            
            return {
                'success': True,
                'balance': {
                    'customer_id': customer_id,
                    'total_points': balance.total_points,
                    'lifetime_points_earned': balance.lifetime_points_earned,
                    'points_redeemed': balance.points_redeemed,
                    'last_updated': balance.last_updated,
                    'cashback_value': balance.total_points * Config.CASHBACK_RATE
                }
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'GET_POINT_BALANCE', str(e))
            return {
                'success': False,
                'error': 'Failed to retrieve point balance'
            }
    
    def validate_point_balance(self, customer_id: str, required_points: int) -> Dict[str, Any]:
        """Validate if customer has sufficient points for redemption."""
        try:
            balance = self.point_repo.find_balance_by_customer(customer_id)
            if not balance:
                return {
                    'success': False,
                    'valid': False,
                    'error': 'Customer point balance not found'
                }
            
            is_valid = balance.total_points >= required_points
            
            return {
                'success': True,
                'valid': is_valid,
                'current_balance': balance.total_points,
                'required_points': required_points,
                'shortfall': max(0, required_points - balance.total_points)
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'VALIDATE_POINT_BALANCE', str(e))
            return {
                'success': False,
                'error': 'Failed to validate point balance'
            }
    
    def deduct_points(self, customer_id: str, points: int, reason: str) -> Dict[str, Any]:
        """Deduct points from customer balance."""
        try:
            balance = self.point_repo.find_balance_by_customer(customer_id)
            if not balance:
                return {
                    'success': False,
                    'error': 'Customer point balance not found'
                }
            
            if not balance.deduct_points(points):
                return {
                    'success': False,
                    'error': 'Insufficient points for deduction'
                }
            
            self.point_repo.save_balance(balance)
            
            # Publish points deducted event
            self.publish_event('PointsDeducted', customer_id, {
                'customer_id': customer_id,
                'points_deducted': points,
                'reason': reason,
                'remaining_balance': balance.total_points
            })
            
            self.logger.log_business_event('INFO', customer_id, 'POINTS_DEDUCTED', 'SUCCESS',
                                         f'Deducted {points} points for {reason}. Remaining: {balance.total_points}')
            
            return {
                'success': True,
                'points_deducted': points,
                'remaining_balance': balance.total_points,
                'message': f'Successfully deducted {points} points'
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'DEDUCT_POINTS', str(e))
            return {
                'success': False,
                'error': 'Failed to deduct points'
            }
    
    def add_points(self, customer_id: str, points: int, reason: str) -> Dict[str, Any]:
        """Add points to customer balance (for adjustments/bonuses)."""
        try:
            balance = self.point_repo.find_balance_by_customer(customer_id)
            if not balance:
                balance = self.point_repo.initialize_balance(customer_id)
            
            balance.add_points(points)
            self.point_repo.save_balance(balance)
            
            # Publish points added event
            self.publish_event('PointsAdded', customer_id, {
                'customer_id': customer_id,
                'points_added': points,
                'reason': reason,
                'new_balance': balance.total_points
            })
            
            self.logger.log_business_event('INFO', customer_id, 'POINTS_ADDED', 'SUCCESS',
                                         f'Added {points} points for {reason}. New balance: {balance.total_points}')
            
            return {
                'success': True,
                'points_added': points,
                'new_balance': balance.total_points,
                'message': f'Successfully added {points} points'
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'ADD_POINTS', str(e))
            return {
                'success': False,
                'error': 'Failed to add points'
            }
    
    def _get_category_multiplier(self, category: str) -> float:
        """Get multiplier for spending category."""
        multiplier_obj = self.category_repo.find_multiplier_by_category(category)
        if multiplier_obj and multiplier_obj.is_active():
            return multiplier_obj.multiplier
        
        return Config.DEFAULT_CATEGORY_MULTIPLIERS.get(category, 1.0)
    
    def _get_tier_multiplier(self, customer_id: str) -> float:
        """Get tier-based multiplier for customer."""
        tier_obj = self.tier_repo.find_tier_by_customer(customer_id)
        if tier_obj:
            return Config.get_tier_multiplier(tier_obj.current_tier)
        
        return Config.get_tier_multiplier('BRONZE')