"""REST API endpoints for Transaction & Rewards Engine unit."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from shared.event_store import EventStore
from ..repositories.transaction_repository import (
    TransactionRepository, PointBalanceRepository, 
    CustomerTierRepository, CategoryMultiplierRepository
)
from ..services.transaction_service import TransactionProcessingService
from ..services.point_calculation_service import PointCalculationService
from ..services.tier_management_service import TierManagementService
from ..services.category_management_service import CategoryManagementService

# Pydantic models for request/response
class TransactionRequest(BaseModel):
    customer_id: str
    amount: float
    merchant_name: str
    merchant_category_code: Optional[str] = "0000"
    card_number_last4: str

class PointCalculationRequest(BaseModel):
    customer_id: str
    amount: float
    category: str

class CategoryMultiplierRequest(BaseModel):
    multiplier: float
    admin_user: Optional[str] = "SYSTEM"

class PromotionalCampaignRequest(BaseModel):
    category: str
    multiplier: float
    start_date: str
    end_date: str
    created_by: Optional[str] = "SYSTEM"

class TransactionAPI:
    def __init__(self):
        self.app = FastAPI(title="Transaction & Rewards Engine API", version="1.0.0")
        
        # Initialize repositories and services
        self.event_store = EventStore()
        self.transaction_repo = TransactionRepository()
        self.point_repo = PointBalanceRepository()
        self.tier_repo = CustomerTierRepository()
        self.category_repo = CategoryMultiplierRepository()
        
        self.transaction_service = TransactionProcessingService(
            self.event_store, self.transaction_repo, self.point_repo, 
            self.tier_repo, self.category_repo
        )
        self.point_service = PointCalculationService(
            self.event_store, self.point_repo, self.category_repo, self.tier_repo
        )
        self.tier_service = TierManagementService(
            self.event_store, self.tier_repo, self.transaction_repo
        )
        self.category_service = CategoryManagementService(
            self.event_store, self.category_repo
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.post("/api/v1/transactions/process")
        async def process_transaction(request: TransactionRequest):
            """Process a customer transaction."""
            result = self.transaction_service.process_transaction(request.dict())
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.get("/api/v1/customers/{customer_id}/points/balance")
        async def get_point_balance(customer_id: str):
            """Get customer point balance."""
            result = self.point_service.get_point_balance(customer_id)
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            return result
        
        @self.app.get("/api/v1/customers/{customer_id}/transactions")
        async def get_transaction_history(customer_id: str, limit: int = 50):
            """Get customer transaction history."""
            result = self.transaction_service.get_transaction_history(customer_id, limit)
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            return result
        
        @self.app.get("/api/v1/customers/{customer_id}/tier-status")
        async def get_tier_status(customer_id: str):
            """Get customer tier status and progression."""
            result = self.tier_service.get_customer_tier_status(customer_id)
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            return result
        
        @self.app.post("/api/v1/customers/{customer_id}/tier-status")
        async def check_tier_advancement(customer_id: str):
            """Check and process tier advancement."""
            result = self.tier_service.check_tier_advancement(customer_id)
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.get("/api/v1/customers/{customer_id}/spending-insights")
        async def get_spending_insights(customer_id: str):
            """Get customer spending insights by category."""
            result = self.category_service.get_spending_insights(customer_id)
            if not result['success']:
                raise HTTPException(status_code=404, detail=result['error'])
            return result
        
        @self.app.post("/api/v1/transactions/validate-balance")
        async def validate_point_balance(customer_id: str, required_points: int):
            """Validate if customer has sufficient points."""
            result = self.point_service.validate_point_balance(customer_id, required_points)
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.post("/api/v1/points/calculate")
        async def calculate_points(request: PointCalculationRequest):
            """Calculate points for a transaction amount and category."""
            result = self.point_service.calculate_points(
                request.customer_id, request.amount, request.category
            )
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        # Admin endpoints
        @self.app.get("/api/v1/categories/multipliers")
        async def get_category_multipliers():
            """Get all category multipliers."""
            result = self.category_service.get_category_multipliers()
            if not result['success']:
                raise HTTPException(status_code=500, detail=result['error'])
            return result
        
        @self.app.put("/api/v1/categories/{category}/multiplier")
        async def update_category_multiplier(category: str, request: CategoryMultiplierRequest):
            """Update multiplier for a category."""
            result = self.category_service.update_category_multiplier(
                category, request.multiplier, request.admin_user
            )
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.post("/api/v1/campaigns")
        async def create_promotional_campaign(request: PromotionalCampaignRequest):
            """Create a promotional campaign."""
            result = self.category_service.create_promotional_campaign(request.dict())
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.post("/api/v1/customers/{customer_id}/points/deduct")
        async def deduct_points(customer_id: str, points: int, reason: str):
            """Deduct points from customer balance."""
            result = self.point_service.deduct_points(customer_id, points, reason)
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.post("/api/v1/customers/{customer_id}/points/add")
        async def add_points(customer_id: str, points: int, reason: str):
            """Add points to customer balance."""
            result = self.point_service.add_points(customer_id, points, reason)
            if not result['success']:
                raise HTTPException(status_code=400, detail=result['error'])
            return result
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "Transaction & Rewards Engine",
                "version": "1.0.0"
            }

# Create API instance
transaction_api = TransactionAPI()
app = transaction_api.app