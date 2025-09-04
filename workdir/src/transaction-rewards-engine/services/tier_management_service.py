"""Tier management service."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.base_service import BaseService
from shared.event_store import EventStore
from shared.config import Config
from ..repositories.transaction_repository import CustomerTierRepository, TransactionRepository
from typing import Dict, Any
from datetime import datetime, timedelta

class TierManagementService(BaseService):
    def __init__(self, event_store: EventStore, tier_repo: CustomerTierRepository, 
                 transaction_repo: TransactionRepository):
        super().__init__("TRANSACTION-ENGINE", event_store)
        self.tier_repo = tier_repo
        self.transaction_repo = transaction_repo
    
    def get_customer_tier_status(self, customer_id: str) -> Dict[str, Any]:
        """Get customer tier status and progression information."""
        try:
            tier_obj = self.tier_repo.find_tier_by_customer(customer_id)
            if not tier_obj:
                tier_obj = self.tier_repo.initialize_tier(customer_id)
            
            # Calculate spending to next tier
            current_tier = tier_obj.current_tier
            next_tier_info = self._get_next_tier_info(current_tier, tier_obj.annual_spending)
            
            return {
                'success': True,
                'tier_status': {
                    'customer_id': customer_id,
                    'current_tier': current_tier,
                    'annual_spending': tier_obj.annual_spending,
                    'tier_start_date': tier_obj.tier_start_date,
                    'tier_multiplier': Config.get_tier_multiplier(current_tier),
                    'next_tier': next_tier_info,
                    'tier_benefits': self._get_tier_benefits(current_tier)
                }
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'GET_TIER_STATUS', str(e))
            return {
                'success': False,
                'error': 'Failed to retrieve tier status'
            }
    
    def check_tier_advancement(self, customer_id: str) -> Dict[str, Any]:
        """Check if customer qualifies for tier advancement."""
        try:
            tier_obj = self.tier_repo.find_tier_by_customer(customer_id)
            if not tier_obj:
                return {
                    'success': False,
                    'error': 'Customer tier information not found'
                }
            
            current_tier = tier_obj.current_tier
            new_tier = Config.get_tier_for_spending(tier_obj.annual_spending)
            
            if new_tier != current_tier:
                # Advance tier
                old_tier = current_tier
                tier_obj.update_tier(new_tier)
                self.tier_repo.save_tier(tier_obj)
                
                # Publish tier advancement event
                self.publish_event('TierAdvanced', customer_id, {
                    'customer_id': customer_id,
                    'previous_tier': old_tier,
                    'new_tier': new_tier,
                    'total_spending': tier_obj.annual_spending,
                    'advancement_date': tier_obj.tier_start_date
                })
                
                self.logger.log_tier_advancement(customer_id, old_tier, new_tier, tier_obj.annual_spending)
                
                return {
                    'success': True,
                    'tier_advanced': True,
                    'previous_tier': old_tier,
                    'new_tier': new_tier,
                    'message': f'Congratulations! You have been upgraded to {new_tier} tier!'
                }
            
            return {
                'success': True,
                'tier_advanced': False,
                'current_tier': current_tier,
                'message': 'No tier advancement at this time'
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'CHECK_TIER_ADVANCEMENT', str(e))
            return {
                'success': False,
                'error': 'Failed to check tier advancement'
            }
    
    def check_tier_maintenance(self, customer_id: str) -> Dict[str, Any]:
        """Check tier maintenance requirements and potential downgrades."""
        try:
            tier_obj = self.tier_repo.find_tier_by_customer(customer_id)
            if not tier_obj or tier_obj.current_tier == 'BRONZE':
                return {
                    'success': True,
                    'maintenance_required': False,
                    'message': 'Bronze tier has no maintenance requirements'
                }
            
            # Check if it's been a year since tier start
            tier_start = datetime.fromisoformat(tier_obj.tier_start_date)
            one_year_later = tier_start + timedelta(days=365)
            now = datetime.now()
            
            if now >= one_year_later:
                # Check if spending meets maintenance requirement
                current_threshold = Config.TIER_THRESHOLDS[tier_obj.current_tier]
                
                if tier_obj.annual_spending < current_threshold:
                    # Downgrade tier
                    new_tier = Config.get_tier_for_spending(tier_obj.annual_spending)
                    old_tier = tier_obj.current_tier
                    
                    tier_obj.update_tier(new_tier)
                    # Reset annual spending for new tier period
                    tier_obj.annual_spending = 0.0
                    self.tier_repo.save_tier(tier_obj)
                    
                    # Publish tier downgrade event
                    self.publish_event('TierDowngraded', customer_id, {
                        'customer_id': customer_id,
                        'previous_tier': old_tier,
                        'new_tier': new_tier,
                        'reason': 'Insufficient annual spending for tier maintenance',
                        'downgrade_date': tier_obj.tier_start_date
                    })
                    
                    self.logger.log_business_event('INFO', customer_id, 'TIER_DOWNGRADE', 'SUCCESS',
                                                 f'Customer downgraded from {old_tier} to {new_tier} due to insufficient spending')
                    
                    return {
                        'success': True,
                        'tier_downgraded': True,
                        'previous_tier': old_tier,
                        'new_tier': new_tier,
                        'reason': 'Insufficient annual spending for tier maintenance'
                    }
                else:
                    # Reset spending for new year
                    tier_obj.annual_spending = 0.0
                    tier_obj.tier_start_date = now.isoformat()
                    self.tier_repo.save_tier(tier_obj)
                    
                    return {
                        'success': True,
                        'tier_maintained': True,
                        'current_tier': tier_obj.current_tier,
                        'message': 'Tier successfully maintained for another year'
                    }
            
            # Calculate time remaining and spending needed
            days_remaining = (one_year_later - now).days
            spending_needed = max(0, current_threshold - tier_obj.annual_spending)
            
            return {
                'success': True,
                'maintenance_required': True,
                'current_tier': tier_obj.current_tier,
                'days_remaining': days_remaining,
                'spending_needed': spending_needed,
                'current_spending': tier_obj.annual_spending,
                'required_spending': current_threshold
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'CHECK_TIER_MAINTENANCE', str(e))
            return {
                'success': False,
                'error': 'Failed to check tier maintenance'
            }
    
    def _get_next_tier_info(self, current_tier: str, current_spending: float) -> Dict[str, Any]:
        """Get information about the next tier."""
        tier_order = ['BRONZE', 'SILVER', 'GOLD', 'PLATINUM']
        
        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                next_tier = tier_order[current_index + 1]
                next_threshold = Config.TIER_THRESHOLDS[next_tier]
                spending_needed = max(0, next_threshold - current_spending)
                
                return {
                    'tier': next_tier,
                    'spending_required': next_threshold,
                    'spending_needed': spending_needed,
                    'progress_percentage': min(100, (current_spending / next_threshold) * 100)
                }
            else:
                return {
                    'tier': None,
                    'message': 'You have reached the highest tier!'
                }
        except ValueError:
            return {
                'tier': 'SILVER',
                'spending_required': Config.TIER_THRESHOLDS['SILVER'],
                'spending_needed': Config.TIER_THRESHOLDS['SILVER'] - current_spending,
                'progress_percentage': 0
            }
    
    def _get_tier_benefits(self, tier: str) -> Dict[str, Any]:
        """Get benefits for a specific tier."""
        benefits = {
            'BRONZE': {
                'point_multiplier': '1x base points',
                'annual_fee': '₹0',
                'customer_support': 'Standard support'
            },
            'SILVER': {
                'point_multiplier': '1.25x base points',
                'annual_fee': '₹500 (waived on ₹50K+ spending)',
                'customer_support': 'Priority support'
            },
            'GOLD': {
                'point_multiplier': '1.5x base points',
                'annual_fee': '₹1,500 (waived on ₹200K+ spending)',
                'customer_support': 'Dedicated support line'
            },
            'PLATINUM': {
                'point_multiplier': '2x base points',
                'annual_fee': '₹5,000 (waived on ₹500K+ spending)',
                'customer_support': '24/7 premium support'
            }
        }
        
        return benefits.get(tier, benefits['BRONZE'])