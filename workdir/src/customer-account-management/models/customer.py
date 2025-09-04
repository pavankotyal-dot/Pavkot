"""Customer data models for the Customer & Account Management unit."""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from datetime import datetime
import re

@dataclass
class Customer:
    id: str
    email: str
    name: str
    phone: str
    card_number: str
    tier: str = 'BRONZE'
    registration_date: str = None
    onboarding_completed: bool = False
    communication_preferences: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.registration_date is None:
            self.registration_date = datetime.now().isoformat()
        if self.communication_preferences is None:
            self.communication_preferences = {
                'email': True,
                'sms': True,
                'push': True,
                'in_app': True
            }
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Customer':
        return cls(**data)
    
    def validate(self) -> bool:
        """Validate customer data."""
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, self.email):
            raise ValueError("Invalid email format")
        
        # Phone validation (Indian format)
        phone_pattern = r'^[6-9]\d{9}$'
        if not re.match(phone_pattern, self.phone.replace('+91', '').replace('-', '').replace(' ', '')):
            raise ValueError("Invalid phone number format")
        
        # Card number validation (basic)
        if len(self.card_number.replace('-', '').replace(' ', '')) != 16:
            raise ValueError("Invalid card number format")
        
        # Name validation
        if len(self.name.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        
        return True

@dataclass
class OnboardingProgress:
    customer_id: str
    tutorial_steps_completed: list
    completion_percentage: float
    started_date: str
    completed_date: Optional[str] = None
    
    def __post_init__(self):
        if not hasattr(self, 'started_date') or self.started_date is None:
            self.started_date = datetime.now().isoformat()
    
    def mark_step_completed(self, step: str):
        if step not in self.tutorial_steps_completed:
            self.tutorial_steps_completed.append(step)
            self.completion_percentage = len(self.tutorial_steps_completed) / 5 * 100  # 5 total steps
            
            if self.completion_percentage >= 100 and not self.completed_date:
                self.completed_date = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)