"""Tier status display service for customer tier information."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.base_service import BaseService
from shared.event_store import EventStore
from shared.config import Config
from ..repositories.customer_repository import CustomerRepository
from typing import Dict, Any

class TierDisplayService(BaseService):
    def __init__(self, event_store: EventStore, customer_repo: CustomerRepository):
        super().__init__("CUSTOMER-MGMT", event_store)
        self.customer_repo = customer_repo
    
    def get_tier_status(self, customer_id: str) -> Dict[str, Any]:
        """Get customer tier status and benefits."""
        try:
            customer = self.customer_repo.find_customer_by_id(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            current_tier = customer.tier
            tier_benefits = self._get_tier_benefits(current_tier)
            next_tier_info = self._get_next_tier_info(current_tier)
            
            # Log tier status view
            self.logger.log_business_event('INFO', customer_id, 'TIER_STATUS_VIEW', 'SUCCESS',
                                         f'Customer viewed tier status - currently {current_tier} tier')
            
            return {
                'success': True,
                'tier_status': {
                    'customer_id': customer_id,
                    'current_tier': current_tier,
                    'tier_benefits': tier_benefits,
                    'next_tier': next_tier_info,
                    'tier_multiplier': Config.get_tier_multiplier(current_tier)
                }
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'GET_TIER_STATUS', str(e))
            return {
                'success': False,
                'error': 'Failed to retrieve tier status'
            }
    
    def _get_tier_benefits(self, tier: str) -> Dict[str, Any]:
        """Get benefits for a specific tier."""
        benefits = {
            'BRONZE': {
                'point_multiplier': '1x base points',
                'redemption_options': ['Cashback', 'Basic merchandise'],
                'customer_support': 'Standard support',
                'special_offers': 'Monthly newsletters',
                'annual_fee': '₹0'
            },
            'SILVER': {
                'point_multiplier': '1.25x base points',
                'redemption_options': ['Cashback', 'Travel bookings', 'Premium merchandise'],
                'customer_support': 'Priority support',
                'special_offers': 'Exclusive deals and early access',
                'annual_fee': '₹500 (waived on ₹50K+ spending)'
            },
            'GOLD': {
                'point_multiplier': '1.5x base points',
                'redemption_options': ['All Silver benefits', 'Luxury experiences', 'Hotel upgrades'],
                'customer_support': 'Dedicated support line',
                'special_offers': 'VIP events and premium offers',
                'annual_fee': '₹1,500 (waived on ₹200K+ spending)'
            },
            'PLATINUM': {
                'point_multiplier': '2x base points',
                'redemption_options': ['All Gold benefits', 'Exclusive experiences', 'Concierge services'],
                'customer_support': '24/7 premium support',
                'special_offers': 'Ultra-premium experiences and personalized offers',
                'annual_fee': '₹5,000 (waived on ₹500K+ spending)'
            }
        }
        
        return benefits.get(tier, benefits['BRONZE'])
    
    def _get_next_tier_info(self, current_tier: str) -> Dict[str, Any]:
        """Get information about the next tier."""
        tier_progression = {
            'BRONZE': {
                'next_tier': 'SILVER',
                'spending_required': Config.TIER_THRESHOLDS['SILVER'],
                'benefits_preview': 'Priority support and 1.25x points'
            },
            'SILVER': {
                'next_tier': 'GOLD',
                'spending_required': Config.TIER_THRESHOLDS['GOLD'],
                'benefits_preview': 'Dedicated support and 1.5x points'
            },
            'GOLD': {
                'next_tier': 'PLATINUM',
                'spending_required': Config.TIER_THRESHOLDS['PLATINUM'],
                'benefits_preview': '24/7 premium support and 2x points'
            },
            'PLATINUM': {
                'next_tier': None,
                'spending_required': None,
                'benefits_preview': 'You have reached the highest tier!'
            }
        }
        
        return tier_progression.get(current_tier, tier_progression['BRONZE'])
    
    def get_tier_comparison(self) -> Dict[str, Any]:
        """Get comparison of all tiers."""
        try:
            tiers = ['BRONZE', 'SILVER', 'GOLD', 'PLATINUM']
            comparison = {}
            
            for tier in tiers:
                comparison[tier] = {
                    'spending_threshold': Config.TIER_THRESHOLDS[tier],
                    'point_multiplier': Config.get_tier_multiplier(tier),
                    'benefits': self._get_tier_benefits(tier)
                }
            
            return {
                'success': True,
                'tier_comparison': comparison
            }
            
        except Exception as e:
            self.logger.log_error(None, 'GET_TIER_COMPARISON', str(e))
            return {
                'success': False,
                'error': 'Failed to retrieve tier comparison'
            }