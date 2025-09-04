"""Transaction processing service."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.base_service import BaseService
from shared.event_store import EventStore
from shared.config import Config
from ..repositories.transaction_repository import TransactionRepository, PointBalanceRepository, CustomerTierRepository, CategoryMultiplierRepository
from ..models.transaction import Transaction
from typing import Dict, Any
import uuid

class TransactionProcessingService(BaseService):
    def __init__(self, event_store: EventStore, transaction_repo: TransactionRepository,
                 point_repo: PointBalanceRepository, tier_repo: CustomerTierRepository,
                 category_repo: CategoryMultiplierRepository):
        super().__init__("TRANSACTION-ENGINE", event_store)
        self.transaction_repo = transaction_repo
        self.point_repo = point_repo
        self.tier_repo = tier_repo
        self.category_repo = category_repo
    
    def process_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a customer transaction and calculate points."""
        try:
            # Validate required fields
            required_fields = ['customer_id', 'amount', 'merchant_name', 'card_number_last4']
            self.validate_required_fields(transaction_data, required_fields)
            
            # Create transaction
            transaction = Transaction(
                id=str(uuid.uuid4()),
                customer_id=transaction_data['customer_id'],
                amount=float(transaction_data['amount']),
                category=self._classify_category(transaction_data.get('merchant_category_code', '0000')),
                merchant_name=transaction_data['merchant_name'],
                merchant_category_code=transaction_data.get('merchant_category_code', '0000'),
                card_number_last4=transaction_data['card_number_last4'],
                status='PROCESSING'
            )
            
            # Get multipliers
            category_multiplier = self._get_category_multiplier(transaction.category)
            tier_multiplier = self._get_tier_multiplier(transaction.customer_id)
            
            # Calculate points
            points_earned = transaction.calculate_points(category_multiplier, tier_multiplier)
            
            # Save transaction
            transaction.status = 'COMPLETED'
            self.transaction_repo.save_transaction(transaction)
            
            # Update point balance
            self._update_point_balance(transaction.customer_id, points_earned)
            
            # Update customer spending and check tier advancement
            self._update_customer_spending(transaction.customer_id, transaction.amount)
            
            # Publish events
            self.publish_event('TransactionProcessed', transaction.customer_id, {
                'transaction_id': transaction.id,
                'customer_id': transaction.customer_id,
                'amount': transaction.amount,
                'category': transaction.category,
                'merchant_name': transaction.merchant_name,
                'points_earned': points_earned,
                'category_multiplier': category_multiplier,
                'tier_multiplier': tier_multiplier,
                'transaction_date': transaction.transaction_date
            })
            
            self.publish_event('PointsEarned', transaction.customer_id, {
                'customer_id': transaction.customer_id,
                'transaction_id': transaction.id,
                'points_amount': points_earned,
                'category': transaction.category,
                'multiplier': transaction.total_multiplier
            })
            
            # Log business event
            self.logger.log_transaction_processed(
                transaction.customer_id, transaction.amount, 
                transaction.category, points_earned, transaction.total_multiplier
            )
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'points_earned': points_earned,
                'category': transaction.category,
                'multiplier_applied': transaction.total_multiplier,
                'message': f'Transaction processed successfully. Earned {points_earned} points.'
            }
            
        except ValueError as e:
            self.logger.log_error(transaction_data.get('customer_id'), 'TRANSACTION_PROCESSING', str(e))
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            self.logger.log_error(transaction_data.get('customer_id'), 'TRANSACTION_PROCESSING', 
                                f'Unexpected error: {str(e)}')
            return {
                'success': False,
                'error': 'Transaction processing failed due to system error'
            }
    
    def _classify_category(self, mcc: str) -> str:
        """Classify merchant category code to spending category."""
        mcc_mapping = {
            '5411': 'GROCERY',  # Grocery Stores
            '5812': 'DINING',   # Eating Places
            '5541': 'FUEL',     # Service Stations
            '3000': 'TRAVEL',   # Airlines
            '3001': 'TRAVEL',   # Airlines
            '7011': 'TRAVEL',   # Hotels
            '5999': 'SHOPPING', # Miscellaneous Retail
            '7832': 'ENTERTAINMENT',  # Motion Picture Theaters
            '7991': 'ENTERTAINMENT',  # Tourist Attractions
        }
        
        return mcc_mapping.get(mcc, 'OTHER')
    
    def _get_category_multiplier(self, category: str) -> float:
        """Get multiplier for spending category."""
        multiplier_obj = self.category_repo.find_multiplier_by_category(category)
        if multiplier_obj and multiplier_obj.is_active():
            return multiplier_obj.multiplier
        
        # Fallback to config default
        return Config.DEFAULT_CATEGORY_MULTIPLIERS.get(category, 1.0)
    
    def _get_tier_multiplier(self, customer_id: str) -> float:
        """Get tier-based multiplier for customer."""
        tier_obj = self.tier_repo.find_tier_by_customer(customer_id)
        if tier_obj:
            return Config.get_tier_multiplier(tier_obj.current_tier)
        
        return Config.get_tier_multiplier('BRONZE')
    
    def _update_point_balance(self, customer_id: str, points: int):
        """Update customer point balance."""
        balance = self.point_repo.find_balance_by_customer(customer_id)
        if not balance:
            balance = self.point_repo.initialize_balance(customer_id)
        
        balance.add_points(points)
        self.point_repo.save_balance(balance)
    
    def _update_customer_spending(self, customer_id: str, amount: float):
        """Update customer spending and check for tier advancement."""
        tier_obj = self.tier_repo.find_tier_by_customer(customer_id)
        if not tier_obj:
            tier_obj = self.tier_repo.initialize_tier(customer_id)
        
        tier_obj.add_spending(amount)
        
        # Check for tier advancement
        new_tier = Config.get_tier_for_spending(tier_obj.annual_spending)
        if new_tier != tier_obj.current_tier:
            old_tier = tier_obj.current_tier
            tier_obj.update_tier(new_tier)
            
            # Publish tier advancement event
            self.publish_event('TierAdvanced', customer_id, {
                'customer_id': customer_id,
                'previous_tier': old_tier,
                'new_tier': new_tier,
                'total_spending': tier_obj.annual_spending,
                'advancement_date': tier_obj.tier_start_date
            })
            
            self.logger.log_tier_advancement(customer_id, old_tier, new_tier, tier_obj.annual_spending)
        
        self.tier_repo.save_tier(tier_obj)
    
    def get_transaction_history(self, customer_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get customer transaction history."""
        try:
            transactions = self.transaction_repo.find_transactions_by_customer(customer_id)
            
            # Sort by date (newest first) and limit
            transactions.sort(key=lambda t: t.transaction_date, reverse=True)
            transactions = transactions[:limit]
            
            return {
                'success': True,
                'transactions': [t.to_dict() for t in transactions],
                'total_count': len(transactions)
            }
            
        except Exception as e:
            self.logger.log_error(customer_id, 'GET_TRANSACTION_HISTORY', str(e))
            return {
                'success': False,
                'error': 'Failed to retrieve transaction history'
            }