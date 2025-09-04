"""Customer profile management service."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.base_service import BaseService
from shared.event_store import EventStore
from ..repositories.customer_repository import CustomerRepository
from typing import Dict, Any

class ProfileService(BaseService):
    def __init__(self, event_store: EventStore, customer_repo: CustomerRepository):
        super().__init__("CUSTOMER-MGMT", event_store)
        self.customer_repo = customer_repo
    
    def update_profile(self, customer_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer profile information."""
        try:
            customer = self.customer_repo.find_customer_by_id(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Validate allowed fields for update
            allowed_fields = ['name', 'phone', 'email']
            invalid_fields = [field for field in updates.keys() if field not in allowed_fields]
            if invalid_fields:
                return {
                    'success': False,
                    'error': f'Cannot update fields: {", ".join(invalid_fields)}'
                }
            
            # Validate email uniqueness if email is being updated
            if 'email' in updates and updates['email'] != customer.email:
                existing_customer = self.customer_repo.find_customer_by_email(updates['email'])
                if existing_customer:
                    return {
                        'success': False,
                        'error': 'Email already exists for another customer'
                    }
            
            # Update customer
            updated_customer = self.customer_repo.update_customer(customer_id, updates)
            if not updated_customer:
                return {
                    'success': False,
                    'error': 'Failed to update customer profile'
                }
            
            # Publish profile updated event
            self.publish_event('CustomerProfileUpdated', customer_id, {
                'customer_id': customer_id,
                'updated_fields': list(updates.keys()),
                'updates': updates
            })
            
            self.logger.log_business_event('INFO', customer_id, 'PROFILE_UPDATE', 'SUCCESS',
                                         f'Updated profile fields: {", ".join(updates.keys())}')
            
            return {
                'success': True,
                'message': 'Profile updated successfully',
                'updated_fields': list(updates.keys())
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'UPDATE_PROFILE', str(e))
            return {
                'success': False,
                'error': 'Failed to update profile'
            }
    
    def update_communication_preferences(self, customer_id: str, preferences: Dict[str, bool]) -> Dict[str, Any]:
        """Update customer communication preferences."""
        try:
            customer = self.customer_repo.find_customer_by_id(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Validate preference keys
            valid_preferences = ['email', 'sms', 'push', 'in_app']
            invalid_prefs = [pref for pref in preferences.keys() if pref not in valid_preferences]
            if invalid_prefs:
                return {
                    'success': False,
                    'error': f'Invalid preference keys: {", ".join(invalid_prefs)}'
                }
            
            # Update preferences
            success = self.customer_repo.update_communication_preferences(customer_id, preferences)
            if not success:
                return {
                    'success': False,
                    'error': 'Failed to update communication preferences'
                }
            
            # Publish preferences updated event
            self.publish_event('CommunicationPreferencesUpdated', customer_id, {
                'customer_id': customer_id,
                'preferences': preferences
            })
            
            # Log preference changes
            enabled_prefs = [pref for pref, enabled in preferences.items() if enabled]
            disabled_prefs = [pref for pref, enabled in preferences.items() if not enabled]
            
            pref_summary = []
            if enabled_prefs:
                pref_summary.append(f"enabled: {', '.join(enabled_prefs)}")
            if disabled_prefs:
                pref_summary.append(f"disabled: {', '.join(disabled_prefs)}")
            
            self.logger.log_business_event('INFO', customer_id, 'PREFERENCES_UPDATE', 'SUCCESS',
                                         f'Updated communication preferences - {"; ".join(pref_summary)}')
            
            return {
                'success': True,
                'message': 'Communication preferences updated successfully',
                'preferences': preferences
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'UPDATE_PREFERENCES', str(e))
            return {
                'success': False,
                'error': 'Failed to update communication preferences'
            }
    
    def get_communication_preferences(self, customer_id: str) -> Dict[str, Any]:
        """Get customer communication preferences."""
        try:
            customer = self.customer_repo.find_customer_by_id(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            return {
                'success': True,
                'preferences': customer.communication_preferences
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'GET_PREFERENCES', str(e))
            return {
                'success': False,
                'error': 'Failed to retrieve communication preferences'
            }