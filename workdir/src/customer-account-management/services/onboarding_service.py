"""Customer onboarding service."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.base_service import BaseService
from shared.event_store import EventStore
from ..repositories.customer_repository import CustomerRepository, OnboardingRepository
from typing import Dict, Any, List

class OnboardingService(BaseService):
    def __init__(self, event_store: EventStore, customer_repo: CustomerRepository, 
                 onboarding_repo: OnboardingRepository):
        super().__init__("CUSTOMER-MGMT", event_store)
        self.customer_repo = customer_repo
        self.onboarding_repo = onboarding_repo
        
        # Define onboarding tutorial steps
        self.tutorial_steps = [
            'welcome_intro',
            'tier_benefits_explained',
            'point_earning_tutorial',
            'redemption_options_overview',
            'dashboard_walkthrough'
        ]
    
    def get_onboarding_status(self, customer_id: str) -> Dict[str, Any]:
        """Get customer onboarding status and progress."""
        try:
            customer = self.customer_repo.find_customer_by_id(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            progress = self.onboarding_repo.find_progress_by_customer(customer_id)
            if not progress:
                # Initialize onboarding progress if not exists
                from ..models.customer import OnboardingProgress
                progress = OnboardingProgress(
                    customer_id=customer_id,
                    tutorial_steps_completed=[],
                    completion_percentage=0.0
                )
                self.onboarding_repo.save_progress(progress)
            
            return {
                'success': True,
                'onboarding_status': {
                    'customer_id': customer_id,
                    'completed': customer.onboarding_completed,
                    'completion_percentage': progress.completion_percentage,
                    'steps_completed': progress.tutorial_steps_completed,
                    'total_steps': len(self.tutorial_steps),
                    'next_step': self._get_next_step(progress.tutorial_steps_completed),
                    'started_date': progress.started_date,
                    'completed_date': progress.completed_date
                }
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'GET_ONBOARDING_STATUS', str(e))
            return {
                'success': False,
                'error': 'Failed to retrieve onboarding status'
            }
    
    def complete_tutorial_step(self, customer_id: str, step: str) -> Dict[str, Any]:
        """Mark a tutorial step as completed."""
        try:
            if step not in self.tutorial_steps:
                return {
                    'success': False,
                    'error': f'Invalid tutorial step: {step}'
                }
            
            progress = self.onboarding_repo.mark_step_completed(customer_id, step)
            if not progress:
                return {
                    'success': False,
                    'error': 'Customer onboarding progress not found'
                }
            
            # Check if onboarding is now complete
            if progress.completion_percentage >= 100:
                self._complete_onboarding(customer_id)
            
            self.logger.log_business_event('INFO', customer_id, 'TUTORIAL_STEP', 'COMPLETED',
                                         f'Completed tutorial step: {step} ({progress.completion_percentage}% complete)')
            
            return {
                'success': True,
                'message': f'Tutorial step {step} completed',
                'completion_percentage': progress.completion_percentage,
                'onboarding_complete': progress.completion_percentage >= 100
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'COMPLETE_TUTORIAL_STEP', str(e))
            return {
                'success': False,
                'error': 'Failed to complete tutorial step'
            }
    
    def _complete_onboarding(self, customer_id: str):
        """Complete the onboarding process."""
        # Update customer onboarding status
        self.customer_repo.update_customer(customer_id, {'onboarding_completed': True})
        
        # Publish onboarding completed event
        customer = self.customer_repo.find_customer_by_id(customer_id)
        progress = self.onboarding_repo.find_progress_by_customer(customer_id)
        
        self.publish_event('CustomerOnboardingCompleted', customer_id, {
            'customer_id': customer_id,
            'completion_date': progress.completed_date,
            'tutorial_steps': progress.tutorial_steps_completed,
            'customer_name': customer.name if customer else 'Unknown'
        })
        
        self.logger.log_business_event('INFO', customer_id, 'ONBOARDING', 'COMPLETED',
                                     f'Customer completed onboarding tutorial in {len(progress.tutorial_steps_completed)} steps')
    
    def _get_next_step(self, completed_steps: List[str]) -> str:
        """Get the next tutorial step to complete."""
        for step in self.tutorial_steps:
            if step not in completed_steps:
                return step
        return None
    
    def get_tutorial_content(self, step: str) -> Dict[str, Any]:
        """Get tutorial content for a specific step."""
        tutorial_content = {
            'welcome_intro': {
                'title': 'Welcome to PremiumCard Loyalty Program!',
                'content': 'Earn points on every purchase and enjoy exclusive benefits.',
                'duration': '2 minutes'
            },
            'tier_benefits_explained': {
                'title': 'Understanding Your Tier Benefits',
                'content': 'Bronze, Silver, Gold, and Platinum tiers offer increasing benefits.',
                'duration': '3 minutes'
            },
            'point_earning_tutorial': {
                'title': 'How to Earn Points',
                'content': 'Earn 1 point per ₹1 spent, with bonus multipliers on categories.',
                'duration': '3 minutes'
            },
            'redemption_options_overview': {
                'title': 'Redeem Your Points',
                'content': 'Cashback, travel, merchandise, and exclusive experiences available.',
                'duration': '4 minutes'
            },
            'dashboard_walkthrough': {
                'title': 'Your Personal Dashboard',
                'content': 'Track spending, points, and discover personalized recommendations.',
                'duration': '3 minutes'
            }
        }
        
        return {
            'success': True,
            'tutorial': tutorial_content.get(step, {
                'title': 'Tutorial Step',
                'content': 'Tutorial content not available',
                'duration': '1 minute'
            })
        }