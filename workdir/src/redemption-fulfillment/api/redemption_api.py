from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from ..services.redemption_orchestration_service import RedemptionOrchestrationService
from ..services.cashback_processing_service import CashbackProcessingService
from ..services.partner_integration_service import PartnerIntegrationService
from ..repositories.redemption_repository import RedemptionRepository
from ...shared.event_store import EventStore
from ...shared.logging import get_logger

# Pydantic models for API requests
class RedemptionRequest(BaseModel):
    customer_id: str
    item_id: str
    request_details: Dict[str, Any]

class CashbackRequest(BaseModel):
    customer_id: str
    points_to_redeem: int
    bank_account: str

class TravelBookingRequest(BaseModel):
    customer_id: str
    points_used: int
    booking_type: str  # flight, hotel, car_rental
    travel_date: str
    destination: str
    estimated_cost: float
    booking_details: Dict[str, Any]

class MerchandiseOrderRequest(BaseModel):
    customer_id: str
    item_id: str
    points_used: int
    quantity: int = 1
    shipping_address: Dict[str, str]

class ExperienceBookingRequest(BaseModel):
    customer_id: str
    experience_id: str
    points_used: int
    experience_date: str
    location: str
    participants: int = 1
    special_requests: str = ""

# Initialize services
event_store = EventStore()
redemption_repo = RedemptionRepository()
redemption_service = RedemptionOrchestrationService(redemption_repo, event_store)
cashback_service = CashbackProcessingService(redemption_repo, event_store)
partner_service = PartnerIntegrationService(event_store)

router = APIRouter(prefix="/api/redemption", tags=["Redemption & Fulfillment"])
logger = get_logger(__name__)

@router.get("/catalog")
async def get_redemption_catalog(customer_tier: Optional[str] = None):
    """Get available redemption catalog"""
    try:
        catalogs = redemption_repo.get_active_catalogs()
        
        if not catalogs:
            # Create default catalog if none exists
            from ..models.redemption import RedemptionCatalog, RedemptionItem, RedemptionType
            
            default_catalog = RedemptionCatalog(
                name="Premium Rewards Catalog",
                description="Exclusive rewards for PremiumCard members"
            )
            
            # Add sample items
            default_catalog.items = [
                RedemptionItem(
                    item_id="CB_100",
                    name="Cashback - 100 Points",
                    description="Convert 100 points to 50 INR cashback",
                    redemption_type=RedemptionType.CASHBACK,
                    points_required=100,
                    category="cashback"
                ),
                RedemptionItem(
                    item_id="FLIGHT_DOMESTIC",
                    name="Domestic Flight Booking",
                    description="Book domestic flights using points",
                    redemption_type=RedemptionType.TRAVEL,
                    points_required=5000,
                    category="travel",
                    tier_requirement="silver"
                ),
                RedemptionItem(
                    item_id="SMARTPHONE_PREMIUM",
                    name="Premium Smartphone",
                    description="Latest smartphone model",
                    redemption_type=RedemptionType.MERCHANDISE,
                    points_required=50000,
                    category="electronics",
                    tier_requirement="gold"
                ),
                RedemptionItem(
                    item_id="SPA_EXPERIENCE",
                    name="Luxury Spa Experience",
                    description="Full day spa treatment at premium location",
                    redemption_type=RedemptionType.EXPERIENCE,
                    points_required=8000,
                    category="wellness",
                    tier_requirement="silver"
                )
            ]
            
            redemption_repo.create_catalog(default_catalog)
            catalogs = [default_catalog]
        
        catalog_data = []
        for catalog in catalogs:
            available_items = catalog.get_available_items(customer_tier)
            catalog_data.append({
                "catalog_id": catalog.catalog_id,
                "name": catalog.name,
                "description": catalog.description,
                "total_items": len(available_items),
                "items": [
                    {
                        "item_id": item.item_id,
                        "name": item.name,
                        "description": item.description,
                        "redemption_type": item.redemption_type.value,
                        "points_required": item.points_required,
                        "category": item.category,
                        "tier_requirement": item.tier_requirement,
                        "availability": item.availability
                    } for item in available_items
                ]
            })
        
        return {"success": True, "catalogs": catalog_data}
        
    except Exception as e:
        logger.error(f"Error getting redemption catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initiate")
async def initiate_redemption(request: RedemptionRequest):
    """Initiate a redemption request"""
    try:
        result = redemption_service.initiate_redemption(
            request.customer_id,
            request.item_id,
            request.request_details
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error initiating redemption: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{request_id}")
async def get_redemption_status(request_id: str):
    """Get redemption request status"""
    try:
        result = redemption_service.get_redemption_status(request_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting redemption status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel/{request_id}")
async def cancel_redemption(request_id: str, reason: str = "Customer request"):
    """Cancel a redemption request"""
    try:
        result = redemption_service.cancel_redemption(request_id, reason)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error cancelling redemption: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{customer_id}")
async def get_redemption_history(customer_id: str):
    """Get customer's redemption history"""
    try:
        result = redemption_service.get_customer_redemption_history(customer_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting redemption history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cashback endpoints
@router.post("/cashback/process")
async def process_cashback(request: CashbackRequest):
    """Process cashback redemption"""
    try:
        result = cashback_service.process_cashback_redemption(
            request.customer_id,
            request.points_to_redeem,
            request.bank_account
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error processing cashback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cashback/preview/{points}")
async def get_cashback_preview(points: int):
    """Get cashback calculation preview"""
    try:
        result = cashback_service.calculate_cashback_preview(points)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error calculating cashback preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cashback/status/{request_id}")
async def get_cashback_status(request_id: str):
    """Get cashback request status"""
    try:
        result = cashback_service.get_cashback_status(request_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting cashback status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cashback/history/{customer_id}")
async def get_cashback_history(customer_id: str):
    """Get customer's cashback history"""
    try:
        result = cashback_service.get_customer_cashback_history(customer_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error getting cashback history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Partner integration endpoints
@router.post("/travel/book")
async def book_travel(request: TravelBookingRequest):
    """Book travel through partner integration"""
    try:
        booking_details = {
            "customer_id": request.customer_id,
            "points_used": request.points_used,
            "type": request.booking_type,
            "travel_date": request.travel_date,
            "destination": request.destination,
            "estimated_cost": request.estimated_cost,
            **request.booking_details
        }
        
        result = partner_service.process_travel_booking(booking_details)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error booking travel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/merchandise/order")
async def order_merchandise(request: MerchandiseOrderRequest):
    """Order merchandise through partner integration"""
    try:
        order_details = {
            "customer_id": request.customer_id,
            "item_id": request.item_id,
            "points_used": request.points_used,
            "quantity": request.quantity,
            "shipping_address": request.shipping_address
        }
        
        result = partner_service.process_merchandise_order(order_details)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error ordering merchandise: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/experience/book")
async def book_experience(request: ExperienceBookingRequest):
    """Book experience through partner integration"""
    try:
        booking_details = {
            "customer_id": request.customer_id,
            "experience_id": request.experience_id,
            "points_used": request.points_used,
            "experience_date": request.experience_date,
            "location": request.location,
            "participants": request.participants,
            "special_requests": request.special_requests
        }
        
        result = partner_service.process_experience_booking(booking_details)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error booking experience: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/partners/status")
async def get_partners_status():
    """Get status of all partner integrations"""
    try:
        result = partner_service.get_all_partners_status()
        return result
        
    except Exception as e:
        logger.error(f"Error getting partners status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/partners/{partner_name}/status")
async def get_partner_status(partner_name: str):
    """Get status of specific partner"""
    try:
        result = partner_service.get_partner_status(partner_name)
        return result
        
    except Exception as e:
        logger.error(f"Error getting partner status: {e}")
        raise HTTPException(status_code=500, detail=str(e))