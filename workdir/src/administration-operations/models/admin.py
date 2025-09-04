from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid

class AdminRole(Enum):
    SUPER_ADMIN = "super_admin"
    PROGRAM_MANAGER = "program_manager"
    CUSTOMER_SUPPORT = "customer_support"
    ANALYST = "analyst"
    OPERATIONS = "operations"

class ConfigurationType(Enum):
    TIER_THRESHOLDS = "tier_thresholds"
    POINT_RATES = "point_rates"
    CATEGORY_MULTIPLIERS = "category_multipliers"
    REDEMPTION_RATES = "redemption_rates"
    SYSTEM_SETTINGS = "system_settings"

class SupportTicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"

@dataclass
class AdminUser:
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    full_name: str = ""
    role: AdminRole = AdminRole.CUSTOMER_SUPPORT
    permissions: List[str] = field(default_factory=list)
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""

@dataclass
class ProgramConfiguration:
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    config_type: ConfigurationType = ConfigurationType.SYSTEM_SETTINGS
    name: str = ""
    description: str = ""
    config_data: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    effective_from: datetime = field(default_factory=datetime.now)
    effective_until: Optional[datetime] = None
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class SupportTicket:
    ticket_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    subject: str = ""
    description: str = ""
    category: str = ""
    priority: str = "medium"  # low, medium, high, urgent
    status: SupportTicketStatus = SupportTicketStatus.OPEN
    assigned_to: Optional[str] = None
    resolution: str = ""
    customer_satisfaction: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

@dataclass
class BusinessReport:
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str = ""
    title: str = ""
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    generated_by: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    file_path: Optional[str] = None

@dataclass
class SystemAlert:
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: str = ""  # error, warning, info
    title: str = ""
    message: str = ""
    severity: str = "medium"
    component: str = ""
    is_resolved: bool = False
    resolved_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

@dataclass
class AuditLog:
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""
    timestamp: datetime = field(default_factory=datetime.now)