from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import random

from ..models.redemption import TravelBooking, MerchandiseOrder, ExperienceBooking, RedemptionStatus
from ...shared.event_store import EventStore
from ...shared.logging import get_logger

class PartnerIntegrationService:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.logger = get_logger(__name__)
        self.travel_partners = ["MakeMyTrip", "Booking.com", "Expedia"]
        self.merchandise_partners = ["Amazon", "Flipkart", "Myntra"]
        self.experience_partners = ["BookMyShow", "Zomato", "Paytm Insider"]

    def process_travel_booking(self, booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """Process travel booking with partner APIs (mock)"""
        try:
            booking_type = booking_details.get("type", "flight")
            partner = random.choice(self.travel_partners)
            
            # Mock partner API call
            partner_response = self._mock_travel_api_call(booking_type, booking_details, partner)
            
            if partner_response["success"]:
                booking = TravelBooking(
                    customer_id=booking_details["customer_id"],
                    booking_type=booking_type,
                    points_used=booking_details["points_used"],
                    booking_details=booking_details,
                    partner_booking_ref=partner_response["booking_reference"],
                    status=RedemptionStatus.CONFIRMED,
                    total_cost=partner_response["total_cost"],
                    points_value=booking_details["points_used"] * 0.5,  # 1 point = 0.5 INR
                    additional_payment=partner_response["additional_payment"],
                    travel_date=datetime.fromisoformat(booking_details.get("travel_date", datetime.now().isoformat()))
                )

                # Publish event
                self.event_store.publish_event({
                    "event_type": "travel_booking_confirmed",
                    "customer_id": booking_details["customer_id"],
                    "booking_id": booking.booking_id,
                    "partner": partner,
                    "booking_reference": partner_response["booking_reference"],
                    "total_cost": partner_response["total_cost"],
                    "timestamp": datetime.now().isoformat()
                })

                self.logger.info(f"Travel booking confirmed with {partner}: {booking.booking_id}")

                return {
                    "success": True,
                    "booking_id": booking.booking_id,
                    "partner": partner,
                    "booking_reference": partner_response["booking_reference"],
                    "status": "confirmed",
                    "total_cost": partner_response["total_cost"],
                    "points_value": booking.points_value,
                    "additional_payment": partner_response["additional_payment"],
                    "confirmation_details": partner_response["confirmation_details"]
                }
            else:
                return {"success": False, "error": partner_response["error"]}

        except Exception as e:
            self.logger.error(f"Error processing travel booking: {e}")
            return {"success": False, "error": str(e)}

    def process_merchandise_order(self, order_details: Dict[str, Any]) -> Dict[str, Any]:
        """Process merchandise order with partner APIs (mock)"""
        try:
            partner = random.choice(self.merchandise_partners)
            
            # Mock partner API call
            partner_response = self._mock_merchandise_api_call(order_details, partner)
            
            if partner_response["success"]:
                order = MerchandiseOrder(
                    customer_id=order_details["customer_id"],
                    item_id=order_details["item_id"],
                    quantity=order_details.get("quantity", 1),
                    points_used=order_details["points_used"],
                    shipping_address=order_details["shipping_address"],
                    status=RedemptionStatus.CONFIRMED,
                    tracking_number=partner_response["tracking_number"],
                    estimated_delivery=datetime.now() + timedelta(days=partner_response["delivery_days"])
                )

                # Publish event
                self.event_store.publish_event({
                    "event_type": "merchandise_order_confirmed",
                    "customer_id": order_details["customer_id"],
                    "order_id": order.order_id,
                    "partner": partner,
                    "tracking_number": partner_response["tracking_number"],
                    "estimated_delivery": order.estimated_delivery.isoformat(),
                    "timestamp": datetime.now().isoformat()
                })

                self.logger.info(f"Merchandise order confirmed with {partner}: {order.order_id}")

                return {
                    "success": True,
                    "order_id": order.order_id,
                    "partner": partner,
                    "tracking_number": partner_response["tracking_number"],
                    "status": "confirmed",
                    "estimated_delivery": order.estimated_delivery.isoformat(),
                    "shipping_details": partner_response["shipping_details"]
                }
            else:
                return {"success": False, "error": partner_response["error"]}

        except Exception as e:
            self.logger.error(f"Error processing merchandise order: {e}")
            return {"success": False, "error": str(e)}

    def process_experience_booking(self, booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """Process experience booking with partner APIs (mock)"""
        try:
            partner = random.choice(self.experience_partners)
            
            # Mock partner API call
            partner_response = self._mock_experience_api_call(booking_details, partner)
            
            if partner_response["success"]:
                booking = ExperienceBooking(
                    customer_id=booking_details["customer_id"],
                    experience_id=booking_details["experience_id"],
                    points_used=booking_details["points_used"],
                    booking_details=booking_details,
                    status=RedemptionStatus.CONFIRMED,
                    experience_date=datetime.fromisoformat(booking_details.get("experience_date", datetime.now().isoformat())),
                    location=booking_details.get("location", ""),
                    participants=booking_details.get("participants", 1),
                    special_requests=booking_details.get("special_requests", ""),
                    confirmation_code=partner_response["confirmation_code"]
                )

                # Publish event
                self.event_store.publish_event({
                    "event_type": "experience_booking_confirmed",
                    "customer_id": booking_details["customer_id"],
                    "booking_id": booking.booking_id,
                    "partner": partner,
                    "confirmation_code": partner_response["confirmation_code"],
                    "experience_date": booking.experience_date.isoformat(),
                    "timestamp": datetime.now().isoformat()
                })

                self.logger.info(f"Experience booking confirmed with {partner}: {booking.booking_id}")

                return {
                    "success": True,
                    "booking_id": booking.booking_id,
                    "partner": partner,
                    "confirmation_code": partner_response["confirmation_code"],
                    "status": "confirmed",
                    "experience_date": booking.experience_date.isoformat(),
                    "location": booking.location,
                    "booking_details": partner_response["booking_details"]
                }
            else:
                return {"success": False, "error": partner_response["error"]}

        except Exception as e:
            self.logger.error(f"Error processing experience booking: {e}")
            return {"success": False, "error": str(e)}

    def _mock_travel_api_call(self, booking_type: str, details: Dict[str, Any], partner: str) -> Dict[str, Any]:
        """Mock travel partner API call"""
        try:
            # Simulate API processing time
            success_rate = 0.95  # 95% success rate
            
            if random.random() < success_rate:
                booking_ref = f"{partner.upper()}_{uuid.uuid4().hex[:8].upper()}"
                base_cost = details.get("estimated_cost", 10000)
                points_value = details["points_used"] * 0.5
                additional_payment = max(0, base_cost - points_value)
                
                return {
                    "success": True,
                    "booking_reference": booking_ref,
                    "total_cost": base_cost,
                    "additional_payment": additional_payment,
                    "confirmation_details": {
                        "partner": partner,
                        "booking_type": booking_type,
                        "confirmation_number": booking_ref,
                        "booking_status": "confirmed",
                        "payment_status": "completed"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Booking failed with {partner}. Please try again later."
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _mock_merchandise_api_call(self, details: Dict[str, Any], partner: str) -> Dict[str, Any]:
        """Mock merchandise partner API call"""
        try:
            success_rate = 0.98  # 98% success rate
            
            if random.random() < success_rate:
                tracking_number = f"{partner.upper()[:3]}{uuid.uuid4().hex[:10].upper()}"
                delivery_days = random.randint(3, 10)
                
                return {
                    "success": True,
                    "tracking_number": tracking_number,
                    "delivery_days": delivery_days,
                    "shipping_details": {
                        "partner": partner,
                        "shipping_method": "Standard Delivery",
                        "tracking_url": f"https://{partner.lower()}.com/track/{tracking_number}",
                        "estimated_delivery_days": delivery_days
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Order processing failed with {partner}. Item may be out of stock."
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _mock_experience_api_call(self, details: Dict[str, Any], partner: str) -> Dict[str, Any]:
        """Mock experience partner API call"""
        try:
            success_rate = 0.92  # 92% success rate
            
            if random.random() < success_rate:
                confirmation_code = f"{partner.upper()[:3]}{uuid.uuid4().hex[:6].upper()}"
                
                return {
                    "success": True,
                    "confirmation_code": confirmation_code,
                    "booking_details": {
                        "partner": partner,
                        "experience_name": details.get("experience_name", "Premium Experience"),
                        "confirmation_code": confirmation_code,
                        "booking_status": "confirmed",
                        "contact_info": f"support@{partner.lower()}.com",
                        "cancellation_policy": "Free cancellation up to 24 hours before experience"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Experience booking failed with {partner}. Selected date may not be available."
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_partner_status(self, partner_name: str) -> Dict[str, Any]:
        """Get partner service status (mock)"""
        try:
            # Mock partner health check
            status = random.choice(["healthy", "degraded", "down"])
            response_time = random.randint(100, 2000)  # milliseconds
            
            return {
                "partner": partner_name,
                "status": status,
                "response_time_ms": response_time,
                "last_checked": datetime.now().isoformat(),
                "services": {
                    "booking": status == "healthy",
                    "cancellation": status in ["healthy", "degraded"],
                    "status_check": True
                }
            }

        except Exception as e:
            self.logger.error(f"Error checking partner status: {e}")
            return {"partner": partner_name, "status": "unknown", "error": str(e)}

    def get_all_partners_status(self) -> Dict[str, Any]:
        """Get status of all partners"""
        try:
            all_partners = self.travel_partners + self.merchandise_partners + self.experience_partners
            partner_statuses = []
            
            for partner in all_partners:
                status = self.get_partner_status(partner)
                partner_statuses.append(status)
            
            healthy_count = len([p for p in partner_statuses if p.get("status") == "healthy"])
            
            return {
                "total_partners": len(all_partners),
                "healthy_partners": healthy_count,
                "overall_health": "healthy" if healthy_count > len(all_partners) * 0.8 else "degraded",
                "partner_details": partner_statuses,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error getting all partners status: {e}")
            return {"error": str(e)}