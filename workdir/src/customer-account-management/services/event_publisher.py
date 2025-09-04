"""Event publisher for customer lifecycle events."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.event_handler import EventHandler
from shared.event_store import EventStore, Event
from shared.logging import BusinessLogger
from typing import Dict, Any

class CustomerEventPublisher:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.event_handler = EventHandler("CUSTOMER-MGMT", event_store)
        self.logger = BusinessLogger("CUSTOMER-MGMT-EventPublisher")
        
        # Register event handlers for tier updates from other units
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup event handlers for incoming events from other units."""
        self.event_handler.register_handler('TierAdvanced', self._handle_tier_advanced)
        self.event_handler.register_handler('TierDowngraded', self._handle_tier_downgraded)
    
    def _handle_tier_advanced(self, event: Event):
        """Handle tier advancement event from Transaction & Rewards Engine."""
        try:
            customer_id = event.data.get('customer_id')
            new_tier = event.data.get('new_tier')
            
            if customer_id and new_tier:
                # Update customer tier in repository
                from ..repositories.customer_repository import CustomerRepository
                customer_repo = CustomerRepository()
                success = customer_repo.update_tier(customer_id, new_tier)
                
                if success:
                    self.logger.log_business_event('INFO', customer_id, 'TIER_UPDATE', 'SUCCESS',
                                                 f'Updated customer tier to {new_tier}')
                else:
                    self.logger.log_error(customer_id, 'TIER_UPDATE', 
                                        f'Failed to update customer tier to {new_tier}')
        
        except Exception as e:
            self.logger.log_error(event.aggregate_id, 'TIER_ADVANCED_HANDLER', str(e))
    
    def _handle_tier_downgraded(self, event: Event):
        """Handle tier downgrade event from Transaction & Rewards Engine."""
        try:
            customer_id = event.data.get('customer_id')
            new_tier = event.data.get('new_tier')
            
            if customer_id and new_tier:
                # Update customer tier in repository
                from ..repositories.customer_repository import CustomerRepository
                customer_repo = CustomerRepository()
                success = customer_repo.update_tier(customer_id, new_tier)
                
                if success:
                    self.logger.log_business_event('INFO', customer_id, 'TIER_DOWNGRADE', 'SUCCESS',
                                                 f'Downgraded customer tier to {new_tier}')
                else:
                    self.logger.log_error(customer_id, 'TIER_DOWNGRADE', 
                                        f'Failed to downgrade customer tier to {new_tier}')
        
        except Exception as e:
            self.logger.log_error(event.aggregate_id, 'TIER_DOWNGRADED_HANDLER', str(e))
    
    def process_incoming_events(self):
        """Process incoming events from other units."""
        self.event_handler.process_events()
    
    def publish_customer_registered(self, customer_id: str, customer_data: Dict[str, Any]):
        """Publish customer registered event."""
        event_data = {
            'customer_id': customer_id,
            'email': customer_data.get('email'),
            'name': customer_data.get('name'),
            'tier': customer_data.get('tier', 'BRONZE'),
            'registration_date': customer_data.get('registration_date')
        }
        
        self.event_store.append_event('CustomerRegistered', customer_id, event_data)
        self.logger.log_business_event('INFO', customer_id, 'EVENT_PUBLISHED', 'SUCCESS',
                                     'Published CustomerRegistered event')
    
    def publish_onboarding_completed(self, customer_id: str, completion_data: Dict[str, Any]):
        """Publish customer onboarding completed event."""
        event_data = {
            'customer_id': customer_id,
            'completion_date': completion_data.get('completion_date'),
            'tutorial_steps': completion_data.get('tutorial_steps', []),
            'customer_name': completion_data.get('customer_name')
        }
        
        self.event_store.append_event('CustomerOnboardingCompleted', customer_id, event_data)
        self.logger.log_business_event('INFO', customer_id, 'EVENT_PUBLISHED', 'SUCCESS',
                                     'Published CustomerOnboardingCompleted event')
    
    def publish_preferences_updated(self, customer_id: str, preferences: Dict[str, bool]):
        """Publish communication preferences updated event."""
        event_data = {
            'customer_id': customer_id,
            'preferences': preferences,
            'updated_date': Event.timestamp if hasattr(Event, 'timestamp') else None
        }
        
        self.event_store.append_event('CommunicationPreferencesUpdated', customer_id, event_data)
        self.logger.log_business_event('INFO', customer_id, 'EVENT_PUBLISHED', 'SUCCESS',
                                     'Published CommunicationPreferencesUpdated event')