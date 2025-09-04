from typing import Dict, List, Optional
from datetime import datetime
import json
import os

from ..models.redemption import (
    RedemptionItem, RedemptionRequest, CashbackRequest, TravelBooking,
    MerchandiseOrder, ExperienceBooking, RedemptionCatalog,
    RedemptionType, RedemptionStatus
)
from ...shared.repository import BaseRepository

class RedemptionRepository(BaseRepository):
    def __init__(self, data_dir: str = "data/redemption"):
        super().__init__(data_dir)
        self.catalogs: Dict[str, RedemptionCatalog] = {}
        self.redemption_requests: Dict[str, RedemptionRequest] = {}
        self.cashback_requests: Dict[str, CashbackRequest] = {}
        self.travel_bookings: Dict[str, TravelBooking] = {}
        self.merchandise_orders: Dict[str, MerchandiseOrder] = {}
        self.experience_bookings: Dict[str, ExperienceBooking] = {}
        self._load_data()

    def _load_data(self):
        """Load all redemption data from JSON files"""
        try:
            # Load catalogs
            catalog_file = os.path.join(self.data_dir, "catalogs.json")
            if os.path.exists(catalog_file):
                with open(catalog_file, 'r') as f:
                    data = json.load(f)
                    for catalog_data in data:
                        catalog = RedemptionCatalog(**catalog_data)
                        catalog.items = [RedemptionItem(**item) for item in catalog_data.get('items', [])]
                        self.catalogs[catalog.catalog_id] = catalog

            # Load redemption requests
            requests_file = os.path.join(self.data_dir, "redemption_requests.json")
            if os.path.exists(requests_file):
                with open(requests_file, 'r') as f:
                    data = json.load(f)
                    for req_data in data:
                        req = RedemptionRequest(**req_data)
                        self.redemption_requests[req.request_id] = req

            # Load cashback requests
            cashback_file = os.path.join(self.data_dir, "cashback_requests.json")
            if os.path.exists(cashback_file):
                with open(cashback_file, 'r') as f:
                    data = json.load(f)
                    for cb_data in data:
                        cb = CashbackRequest(**cb_data)
                        self.cashback_requests[cb.request_id] = cb

        except Exception as e:
            self.logger.error(f"Error loading redemption data: {e}")

    def save_data(self):
        """Save all redemption data to JSON files"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)

            # Save catalogs
            catalog_file = os.path.join(self.data_dir, "catalogs.json")
            with open(catalog_file, 'w') as f:
                catalog_data = []
                for catalog in self.catalogs.values():
                    data = {
                        'catalog_id': catalog.catalog_id,
                        'name': catalog.name,
                        'description': catalog.description,
                        'active': catalog.active,
                        'tier_specific': catalog.tier_specific,
                        'valid_from': catalog.valid_from.isoformat(),
                        'valid_until': catalog.valid_until.isoformat() if catalog.valid_until else None,
                        'created_at': catalog.created_at.isoformat(),
                        'updated_at': catalog.updated_at.isoformat(),
                        'items': [
                            {
                                'item_id': item.item_id,
                                'name': item.name,
                                'description': item.description,
                                'redemption_type': item.redemption_type.value,
                                'points_required': item.points_required,
                                'category': item.category,
                                'availability': item.availability,
                                'tier_requirement': item.tier_requirement,
                                'partner_id': item.partner_id,
                                'metadata': item.metadata,
                                'created_at': item.created_at.isoformat(),
                                'updated_at': item.updated_at.isoformat()
                            } for item in catalog.items
                        ]
                    }
                    catalog_data.append(data)
                json.dump(catalog_data, f, indent=2)

            # Save redemption requests
            requests_file = os.path.join(self.data_dir, "redemption_requests.json")
            with open(requests_file, 'w') as f:
                requests_data = []
                for req in self.redemption_requests.values():
                    data = {
                        'request_id': req.request_id,
                        'customer_id': req.customer_id,
                        'item_id': req.item_id,
                        'points_used': req.points_used,
                        'redemption_type': req.redemption_type.value,
                        'status': req.status.value,
                        'fulfillment_status': req.fulfillment_status.value,
                        'request_details': req.request_details,
                        'fulfillment_details': req.fulfillment_details,
                        'partner_reference': req.partner_reference,
                        'estimated_fulfillment': req.estimated_fulfillment.isoformat() if req.estimated_fulfillment else None,
                        'actual_fulfillment': req.actual_fulfillment.isoformat() if req.actual_fulfillment else None,
                        'created_at': req.created_at.isoformat(),
                        'updated_at': req.updated_at.isoformat()
                    }
                    requests_data.append(data)
                json.dump(requests_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving redemption data: {e}")

    # Catalog operations
    def create_catalog(self, catalog: RedemptionCatalog) -> RedemptionCatalog:
        self.catalogs[catalog.catalog_id] = catalog
        self.save_data()
        return catalog

    def get_catalog(self, catalog_id: str) -> Optional[RedemptionCatalog]:
        return self.catalogs.get(catalog_id)

    def get_active_catalogs(self) -> List[RedemptionCatalog]:
        return [catalog for catalog in self.catalogs.values() if catalog.active]

    def update_catalog(self, catalog: RedemptionCatalog) -> RedemptionCatalog:
        catalog.updated_at = datetime.now()
        self.catalogs[catalog.catalog_id] = catalog
        self.save_data()
        return catalog

    # Redemption request operations
    def create_redemption_request(self, request: RedemptionRequest) -> RedemptionRequest:
        self.redemption_requests[request.request_id] = request
        self.save_data()
        return request

    def get_redemption_request(self, request_id: str) -> Optional[RedemptionRequest]:
        return self.redemption_requests.get(request_id)

    def get_customer_redemptions(self, customer_id: str) -> List[RedemptionRequest]:
        return [req for req in self.redemption_requests.values() if req.customer_id == customer_id]

    def update_redemption_request(self, request: RedemptionRequest) -> RedemptionRequest:
        request.updated_at = datetime.now()
        self.redemption_requests[request.request_id] = request
        self.save_data()
        return request

    def get_redemptions_by_status(self, status: RedemptionStatus) -> List[RedemptionRequest]:
        return [req for req in self.redemption_requests.values() if req.status == status]

    # Cashback operations
    def create_cashback_request(self, request: CashbackRequest) -> CashbackRequest:
        self.cashback_requests[request.request_id] = request
        self.save_data()
        return request

    def get_cashback_request(self, request_id: str) -> Optional[CashbackRequest]:
        return self.cashback_requests.get(request_id)

    def get_customer_cashbacks(self, customer_id: str) -> List[CashbackRequest]:
        return [req for req in self.cashback_requests.values() if req.customer_id == customer_id]

    def update_cashback_request(self, request: CashbackRequest) -> CashbackRequest:
        self.cashback_requests[request.request_id] = request
        self.save_data()
        return request