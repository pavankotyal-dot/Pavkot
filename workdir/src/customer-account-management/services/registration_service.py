"""Customer registration service."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.base_service import BaseService
from shared.event_store import EventStore
from shared.config import Config
from ..repositories.customer_repository import CustomerRepository, OnboardingRepository
from ..models.customer import Customer, OnboardingProgress
from typing import Dict, Any
import uuid

class RegistrationService(BaseService):
    def __init__(self, event_store: EventStore, customer_repo: CustomerRepository, 
                 onboarding_repo: OnboardingRepository):
        super().__init__("CUSTOMER-MGMT", event_store)
        self.customer_repo = customer_repo
        self.onboarding_repo = onboarding_repo
    
    def register_customer(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new customer."""
        try:
            # Validate required fields
            required_fields = ['email', 'name', 'phone', 'card_number']
            self.validate_required_fields(registration_data, required_fields)
            
            # Check if customer already exists
            existing_customer = self.customer_repo.find_customer_by_email(registration_data['email'])
            if existing_customer:
                raise ValueError("Customer with this email already exists")
            
            existing_card = self.customer_repo.find_customer_by_card(registration_data['card_number'])
            if existing_card:
                raise ValueError("Customer with this card number already exists")
            
            # Create new customer
            customer_id = str(uuid.uuid4())
            customer = Customer(
                id=customer_id,
                email=registration_data['email'],
                name=registration_data['name'],
                phone=registration_data['phone'],
                card_number=registration_data['card_number'],
                tier='BRONZE'
            )
            
            # Save customer
            self.customer_repo.save_customer(customer)
            
            # Initialize onboarding progress
            onboarding_progress = OnboardingProgress(
                customer_id=customer_id,
                tutorial_steps_completed=[],
                completion_percentage=0.0
            )
            self.onboarding_repo.save_progress(onboarding_progress)
            
            # Publish customer registered event
            self.publish_event('CustomerRegistered', customer_id, {
                'customer_id': customer_id,
                'email': customer.email,
                'name': customer.name,
                'tier': customer.tier,
                'registration_date': customer.registration_date
            })
            
            # Log business event
            self.logger.log_customer_registration(customer_id, customer.name, customer.tier)
            
            return {
                'success': True,
                'customer_id': customer_id,
                'message': f'Customer {customer.name} registered successfully',
                'tier': customer.tier
            }
            
        except ValueError as e:
            self.logger.log_error(None, 'REGISTRATION', str(e))
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            self.logger.log_error(None, 'REGISTRATION', f'Unexpected error: {str(e)}')
            return {
                'success': False,
                'error': 'Registration failed due to system error'
            }
    
    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get customer profile information."""
        try:
            customer = self.customer_repo.find_customer_by_id(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            return {
                'success': True,
                'customer': {
                    'id': customer.id,
                    'name': customer.name,
                    'email': customer.email,
                    'phone': customer.phone,
                    'tier': customer.tier,
                    'registration_date': customer.registration_date,
                    'onboarding_completed': customer.onboarding_completed,
                    'communication_preferences': customer.communication_preferences
                }
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'GET_PROFILE', str(e))
            return {
                'success': False,
                'error': 'Failed to retrieve customer profile'
            }