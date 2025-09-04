from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

from ..models.redemption import (
    RedemptionRequest, RedemptionItem, RedemptionType, RedemptionStatus,
    FulfillmentStatus, CashbackRequest, TravelBooking, MerchandiseOrder, ExperienceBooking
)
from ..repositories.redemption_repository import RedemptionRepository
from ...shared.event_store import EventStore
from ...shared.logging import get_logger

class RedemptionOrchestrationService:
    def __init__(self, redemption_repo: RedemptionRepository, event_store: EventStore):
        self.redemption_repo = redemption_repo
        self.event_store = event_store
        self.logger = get_logger(__name__)

    def initiate_redemption(self, customer_id: str, item_id: str, 
                          request_details: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate a redemption request"""
        try:
            # Find the item in active catalogs
            item = self._find_redemption_item(item_id)
            if not item:
                return {"success": False, "error": "Redemption item not found"}

            if not item.availability:
                return {"success": False, "error": "Item is currently unavailable"}

            # Validate customer points (would integrate with points service)
            customer_points = self._get_customer_points(customer_id)
            if customer_points < item.points_required:
                return {"success": False, "error": "Insufficient points"}

            # Create redemption request
            request = RedemptionRequest(
                customer_id=customer_id,
                item_id=item_id,
                points_used=item.points_required,
                redemption_type=item.redemption_type,
                status=RedemptionStatus.PENDING,
                request_details=request_details
            )

            # Save request
            self.redemption_repo.create_redemption_request(request)

            # Publish event
            self.event_store.publish_event({
                "event_type": "redemption_initiated",
                "customer_id": customer_id,
                "request_id": request.request_id,
                "item_id": item_id,
                "points_used": item.points_required,
                "redemption_type": item.redemption_type.value,
                "timestamp": datetime.now().isoformat()
            })

            # Route to appropriate fulfillment service
            fulfillment_result = self._route_to_fulfillment(request, item)

            self.logger.info(f"Redemption initiated for customer {customer_id}, request {request.request_id}")
            
            return {
                "success": True,
                "request_id": request.request_id,
                "status": request.status.value,
                "estimated_fulfillment": request.estimated_fulfillment.isoformat() if request.estimated_fulfillment else None,
                "fulfillment_details": fulfillment_result
            }

        except Exception as e:
            self.logger.error(f"Error initiating redemption: {e}")
            return {"success": False, "error": str(e)}

    def _find_redemption_item(self, item_id: str) -> Optional[RedemptionItem]:
        """Find redemption item in active catalogs"""
        for catalog in self.redemption_repo.get_active_catalogs():
            for item in catalog.items:
                if item.item_id == item_id:
                    return item
        return None

    def _get_customer_points(self, customer_id: str) -> int:
        """Get customer's available points (mock implementation)"""
        # In real implementation, this would call the points service
        return 10000  # Mock sufficient points

    def _route_to_fulfillment(self, request: RedemptionRequest, item: RedemptionItem) -> Dict[str, Any]:
        """Route redemption to appropriate fulfillment service"""
        try:
            if request.redemption_type == RedemptionType.CASHBACK:
                return self._process_cashback_fulfillment(request)
            elif request.redemption_type == RedemptionType.TRAVEL:
                return self._process_travel_fulfillment(request, item)
            elif request.redemption_type == RedemptionType.MERCHANDISE:
                return self._process_merchandise_fulfillment(request, item)
            elif request.redemption_type == RedemptionType.EXPERIENCE:
                return self._process_experience_fulfillment(request, item)
            else:
                return {"status": "unsupported_type"}

        except Exception as e:
            self.logger.error(f"Error in fulfillment routing: {e}")
            return {"status": "error", "message": str(e)}

    def _process_cashback_fulfillment(self, request: RedemptionRequest) -> Dict[str, Any]:
        """Process cashback redemption"""
        # Update request status
        request.status = RedemptionStatus.PROCESSING
        request.fulfillment_status = FulfillmentStatus.IN_PROGRESS
        request.estimated_fulfillment = datetime.now() + timedelta(days=3)
        
        self.redemption_repo.update_redemption_request(request)
        
        return {
            "status": "processing",
            "estimated_completion": "3 business days",
            "next_steps": "Cashback will be processed to your registered bank account"
        }

    def _process_travel_fulfillment(self, request: RedemptionRequest, item: RedemptionItem) -> Dict[str, Any]:
        """Process travel booking redemption"""
        request.status = RedemptionStatus.PROCESSING
        request.fulfillment_status = FulfillmentStatus.IN_PROGRESS
        request.estimated_fulfillment = datetime.now() + timedelta(hours=24)
        
        self.redemption_repo.update_redemption_request(request)
        
        return {
            "status": "processing",
            "estimated_completion": "24 hours",
            "next_steps": "Travel booking confirmation will be sent via email"
        }

    def _process_merchandise_fulfillment(self, request: RedemptionRequest, item: RedemptionItem) -> Dict[str, Any]:
        """Process merchandise order redemption"""
        request.status = RedemptionStatus.CONFIRMED
        request.fulfillment_status = FulfillmentStatus.IN_PROGRESS
        request.estimated_fulfillment = datetime.now() + timedelta(days=7)
        
        self.redemption_repo.update_redemption_request(request)
        
        return {
            "status": "confirmed",
            "estimated_completion": "7-10 business days",
            "next_steps": "Item will be shipped to your registered address"
        }

    def _process_experience_fulfillment(self, request: RedemptionRequest, item: RedemptionItem) -> Dict[str, Any]:
        """Process experience booking redemption"""
        request.status = RedemptionStatus.PROCESSING
        request.fulfillment_status = FulfillmentStatus.IN_PROGRESS
        request.estimated_fulfillment = datetime.now() + timedelta(days=2)
        
        self.redemption_repo.update_redemption_request(request)
        
        return {
            "status": "processing",
            "estimated_completion": "48 hours",
            "next_steps": "Experience booking details will be confirmed via email"
        }

    def get_redemption_status(self, request_id: str) -> Dict[str, Any]:
        """Get current status of redemption request"""
        try:
            request = self.redemption_repo.get_redemption_request(request_id)
            if not request:
                return {"success": False, "error": "Redemption request not found"}

            return {
                "success": True,
                "request_id": request.request_id,
                "status": request.status.value,
                "fulfillment_status": request.fulfillment_status.value,
                "points_used": request.points_used,
                "redemption_type": request.redemption_type.value,
                "estimated_fulfillment": request.estimated_fulfillment.isoformat() if request.estimated_fulfillment else None,
                "actual_fulfillment": request.actual_fulfillment.isoformat() if request.actual_fulfillment else None,
                "created_at": request.created_at.isoformat(),
                "fulfillment_details": request.fulfillment_details
            }

        except Exception as e:
            self.logger.error(f"Error getting redemption status: {e}")
            return {"success": False, "error": str(e)}

    def cancel_redemption(self, request_id: str, reason: str) -> Dict[str, Any]:
        """Cancel a redemption request"""
        try:
            request = self.redemption_repo.get_redemption_request(request_id)
            if not request:
                return {"success": False, "error": "Redemption request not found"}

            if request.status in [RedemptionStatus.FULFILLED, RedemptionStatus.CANCELLED]:
                return {"success": False, "error": "Cannot cancel completed or already cancelled redemption"}

            # Update status
            request.status = RedemptionStatus.CANCELLED
            request.fulfillment_details["cancellation_reason"] = reason
            request.fulfillment_details["cancelled_at"] = datetime.now().isoformat()
            
            self.redemption_repo.update_redemption_request(request)

            # Publish cancellation event
            self.event_store.publish_event({
                "event_type": "redemption_cancelled",
                "customer_id": request.customer_id,
                "request_id": request.request_id,
                "points_refunded": request.points_used,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })

            self.logger.info(f"Redemption {request_id} cancelled: {reason}")
            
            return {
                "success": True,
                "request_id": request_id,
                "status": "cancelled",
                "points_refunded": request.points_used
            }

        except Exception as e:
            self.logger.error(f"Error cancelling redemption: {e}")
            return {"success": False, "error": str(e)}

    def get_customer_redemption_history(self, customer_id: str) -> Dict[str, Any]:
        """Get customer's redemption history"""
        try:
            redemptions = self.redemption_repo.get_customer_redemptions(customer_id)
            
            history = []
            for redemption in sorted(redemptions, key=lambda x: x.created_at, reverse=True):
                history.append({
                    "request_id": redemption.request_id,
                    "redemption_type": redemption.redemption_type.value,
                    "points_used": redemption.points_used,
                    "status": redemption.status.value,
                    "fulfillment_status": redemption.fulfillment_status.value,
                    "created_at": redemption.created_at.isoformat(),
                    "estimated_fulfillment": redemption.estimated_fulfillment.isoformat() if redemption.estimated_fulfillment else None
                })

            return {
                "success": True,
                "customer_id": customer_id,
                "total_redemptions": len(history),
                "redemption_history": history
            }

        except Exception as e:
            self.logger.error(f"Error getting redemption history: {e}")
            return {"success": False, "error": str(e)}