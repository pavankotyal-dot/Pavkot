"""REST API endpoints for Customer & Account Management unit."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
from shared.event_store import EventStore
from ..repositories.customer_repository import CustomerRepository, OnboardingRepository
from ..services.registration_service import RegistrationService
from ..services.onboarding_service import OnboardingService
from ..services.profile_service import ProfileService
from ..services.tier_display_service import TierDisplayService

# Pydantic models for request/response
class CustomerRegistrationRequest(BaseModel):
    email: EmailStr
    name: str
    phone: str
    card_number: str

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class CommunicationPreferencesRequest(BaseModel):
    email: Optional[bool] = None
    sms: Optional[bool] = None
    push: Optional[bool] = None
    in_app: Optional[bool] = None

class CustomerAPI:
    def __init__(self):
        self.app = FastAPI(title="Customer & Account Management API", version="1.0.0")
        
        # Initialize repositories and services
        self.event_store = EventStore()
        self.customer_repo = CustomerRepository()
        self.onboarding_repo = OnboardingRepository()
        
        self.registration_service = RegistrationService(
            self.event_store, self.customer_repo, self.onboarding_repo
        )
        self.onboarding_service = OnboardingService(
            self.event_store, self.customer_repo, self.onboarding_repo
        )
        self.profile_service = ProfileService(self.event_store, self.customer_repo)
        self.tier_display_service = TierDisplayService(self.event_store, self.customer_repo)
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.post("/api/v1/customers/register")
        async def register_customer(request: CustomerRegistrationRequest):
            """Register a new customer."""
            result = self.registration_service.register_customer(request.dict())
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.get("/api/v1/customers/{customer_id}/profile")
        async def get_customer_profile(customer_id: str):
            """Get customer profile information."""
            result = self.registration_service.get_customer_profile(customer_id)
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            return result
        
        @self.app.put("/api/v1/customers/{customer_id}/profile")
        async def update_customer_profile(customer_id: str, request: ProfileUpdateRequest):
            """Update customer profile information."""
            updates = {k: v for k, v in request.dict().items() if v is not None}
            if not updates:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            result = self.profile_service.update_profile(customer_id, updates)
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.get("/api/v1/customers/{customer_id}/tier-status")
        async def get_tier_status(customer_id: str):
            """Get customer tier status and benefits."""
            result = self.tier_display_service.get_tier_status(customer_id)
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            return result
        
        @self.app.put("/api/v1/customers/{customer_id}/preferences")
        async def update_communication_preferences(customer_id: str, request: CommunicationPreferencesRequest):
            """Update customer communication preferences."""
            preferences = {k: v for k, v in request.dict().items() if v is not None}
            if not preferences:
                raise HTTPException(status_code=400, detail="No preferences to update")
            
            result = self.profile_service.update_communication_preferences(customer_id, preferences)
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.get("/api/v1/customers/{customer_id}/onboarding-status")
        async def get_onboarding_status(customer_id: str):
            """Get customer onboarding status and progress."""
            result = self.onboarding_service.get_onboarding_status(customer_id)
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            return result
        
        @self.app.post("/api/v1/customers/{customer_id}/complete-onboarding")
        async def complete_onboarding_step(customer_id: str, step: str):
            """Complete an onboarding tutorial step."""
            result = self.onboarding_service.complete_tutorial_step(customer_id, step)
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.get("/api/v1/tutorial/{step}")
        async def get_tutorial_content(step: str):
            """Get tutorial content for a specific step."""
            result = self.onboarding_service.get_tutorial_content(step)
            return result
        
        @self.app.get("/api/v1/tiers/comparison")
        async def get_tier_comparison():
            """Get comparison of all tiers."""
            result = self.tier_display_service.get_tier_comparison()
            if not result['success']:
                raise HTTPException(status_code=500, detail=result['error'])
            return result
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "Customer & Account Management",
                "version": "1.0.0"
            }

# Create API instance
customer_api = CustomerAPI()
app = customer_api.app