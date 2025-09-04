"""Customer repository for data persistence."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.repository import BaseRepository
from typing import Optional, List, Dict, Any
from ..models.customer import Customer, OnboardingProgress

class CustomerRepository(BaseRepository):
    def __init__(self, data_dir: str = "workdir/data"):
        super().__init__(f"{data_dir}/customers.json")
    
    def save_customer(self, customer: Customer) -> str:
        """Save a customer to the repository."""
        customer.validate()  # Validate before saving
        return self.save(customer.id, customer.to_dict())
    
    def find_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """Find a customer by ID."""
        data = self.find_by_id(customer_id)
        return Customer.from_dict(data) if data else None
    
    def find_customer_by_email(self, email: str) -> Optional[Customer]:
        """Find a customer by email."""
        customers = self.find_by_field('email', email)
        return Customer.from_dict(customers[0]) if customers else None
    
    def find_customer_by_card(self, card_number: str) -> Optional[Customer]:
        """Find a customer by card number."""
        customers = self.find_by_field('card_number', card_number)
        return Customer.from_dict(customers[0]) if customers else None
    
    def get_all_customers(self) -> List[Customer]:
        """Get all customers."""
        return [Customer.from_dict(data) for data in self.find_all()]
    
    def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> Optional[Customer]:
        """Update customer information."""
        updated_data = self.update(customer_id, updates)
        return Customer.from_dict(updated_data) if updated_data else None
    
    def update_tier(self, customer_id: str, new_tier: str) -> bool:
        """Update customer tier."""
        return self.update(customer_id, {'tier': new_tier}) is not None
    
    def update_communication_preferences(self, customer_id: str, preferences: Dict[str, bool]) -> bool:
        """Update customer communication preferences."""
        return self.update(customer_id, {'communication_preferences': preferences}) is not None

class OnboardingRepository(BaseRepository):
    def __init__(self, data_dir: str = "workdir/data"):
        super().__init__(f"{data_dir}/onboarding.json")
    
    def save_progress(self, progress: OnboardingProgress) -> str:
        """Save onboarding progress."""
        return self.save(progress.customer_id, progress.to_dict())
    
    def find_progress_by_customer(self, customer_id: str) -> Optional[OnboardingProgress]:
        """Find onboarding progress by customer ID."""
        data = self.find_by_id(customer_id)
        return OnboardingProgress(**data) if data else None
    
    def mark_step_completed(self, customer_id: str, step: str) -> Optional[OnboardingProgress]:
        """Mark an onboarding step as completed."""
        progress = self.find_progress_by_customer(customer_id)
        if progress:
            progress.mark_step_completed(step)
            self.save_progress(progress)
            return progress
        return None