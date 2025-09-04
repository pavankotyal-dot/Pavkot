from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid

from ..models.redemption import CashbackRequest, RedemptionStatus
from ..repositories.redemption_repository import RedemptionRepository
from ...shared.event_store import EventStore
from ...shared.logging import get_logger

class CashbackProcessingService:
    def __init__(self, redemption_repo: RedemptionRepository, event_store: EventStore):
        self.redemption_repo = redemption_repo
        self.event_store = event_store
        self.logger = get_logger(__name__)
        self.cashback_rate = 0.5  # 100 points = 50 INR (50% conversion)
        self.processing_fee_rate = 0.02  # 2% processing fee

    def process_cashback_redemption(self, customer_id: str, points_to_redeem: int, 
                                  bank_account: str) -> Dict[str, Any]:
        """Process cashback redemption request"""
        try:
            # Validate minimum redemption
            min_points = 100  # Minimum 100 points for cashback
            if points_to_redeem < min_points:
                return {"success": False, "error": f"Minimum {min_points} points required for cashback"}

            # Calculate cashback amount
            cashback_amount = points_to_redeem * self.cashback_rate
            processing_fee = cashback_amount * self.processing_fee_rate
            net_amount = cashback_amount - processing_fee

            # Validate customer points balance (mock implementation)
            customer_points = self._get_customer_points(customer_id)
            if customer_points < points_to_redeem:
                return {"success": False, "error": "Insufficient points balance"}

            # Create cashback request
            cashback_request = CashbackRequest(
                customer_id=customer_id,
                points_redeemed=points_to_redeem,
                cashback_amount=cashback_amount,
                bank_account=bank_account,
                status=RedemptionStatus.PENDING,
                processing_fee=processing_fee,
                net_amount=net_amount
            )

            # Save request
            self.redemption_repo.create_cashback_request(cashback_request)

            # Initiate bank transfer (mock)
            transfer_result = self._initiate_bank_transfer(cashback_request)
            
            if transfer_result["success"]:
                cashback_request.status = RedemptionStatus.PROCESSING
                cashback_request.transaction_reference = transfer_result["transaction_ref"]
                self.redemption_repo.update_cashback_request(cashback_request)

                # Publish event
                self.event_store.publish_event({
                    "event_type": "cashback_processing_initiated",
                    "customer_id": customer_id,
                    "request_id": cashback_request.request_id,
                    "points_redeemed": points_to_redeem,
                    "cashback_amount": cashback_amount,
                    "net_amount": net_amount,
                    "transaction_reference": transfer_result["transaction_ref"],
                    "timestamp": datetime.now().isoformat()
                })

                self.logger.info(f"Cashback processing initiated for customer {customer_id}, amount: {net_amount}")

                return {
                    "success": True,
                    "request_id": cashback_request.request_id,
                    "points_redeemed": points_to_redeem,
                    "cashback_amount": cashback_amount,
                    "processing_fee": processing_fee,
                    "net_amount": net_amount,
                    "transaction_reference": transfer_result["transaction_ref"],
                    "estimated_completion": "3-5 business days",
                    "status": "processing"
                }
            else:
                cashback_request.status = RedemptionStatus.FAILED
                self.redemption_repo.update_cashback_request(cashback_request)
                return {"success": False, "error": "Bank transfer initiation failed"}

        except Exception as e:
            self.logger.error(f"Error processing cashback redemption: {e}")
            return {"success": False, "error": str(e)}

    def _get_customer_points(self, customer_id: str) -> int:
        """Get customer's available points (mock implementation)"""
        # In real implementation, this would call the points service
        return 10000  # Mock sufficient points

    def _initiate_bank_transfer(self, cashback_request: CashbackRequest) -> Dict[str, Any]:
        """Initiate bank transfer (mock implementation)"""
        try:
            # Mock bank API call
            transaction_ref = f"TXN_{uuid.uuid4().hex[:8].upper()}"
            
            # Simulate processing delay
            processing_time = datetime.now() + timedelta(days=3)
            
            # Mock successful response
            return {
                "success": True,
                "transaction_ref": transaction_ref,
                "status": "initiated",
                "estimated_completion": processing_time.isoformat(),
                "bank_response": {
                    "status_code": "200",
                    "message": "Transfer initiated successfully",
                    "reference": transaction_ref
                }
            }

        except Exception as e:
            self.logger.error(f"Error initiating bank transfer: {e}")
            return {"success": False, "error": str(e)}

    def complete_cashback_processing(self, request_id: str, 
                                   bank_confirmation: Dict[str, Any]) -> Dict[str, Any]:
        """Complete cashback processing with bank confirmation"""
        try:
            cashback_request = self.redemption_repo.get_cashback_request(request_id)
            if not cashback_request:
                return {"success": False, "error": "Cashback request not found"}

            if cashback_request.status != RedemptionStatus.PROCESSING:
                return {"success": False, "error": "Request is not in processing status"}

            # Update status based on bank confirmation
            if bank_confirmation.get("status") == "completed":
                cashback_request.status = RedemptionStatus.FULFILLED
                cashback_request.processed_at = datetime.now()
                
                # Publish completion event
                self.event_store.publish_event({
                    "event_type": "cashback_completed",
                    "customer_id": cashback_request.customer_id,
                    "request_id": request_id,
                    "net_amount": cashback_request.net_amount,
                    "bank_reference": bank_confirmation.get("bank_reference"),
                    "timestamp": datetime.now().isoformat()
                })

                self.logger.info(f"Cashback completed for request {request_id}")
                
            else:
                cashback_request.status = RedemptionStatus.FAILED
                
                # Publish failure event
                self.event_store.publish_event({
                    "event_type": "cashback_failed",
                    "customer_id": cashback_request.customer_id,
                    "request_id": request_id,
                    "failure_reason": bank_confirmation.get("error_message"),
                    "timestamp": datetime.now().isoformat()
                })

            self.redemption_repo.update_cashback_request(cashback_request)

            return {
                "success": True,
                "request_id": request_id,
                "status": cashback_request.status.value,
                "processed_at": cashback_request.processed_at.isoformat() if cashback_request.processed_at else None
            }

        except Exception as e:
            self.logger.error(f"Error completing cashback processing: {e}")
            return {"success": False, "error": str(e)}

    def get_cashback_status(self, request_id: str) -> Dict[str, Any]:
        """Get cashback request status"""
        try:
            cashback_request = self.redemption_repo.get_cashback_request(request_id)
            if not cashback_request:
                return {"success": False, "error": "Cashback request not found"}

            return {
                "success": True,
                "request_id": request_id,
                "customer_id": cashback_request.customer_id,
                "points_redeemed": cashback_request.points_redeemed,
                "cashback_amount": cashback_request.cashback_amount,
                "processing_fee": cashback_request.processing_fee,
                "net_amount": cashback_request.net_amount,
                "status": cashback_request.status.value,
                "transaction_reference": cashback_request.transaction_reference,
                "created_at": cashback_request.created_at.isoformat(),
                "processed_at": cashback_request.processed_at.isoformat() if cashback_request.processed_at else None
            }

        except Exception as e:
            self.logger.error(f"Error getting cashback status: {e}")
            return {"success": False, "error": str(e)}

    def get_customer_cashback_history(self, customer_id: str) -> Dict[str, Any]:
        """Get customer's cashback history"""
        try:
            cashback_requests = self.redemption_repo.get_customer_cashbacks(customer_id)
            
            history = []
            total_cashback = 0.0
            total_points_redeemed = 0

            for request in sorted(cashback_requests, key=lambda x: x.created_at, reverse=True):
                history.append({
                    "request_id": request.request_id,
                    "points_redeemed": request.points_redeemed,
                    "cashback_amount": request.cashback_amount,
                    "net_amount": request.net_amount,
                    "status": request.status.value,
                    "created_at": request.created_at.isoformat(),
                    "processed_at": request.processed_at.isoformat() if request.processed_at else None
                })

                if request.status == RedemptionStatus.FULFILLED:
                    total_cashback += request.net_amount
                    total_points_redeemed += request.points_redeemed

            return {
                "success": True,
                "customer_id": customer_id,
                "total_requests": len(history),
                "total_cashback_received": total_cashback,
                "total_points_redeemed": total_points_redeemed,
                "cashback_history": history
            }

        except Exception as e:
            self.logger.error(f"Error getting cashback history: {e}")
            return {"success": False, "error": str(e)}

    def calculate_cashback_preview(self, points: int) -> Dict[str, Any]:
        """Calculate cashback preview for given points"""
        try:
            if points < 100:
                return {
                    "success": False,
                    "error": "Minimum 100 points required for cashback"
                }

            cashback_amount = points * self.cashback_rate
            processing_fee = cashback_amount * self.processing_fee_rate
            net_amount = cashback_amount - processing_fee

            return {
                "success": True,
                "points": points,
                "cashback_amount": cashback_amount,
                "processing_fee": processing_fee,
                "net_amount": net_amount,
                "conversion_rate": self.cashback_rate,
                "processing_fee_rate": self.processing_fee_rate
            }

        except Exception as e:
            self.logger.error(f"Error calculating cashback preview: {e}")
            return {"success": False, "error": str(e)}