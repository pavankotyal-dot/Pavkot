"""Transaction and Point data models for the Transaction & Rewards Engine unit."""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

@dataclass
class Transaction:
    id: str
    customer_id: str
    amount: float
    category: str
    merchant_name: str
    merchant_category_code: str
    card_number_last4: str
    transaction_date: str
    status: str = 'PENDING'
    points_earned: int = 0
    category_multiplier: float = 1.0
    tier_multiplier: float = 1.0
    total_multiplier: float = 1.0
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.transaction_date:
            self.transaction_date = datetime.now().isoformat()
    
    def calculate_points(self, category_multiplier: float, tier_multiplier: float) -> int:
        """Calculate points earned for this transaction."""
        self.category_multiplier = category_multiplier
        self.tier_multiplier = tier_multiplier
        self.total_multiplier = category_multiplier * tier_multiplier
        self.points_earned = int(self.amount * self.total_multiplier)
        return self.points_earned
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        return cls(**data)

@dataclass
class PointBalance:
    customer_id: str
    total_points: int = 0
    lifetime_points_earned: int = 0
    points_redeemed: int = 0
    last_updated: str = None
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
    
    def add_points(self, points: int):
        """Add points to the balance."""
        self.total_points += points
        self.lifetime_points_earned += points
        self.last_updated = datetime.now().isoformat()
    
    def deduct_points(self, points: int) -> bool:
        """Deduct points from the balance."""
        if self.total_points >= points:
            self.total_points -= points
            self.points_redeemed += points
            self.last_updated = datetime.now().isoformat()
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PointBalance':
        return cls(**data)

@dataclass
class CustomerTier:
    customer_id: str
    current_tier: str = 'BRONZE'
    annual_spending: float = 0.0
    tier_start_date: str = None
    last_tier_check: str = None
    spending_to_next_tier: float = 0.0
    
    def __post_init__(self):
        if not self.tier_start_date:
            self.tier_start_date = datetime.now().isoformat()
        if not self.last_tier_check:
            self.last_tier_check = datetime.now().isoformat()
    
    def add_spending(self, amount: float):
        """Add spending amount to annual total."""
        self.annual_spending += amount
        self.last_tier_check = datetime.now().isoformat()
    
    def update_tier(self, new_tier: str):
        """Update customer tier."""
        if new_tier != self.current_tier:
            self.current_tier = new_tier
            self.tier_start_date = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomerTier':
        return cls(**data)

@dataclass
class CategoryMultiplier:
    category: str
    multiplier: float
    active: bool = True
    start_date: str = None
    end_date: Optional[str] = None
    campaign_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.start_date:
            self.start_date = datetime.now().isoformat()
    
    def is_active(self) -> bool:
        """Check if multiplier is currently active."""
        if not self.active:
            return False
        
        now = datetime.now().isoformat()
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CategoryMultiplier':
        return cls(**data)