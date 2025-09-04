from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel

from ..services.admin_service import AdminService
from ..models.admin import AdminRole, ConfigurationType
from ...shared.event_store import EventStore
from ...shared.logging import get_logger

# Pydantic models
class CreateAdminUserRequest(BaseModel):
    username: str
    email: str
    full_name: str
    role: str
    created_by: str

class UpdateConfigurationRequest(BaseModel):
    config_type: str
    config_data: Dict
    updated_by: str

class CreateSupportTicketRequest(BaseModel):
    customer_id: str
    subject: str
    description: str
    category: str
    priority: str = "medium"

class AssignTicketRequest(BaseModel):
    assigned_to: str
    assigned_by: str

class ResolveTicketRequest(BaseModel):
    resolution: str
    resolved_by: str

class GenerateReportRequest(BaseModel):
    report_type: str
    parameters: Dict
    generated_by: str

class CreateAlertRequest(BaseModel):
    alert_type: str
    title: str
    message: str
    component: str
    severity: str = "medium"

# Initialize services
event_store = EventStore()
admin_service = AdminService(event_store)

router = APIRouter(prefix="/api/admin", tags=["Administration & Operations"])
logger = get_logger(__name__)

# Admin user management
@router.post("/users")
async def create_admin_user(request: CreateAdminUserRequest):
    """Create a new admin user"""
    try:
        role = AdminRole(request.role)
        result = admin_service.create_admin_user(
            request.username,
            request.email,
            request.full_name,
            role,
            request.created_by
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid admin role")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def get_admin_users():
    """Get all admin users"""
    try:
        users = []
        for user in admin_service.admin_users.values():
            users.append({
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "permissions": user.permissions,
                "is_active": user.is_active,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat()
            })
        
        return {
            "success": True,
            "total_users": len(users),
            "users": users
        }
        
    except Exception as e:
        logger.error(f"Error getting admin users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Program configuration
@router.post("/configuration")
async def update_configuration(request: UpdateConfigurationRequest):
    """Update program configuration"""
    try:
        config_type = ConfigurationType(request.config_type)
        result = admin_service.update_program_configuration(
            config_type,
            request.config_data,
            request.updated_by
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid configuration type")
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configuration")
async def get_configurations():
    """Get all active configurations"""
    try:
        configs = []
        for config in admin_service.configurations.values():
            if config.is_active:
                configs.append({
                    "config_id": config.config_id,
                    "config_type": config.config_type.value,
                    "name": config.name,
                    "description": config.description,
                    "config_data": config.config_data,
                    "effective_from": config.effective_from.isoformat(),
                    "created_by": config.created_by,
                    "created_at": config.created_at.isoformat()
                })
        
        return {
            "success": True,
            "total_configurations": len(configs),
            "configurations": configs
        }
        
    except Exception as e:
        logger.error(f"Error getting configurations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configuration/{config_type}")
async def get_configuration_by_type(config_type: str):
    """Get configuration by type"""
    try:
        config_type_enum = ConfigurationType(config_type)
        
        for config in admin_service.configurations.values():
            if config.config_type == config_type_enum and config.is_active:
                return {
                    "success": True,
                    "configuration": {
                        "config_id": config.config_id,
                        "config_type": config.config_type.value,
                        "name": config.name,
                        "description": config.description,
                        "config_data": config.config_data,
                        "effective_from": config.effective_from.isoformat(),
                        "created_by": config.created_by
                    }
                }
        
        raise HTTPException(status_code=404, detail="Configuration not found")
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid configuration type")
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Support ticket management
@router.post("/support/tickets")
async def create_support_ticket(request: CreateSupportTicketRequest):
    """Create a support ticket"""
    try:
        result = admin_service.create_support_ticket(
            request.customer_id,
            request.subject,
            request.description,
            request.category,
            request.priority
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error creating support ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/support/tickets")
async def get_support_tickets(status: Optional[str] = None, assigned_to: Optional[str] = None):
    """Get support tickets with optional filters"""
    try:
        tickets = []
        for ticket in admin_service.support_tickets.values():
            # Apply filters
            if status and ticket.status.value != status:
                continue
            if assigned_to and ticket.assigned_to != assigned_to:
                continue
                
            tickets.append({
                "ticket_id": ticket.ticket_id,
                "customer_id": ticket.customer_id,
                "subject": ticket.subject,
                "category": ticket.category,
                "priority": ticket.priority,
                "status": ticket.status.value,
                "assigned_to": ticket.assigned_to,
                "created_at": ticket.created_at.isoformat(),
                "updated_at": ticket.updated_at.isoformat(),
                "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None
            })
        
        return {
            "success": True,
            "total_tickets": len(tickets),
            "tickets": tickets
        }
        
    except Exception as e:
        logger.error(f"Error getting support tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/support/tickets/{ticket_id}/assign")
async def assign_support_ticket(ticket_id: str, request: AssignTicketRequest):
    """Assign support ticket to admin user"""
    try:
        result = admin_service.assign_support_ticket(
            ticket_id,
            request.assigned_to,
            request.assigned_by
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error assigning support ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/support/tickets/{ticket_id}/resolve")
async def resolve_support_ticket(ticket_id: str, request: ResolveTicketRequest):
    """Resolve support ticket"""
    try:
        result = admin_service.resolve_support_ticket(
            ticket_id,
            request.resolution,
            request.resolved_by
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error resolving support ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Business intelligence and reporting
@router.post("/reports/generate")
async def generate_business_report(request: GenerateReportRequest):
    """Generate business intelligence report"""
    try:
        result = admin_service.generate_business_report(
            request.report_type,
            request.parameters,
            request.generated_by
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports")
async def get_business_reports():
    """Get all business reports"""
    try:
        reports = []
        for report in admin_service.business_reports.values():
            reports.append({
                "report_id": report.report_id,
                "report_type": report.report_type,
                "title": report.title,
                "description": report.description,
                "generated_by": report.generated_by,
                "generated_at": report.generated_at.isoformat(),
                "parameters": report.parameters
            })
        
        return {
            "success": True,
            "total_reports": len(reports),
            "reports": reports
        }
        
    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/{report_id}")
async def get_business_report(report_id: str):
    """Get specific business report with data"""
    try:
        report = admin_service.business_reports.get(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {
            "success": True,
            "report": {
                "report_id": report.report_id,
                "report_type": report.report_type,
                "title": report.title,
                "description": report.description,
                "parameters": report.parameters,
                "data": report.data,
                "generated_by": report.generated_by,
                "generated_at": report.generated_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System monitoring and alerts
@router.post("/alerts")
async def create_system_alert(request: CreateAlertRequest):
    """Create system alert"""
    try:
        result = admin_service.create_system_alert(
            request.alert_type,
            request.title,
            request.message,
            request.component,
            request.severity
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error creating system alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_system_alerts(resolved: Optional[bool] = None):
    """Get system alerts"""
    try:
        alerts = []
        for alert in admin_service.system_alerts.values():
            if resolved is not None and alert.is_resolved != resolved:
                continue
                
            alerts.append({
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity,
                "component": alert.component,
                "is_resolved": alert.is_resolved,
                "resolved_by": alert.resolved_by,
                "created_at": alert.created_at.isoformat(),
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            })
        
        return {
            "success": True,
            "total_alerts": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/health")
async def get_system_health():
    """Get system health status"""
    try:
        result = admin_service.get_system_health()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit/logs")
async def get_audit_logs(limit: int = 100):
    """Get audit logs"""
    try:
        logs = []
        recent_logs = admin_service.audit_logs[-limit:] if len(admin_service.audit_logs) > limit else admin_service.audit_logs
        
        for log in reversed(recent_logs):  # Most recent first
            logs.append({
                "log_id": log.log_id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address
            })
        
        return {
            "success": True,
            "total_logs": len(logs),
            "logs": logs
        }
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))