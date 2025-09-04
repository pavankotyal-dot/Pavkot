"""Transaction repository for data persistence."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.repository import BaseRepository
from typing import Optional, List, Dict, Any
from ..models.transaction import Transaction, PointBalance, CustomerTier, CategoryMultiplier
from datetime import datetime, timedelta

class TransactionRepository(BaseRepository):
    def __init__(self, data_dir: str = "workdir/data"):
        super().__init__(f"{data_dir}/transactions.json")
    
    def save_transaction(self, transaction: Transaction) -> str:
        """Save a transaction to the repository."""
        return self.save(transaction.id, transaction.to_dict())
    
    def find_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Find a transaction by ID."""
        data = self.find_by_id(transaction_id)
        return Transaction.from_dict(data) if data else None
    
    def find_transactions_by_customer(self, customer_id: str) -> List[Transaction]:
        """Find all transactions for a customer."""
        transactions_data = self.find_by_field('customer_id', customer_id)
        return [Transaction.from_dict(data) for data in transactions_data]
    
    def get_customer_spending_by_period(self, customer_id: str, days: int = 365) -> float:
        """Get customer spending for a specific period."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        transactions = self.find_transactions_by_customer(customer_id)
        
        total_spending = 0.0
        for transaction in transactions:
            if transaction.transaction_date >= cutoff_date and transaction.status == 'COMPLETED':
                total_spending += transaction.amount
        
        return total_spending

class PointBalanceRepository(BaseRepository):
    def __init__(self, data_dir: str = "workdir/data"):
        super().__init__(f"{data_dir}/point_balances.json")
    
    def save_balance(self, balance: PointBalance) -> str:
        """Save point balance to the repository."""
        return self.save(balance.customer_id, balance.to_dict())
    
    def find_balance_by_customer(self, customer_id: str) -> Optional[PointBalance]:
        """Find point balance by customer ID."""
        data = self.find_by_id(customer_id)
        return PointBalance.from_dict(data) if data else None
    
    def initialize_balance(self, customer_id: str) -> PointBalance:
        """Initialize point balance for new customer."""
        balance = PointBalance(customer_id=customer_id)
        self.save_balance(balance)
        return balance

class CustomerTierRepository(BaseRepository):
    def __init__(self, data_dir: str = "workdir/data"):
        super().__init__(f"{data_dir}/customer_tiers.json")
    
    def save_tier(self, tier: CustomerTier) -> str:
        """Save customer tier to the repository."""
        return self.save(tier.customer_id, tier.to_dict())
    
    def find_tier_by_customer(self, customer_id: str) -> Optional[CustomerTier]:
        """Find customer tier by customer ID."""
        data = self.find_by_id(customer_id)
        return CustomerTier.from_dict(data) if data else None
    
    def initialize_tier(self, customer_id: str) -> CustomerTier:
        """Initialize tier for new customer."""
        tier = CustomerTier(customer_id=customer_id, current_tier='BRONZE')
        self.save_tier(tier)
        return tier

class CategoryMultiplierRepository(BaseRepository):
    def __init__(self, data_dir: str = "workdir/data"):
        super().__init__(f"{data_dir}/category_multipliers.json")
    
    def save_multiplier(self, multiplier: CategoryMultiplier) -> str:
        """Save category multiplier to the repository."""
        return self.save(multiplier.category, multiplier.to_dict())
    
    def find_multiplier_by_category(self, category: str) -> Optional[CategoryMultiplier]:
        """Find multiplier by category."""
        data = self.find_by_id(category)
        return CategoryMultiplier.from_dict(data) if data else None
    
    def get_active_multipliers(self) -> List[CategoryMultiplier]:
        """Get all active category multipliers."""
        all_data = self.find_all()
        multipliers = [CategoryMultiplier.from_dict(data) for data in all_data]
        return [m for m in multipliers if m.is_active()]
    
    def initialize_default_multipliers(self):
        """Initialize default category multipliers."""
        from shared.config import Config
        
        for category, multiplier in Config.DEFAULT_CATEGORY_MULTIPLIERS.items():
            existing = self.find_multiplier_by_category(category)
            if not existing:
                cat_multiplier = CategoryMultiplier(
                    category=category,
                    multiplier=multiplier
                )
                self.save_multiplier(cat_multiplier)