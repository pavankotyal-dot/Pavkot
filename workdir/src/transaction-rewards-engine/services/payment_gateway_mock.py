"""Mock payment gateway for transaction simulation."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.logging import BusinessLogger
from typing import Dict, Any, Optional
import random
import time
import uuid
from datetime import datetime

class PaymentGatewayMock:
    def __init__(self):
        self.logger = BusinessLogger("PaymentGateway-Mock")
        self.success_rate = 0.95  # 95% success rate
        self.processing_delay = (0.5, 2.0)  # Random delay between 0.5-2.0 seconds
        
        # Mock merchant database
        self.merchants = {
            'GROCERY_STORE_1': {'name': 'Fresh Mart', 'mcc': '5411', 'category': 'GROCERY'},
            'RESTAURANT_1': {'name': 'Spice Garden', 'mcc': '5812', 'category': 'DINING'},
            'GAS_STATION_1': {'name': 'Fuel Plus', 'mcc': '5541', 'category': 'FUEL'},
            'AIRLINE_1': {'name': 'Sky Airways', 'mcc': '3000', 'category': 'TRAVEL'},
            'HOTEL_1': {'name': 'Grand Plaza', 'mcc': '7011', 'category': 'TRAVEL'},
            'MALL_1': {'name': 'City Mall', 'mcc': '5999', 'category': 'SHOPPING'},
            'CINEMA_1': {'name': 'Star Cinema', 'mcc': '7832', 'category': 'ENTERTAINMENT'},
        }
    
    def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment transaction."""
        try:
            # Simulate processing delay
            delay = random.uniform(*self.processing_delay)
            time.sleep(delay)
            
            # Validate payment data
            required_fields = ['card_number', 'amount', 'merchant_id']
            for field in required_fields:
                if field not in payment_data:
                    return self._create_error_response(f"Missing required field: {field}")
            
            # Simulate random failures
            if random.random() > self.success_rate:
                return self._create_error_response("Payment declined by issuing bank")
            
            # Get merchant info
            merchant_info = self.merchants.get(payment_data['merchant_id'], {
                'name': 'Unknown Merchant',
                'mcc': '0000',
                'category': 'OTHER'
            })
            
            # Create successful transaction
            transaction_id = str(uuid.uuid4())
            
            response = {
                'success': True,
                'transaction_id': transaction_id,
                'amount': float(payment_data['amount']),
                'currency': 'INR',
                'merchant_name': merchant_info['name'],
                'merchant_category_code': merchant_info['mcc'],
                'card_number_last4': payment_data['card_number'][-4:],
                'processing_time': delay,
                'timestamp': datetime.now().isoformat(),
                'status': 'APPROVED'
            }
            
            self.logger.log_business_event('INFO', payment_data.get('customer_id'), 
                                         'PAYMENT_PROCESSED', 'SUCCESS',
                                         f'Payment gateway processed transaction in {delay:.1f} seconds')
            
            return response
            
        except Exception as e:
            self.logger.log_error(payment_data.get('customer_id'), 'PAYMENT_PROCESSING', str(e))
            return self._create_error_response(f"Payment processing error: {str(e)}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            'success': False,
            'error': error_message,
            'error_code': 'PAYMENT_FAILED',
            'timestamp': datetime.now().isoformat()
        }
    
    def simulate_transaction(self, customer_id: str, amount: float, 
                           merchant_id: Optional[str] = None) -> Dict[str, Any]:
        """Simulate a transaction for testing purposes."""
        if not merchant_id:
            merchant_id = random.choice(list(self.merchants.keys()))
        
        # Generate mock card number
        card_number = f"4532{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
        
        payment_data = {
            'customer_id': customer_id,
            'card_number': card_number,
            'amount': amount,
            'merchant_id': merchant_id
        }
        
        return self.process_payment(payment_data)
    
    def get_merchant_info(self, merchant_id: str) -> Dict[str, Any]:
        """Get merchant information."""
        return self.merchants.get(merchant_id, {
            'name': 'Unknown Merchant',
            'mcc': '0000',
            'category': 'OTHER'
        })
    
    def get_all_merchants(self) -> Dict[str, Dict[str, Any]]:
        """Get all available merchants for testing."""
        return self.merchants.copy()

class TransactionSimulator:
    def __init__(self, payment_gateway: PaymentGatewayMock):
        self.payment_gateway = payment_gateway
        self.logger = BusinessLogger("TransactionSimulator")
    
    def simulate_customer_spending(self, customer_id: str, num_transactions: int = 10) -> List[Dict[str, Any]]:
        """Simulate multiple transactions for a customer."""
        transactions = []
        
        # Define realistic spending patterns
        spending_patterns = [
            {'merchant_id': 'GROCERY_STORE_1', 'amount_range': (500, 3000), 'frequency': 0.3},
            {'merchant_id': 'RESTAURANT_1', 'amount_range': (200, 1500), 'frequency': 0.25},
            {'merchant_id': 'GAS_STATION_1', 'amount_range': (1000, 4000), 'frequency': 0.15},
            {'merchant_id': 'MALL_1', 'amount_range': (1000, 8000), 'frequency': 0.15},
            {'merchant_id': 'CINEMA_1', 'amount_range': (300, 800), 'frequency': 0.1},
            {'merchant_id': 'AIRLINE_1', 'amount_range': (5000, 25000), 'frequency': 0.03},
            {'merchant_id': 'HOTEL_1', 'amount_range': (3000, 15000), 'frequency': 0.02},
        ]
        
        for _ in range(num_transactions):
            # Select merchant based on frequency
            rand = random.random()
            cumulative_freq = 0
            selected_pattern = spending_patterns[-1]  # Default to last pattern
            
            for pattern in spending_patterns:
                cumulative_freq += pattern['frequency']
                if rand <= cumulative_freq:
                    selected_pattern = pattern
                    break
            
            # Generate random amount within range
            amount = random.uniform(*selected_pattern['amount_range'])
            amount = round(amount, 2)
            
            # Process transaction
            result = self.payment_gateway.simulate_transaction(
                customer_id, amount, selected_pattern['merchant_id']
            )
            
            if result['success']:
                transactions.append(result)
                self.logger.log_business_event('INFO', customer_id, 'TRANSACTION_SIMULATED', 'SUCCESS',
                                             f'Simulated ₹{amount} transaction at {result["merchant_name"]}')
            
            # Small delay between transactions
            time.sleep(0.1)
        
        return transactions