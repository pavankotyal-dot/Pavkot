from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid

class RedemptionType(Enum):
    CASHBACK = "cashback"
    TRAVEL = "travel"
    MERCHANDISE = "merchandise"
    EXPERIENCE = "experience"
    GIFT_CARD = "gift_card"

class RedemptionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    FAILED = "failed"

class FulfillmentStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class RedemptionItem:
    item_id: str
    name: str
    description: str
    redemption_type: RedemptionType
    points_required: int
    category: str
    availability: bool = True
    tier_requirement: Optional[str] = None
    partner_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class RedemptionRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    item_id: str = ""
    points_used: int = 0
    redemption_type: RedemptionType = RedemptionType.CASHBACK
    status: RedemptionStatus = RedemptionStatus.PENDING
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.NOT_STARTED
    request_details: Dict[str, Any] = field(default_factory=dict)
    fulfillment_details: Dict[str, Any] = field(default_factory=dict)
    partner_reference: Optional[str] = None
    estimated_fulfillment: Optional[datetime] = None
    actual_fulfillment: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class CashbackRequest:
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    points_redeemed: int = 0
    cashback_amount: float = 0.0
    bank_account: str = ""
    status: RedemptionStatus = RedemptionStatus.PENDING
    transaction_reference: Optional[str] = None
    processing_fee: float = 0.0
    net_amount: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None

@dataclass
class TravelBooking:
    booking_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    booking_type: str = ""  # flight, hotel, car_rental
    points_used: int = 0
    booking_details: Dict[str, Any] = field(default_factory=dict)
    partner_booking_ref: Optional[str] = None
    status: RedemptionStatus = RedemptionStatus.PENDING
    total_cost: float = 0.0
    points_value: float = 0.0
    additional_payment: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    travel_date: Optional[datetime] = None

@dataclass
class MerchandiseOrder:
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    item_id: str = ""
    quantity: int = 1
    points_used: int = 0
    shipping_address: Dict[str, str] = field(default_factory=dict)
    status: RedemptionStatus = RedemptionStatus.PENDING
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.NOT_STARTED
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ExperienceBooking:
    booking_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    experience_id: str = ""
    points_used: int = 0
    booking_details: Dict[str, Any] = field(default_factory=dict)
    status: RedemptionStatus = RedemptionStatus.PENDING
    experience_date: Optional[datetime] = None
    location: str = ""
    participants: int = 1
    special_requests: str = ""
    confirmation_code: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class RedemptionCatalog:
    catalog_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    items: List[RedemptionItem] = field(default_factory=list)
    active: bool = True
    tier_specific: bool = False
    valid_from: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_available_items(self, customer_tier: str = None) -> List[RedemptionItem]:
        available = [item for item in self.items if item.availability]
        if customer_tier:
            tier_order = {"bronze": 0, "silver": 1, "gold": 2, "platinum": 3}
            customer_level = tier_order.get(customer_tier.lower(), 0)
            available = [item for item in available 
                        if not item.tier_requirement or 
                        tier_order.get(item.tier_requirement.lower(), 0) <= customer_level]
        return available

    def get_items_by_category(self, category: str) -> List[RedemptionItem]:
        return [item for item in self.items if item.category.lower() == category.lower()]

    def get_items_by_type(self, redemption_type: RedemptionType) -> List[RedemptionItem]:
        return [item for item in self.items if item.redemption_type == redemption_type]