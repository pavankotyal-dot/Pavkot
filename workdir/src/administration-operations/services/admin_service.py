from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os

from ..models.admin import AdminUser, ProgramConfiguration, SupportTicket, BusinessReport, SystemAlert, AuditLog
from ..models.admin import AdminRole, ConfigurationType, SupportTicketStatus
from ...shared.event_store import EventStore
from ...shared.logging import get_logger

class AdminService:
    def __init__(self, event_store: EventStore, data_dir: str = "data/admin"):
        self.event_store = event_store
        self.data_dir = data_dir
        self.logger = get_logger(__name__)
        
        # In-memory storage
        self.admin_users: Dict[str, AdminUser] = {}
        self.configurations: Dict[str, ProgramConfiguration] = {}
        self.support_tickets: Dict[str, SupportTicket] = {}
        self.business_reports: Dict[str, BusinessReport] = {}
        self.system_alerts: Dict[str, SystemAlert] = {}
        self.audit_logs: List[AuditLog] = []
        
        self._load_data()
        self._initialize_default_config()

    def _load_data(self):
        """Load admin data from JSON files"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Load admin users
            users_file = os.path.join(self.data_dir, "admin_users.json")
            if os.path.exists(users_file):
                with open(users_file, 'r') as f:
                    data = json.load(f)
                    for user_data in data:
                        user = AdminUser(**user_data)
                        self.admin_users[user.user_id] = user

        except Exception as e:
            self.logger.error(f"Error loading admin data: {e}")

    def _save_data(self):
        """Save admin data to JSON files"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Save admin users
            users_file = os.path.join(self.data_dir, "admin_users.json")
            with open(users_file, 'w') as f:
                users_data = []
                for user in self.admin_users.values():
                    data = {
                        'user_id': user.user_id,
                        'username': user.username,
                        'email': user.email,
                        'full_name': user.full_name,
                        'role': user.role.value,
                        'permissions': user.permissions,
                        'is_active': user.is_active,
                        'last_login': user.last_login.isoformat() if user.last_login else None,
                        'created_at': user.created_at.isoformat(),
                        'created_by': user.created_by
                    }
                    users_data.append(data)
                json.dump(users_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving admin data: {e}")

    def _initialize_default_config(self):
        """Initialize default program configurations"""
        if not self.configurations:
            default_configs = [
                {
                    "config_type": ConfigurationType.TIER_THRESHOLDS,
                    "name": "Customer Tier Thresholds",
                    "description": "Annual spending thresholds for customer tiers",
                    "config_data": {
                        "bronze": 0,
                        "silver": 50000,
                        "gold": 200000,
                        "platinum": 500000
                    }
                },
                {
                    "config_type": ConfigurationType.POINT_RATES,
                    "name": "Point Earning Rates",
                    "description": "Points earned per rupee spent",
                    "config_data": {
                        "base_rate": 1.0,
                        "bonus_categories": {
                            "dining": 2.0,
                            "fuel": 1.5,
                            "grocery": 1.5
                        }
                    }
                },
                {
                    "config_type": ConfigurationType.REDEMPTION_RATES,
                    "name": "Redemption Conversion Rates",
                    "description": "Conversion rates for different redemption types",
                    "config_data": {
                        "cashback_rate": 0.5,
                        "travel_rate": 0.6,
                        "merchandise_rate": 0.4
                    }
                }
            ]
            
            for config_data in default_configs:
                config = ProgramConfiguration(
                    config_type=config_data["config_type"],
                    name=config_data["name"],
                    description=config_data["description"],
                    config_data=config_data["config_data"],
                    created_by="system"
                )
                self.configurations[config.config_id] = config

    def create_admin_user(self, username: str, email: str, full_name: str, 
                         role: AdminRole, created_by: str) -> Dict[str, Any]:
        """Create a new admin user"""
        try:
            # Check if username already exists
            if any(user.username == username for user in self.admin_users.values()):
                return {"success": False, "error": "Username already exists"}

            user = AdminUser(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                created_by=created_by
            )
            
            # Set default permissions based on role
            user.permissions = self._get_default_permissions(role)
            
            self.admin_users[user.user_id] = user
            self._save_data()
            
            # Log audit event
            self._log_audit_action(created_by, "create_admin_user", "admin_user", user.user_id)
            
            return {
                "success": True,
                "user_id": user.user_id,
                "username": user.username,
                "role": user.role.value,
                "permissions": user.permissions
            }

        except Exception as e:
            self.logger.error(f"Error creating admin user: {e}")
            return {"success": False, "error": str(e)}

    def _get_default_permissions(self, role: AdminRole) -> List[str]:
        """Get default permissions for admin role"""
        permission_map = {
            AdminRole.SUPER_ADMIN: ["*"],
            AdminRole.PROGRAM_MANAGER: ["config_read", "config_write", "reports_read", "reports_write"],
            AdminRole.CUSTOMER_SUPPORT: ["tickets_read", "tickets_write", "customer_read"],
            AdminRole.ANALYST: ["reports_read", "analytics_read"],
            AdminRole.OPERATIONS: ["system_read", "alerts_read", "alerts_write"]
        }
        return permission_map.get(role, [])

    def update_program_configuration(self, config_type: ConfigurationType, 
                                   config_data: Dict[str, Any], updated_by: str) -> Dict[str, Any]:
        """Update program configuration"""
        try:
            # Find existing configuration
            existing_config = None
            for config in self.configurations.values():
                if config.config_type == config_type and config.is_active:
                    existing_config = config
                    break
            
            if existing_config:
                # Deactivate old configuration
                existing_config.is_active = False
                existing_config.effective_until = datetime.now()
            
            # Create new configuration
            new_config = ProgramConfiguration(
                config_type=config_type,
                name=f"{config_type.value.replace('_', ' ').title()} Configuration",
                description=f"Updated {config_type.value} configuration",
                config_data=config_data,
                created_by=updated_by
            )
            
            self.configurations[new_config.config_id] = new_config
            
            # Publish configuration change event
            self.event_store.publish_event({
                "event_type": "program_configuration_updated",
                "config_type": config_type.value,
                "config_id": new_config.config_id,
                "updated_by": updated_by,
                "timestamp": datetime.now().isoformat()
            })
            
            # Log audit event
            self._log_audit_action(updated_by, "update_configuration", "program_config", new_config.config_id)
            
            return {
                "success": True,
                "config_id": new_config.config_id,
                "config_type": config_type.value,
                "effective_from": new_config.effective_from.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return {"success": False, "error": str(e)}

    def create_support_ticket(self, customer_id: str, subject: str, description: str, 
                            category: str, priority: str = "medium") -> Dict[str, Any]:
        """Create a support ticket"""
        try:
            ticket = SupportTicket(
                customer_id=customer_id,
                subject=subject,
                description=description,
                category=category,
                priority=priority
            )
            
            self.support_tickets[ticket.ticket_id] = ticket
            
            # Publish ticket creation event
            self.event_store.publish_event({
                "event_type": "support_ticket_created",
                "ticket_id": ticket.ticket_id,
                "customer_id": customer_id,
                "category": category,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "ticket_id": ticket.ticket_id,
                "status": ticket.status.value,
                "created_at": ticket.created_at.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error creating support ticket: {e}")
            return {"success": False, "error": str(e)}

    def assign_support_ticket(self, ticket_id: str, assigned_to: str, assigned_by: str) -> Dict[str, Any]:
        """Assign support ticket to admin user"""
        try:
            ticket = self.support_tickets.get(ticket_id)
            if not ticket:
                return {"success": False, "error": "Ticket not found"}
            
            ticket.assigned_to = assigned_to
            ticket.status = SupportTicketStatus.IN_PROGRESS
            ticket.updated_at = datetime.now()
            
            # Log audit event
            self._log_audit_action(assigned_by, "assign_ticket", "support_ticket", ticket_id)
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "assigned_to": assigned_to,
                "status": ticket.status.value
            }

        except Exception as e:
            self.logger.error(f"Error assigning ticket: {e}")
            return {"success": False, "error": str(e)}

    def resolve_support_ticket(self, ticket_id: str, resolution: str, 
                             resolved_by: str) -> Dict[str, Any]:
        """Resolve support ticket"""
        try:
            ticket = self.support_tickets.get(ticket_id)
            if not ticket:
                return {"success": False, "error": "Ticket not found"}
            
            ticket.resolution = resolution
            ticket.status = SupportTicketStatus.RESOLVED
            ticket.resolved_at = datetime.now()
            ticket.updated_at = datetime.now()
            
            # Publish resolution event
            self.event_store.publish_event({
                "event_type": "support_ticket_resolved",
                "ticket_id": ticket_id,
                "customer_id": ticket.customer_id,
                "resolved_by": resolved_by,
                "resolution_time_hours": (ticket.resolved_at - ticket.created_at).total_seconds() / 3600,
                "timestamp": datetime.now().isoformat()
            })
            
            # Log audit event
            self._log_audit_action(resolved_by, "resolve_ticket", "support_ticket", ticket_id)
            
            return {
                "success": True,
                "ticket_id": ticket_id,
                "status": ticket.status.value,
                "resolved_at": ticket.resolved_at.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error resolving ticket: {e}")
            return {"success": False, "error": str(e)}

    def generate_business_report(self, report_type: str, parameters: Dict[str, Any], 
                               generated_by: str) -> Dict[str, Any]:
        """Generate business intelligence report"""
        try:
            # Get data based on report type
            report_data = self._generate_report_data(report_type, parameters)
            
            report = BusinessReport(
                report_type=report_type,
                title=f"{report_type.replace('_', ' ').title()} Report",
                description=f"Generated {report_type} report",
                parameters=parameters,
                data=report_data,
                generated_by=generated_by
            )
            
            self.business_reports[report.report_id] = report
            
            return {
                "success": True,
                "report_id": report.report_id,
                "report_type": report_type,
                "data": report_data,
                "generated_at": report.generated_at.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {"success": False, "error": str(e)}

    def _generate_report_data(self, report_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report data based on type"""
        # Mock report data generation
        if report_type == "customer_summary":
            return {
                "total_customers": 1250,
                "active_customers": 1100,
                "tier_distribution": {
                    "bronze": 600,
                    "silver": 350,
                    "gold": 120,
                    "platinum": 30
                },
                "avg_engagement_score": 67.5
            }
        elif report_type == "revenue_analysis":
            return {
                "total_revenue": 15750000,
                "points_issued": 15750000,
                "points_redeemed": 3150000,
                "redemption_rate": 20.0,
                "top_categories": ["dining", "shopping", "fuel"]
            }
        else:
            return {"message": "Report data not available"}

    def create_system_alert(self, alert_type: str, title: str, message: str, 
                          component: str, severity: str = "medium") -> Dict[str, Any]:
        """Create system alert"""
        try:
            alert = SystemAlert(
                alert_type=alert_type,
                title=title,
                message=message,
                component=component,
                severity=severity
            )
            
            self.system_alerts[alert.alert_id] = alert
            
            # Publish alert event
            self.event_store.publish_event({
                "event_type": "system_alert_created",
                "alert_id": alert.alert_id,
                "alert_type": alert_type,
                "severity": severity,
                "component": component,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "alert_id": alert.alert_id,
                "severity": severity,
                "created_at": alert.created_at.isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error creating system alert: {e}")
            return {"success": False, "error": str(e)}

    def _log_audit_action(self, user_id: str, action: str, resource_type: str, resource_id: str):
        """Log audit action"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address="127.0.0.1",  # Mock IP
                user_agent="Admin Dashboard"  # Mock user agent
            )
            
            self.audit_logs.append(audit_log)
            
            # Keep only last 1000 audit logs
            if len(self.audit_logs) > 1000:
                self.audit_logs = self.audit_logs[-1000:]

        except Exception as e:
            self.logger.error(f"Error logging audit action: {e}")

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            # Mock system health metrics
            unresolved_alerts = len([a for a in self.system_alerts.values() if not a.is_resolved])
            open_tickets = len([t for t in self.support_tickets.values() if t.status == SupportTicketStatus.OPEN])
            
            health_score = 100
            if unresolved_alerts > 5:
                health_score -= 20
            if open_tickets > 10:
                health_score -= 15
            
            return {
                "success": True,
                "health_score": max(health_score, 0),
                "status": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "critical",
                "metrics": {
                    "unresolved_alerts": unresolved_alerts,
                    "open_support_tickets": open_tickets,
                    "active_admin_users": len([u for u in self.admin_users.values() if u.is_active]),
                    "system_uptime_hours": 24 * 30  # Mock 30 days uptime
                },
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {"success": False, "error": str(e)}