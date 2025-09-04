"""Business-friendly logging for the loyalty program."""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any

class BusinessLogger:
    def __init__(self, unit_name: str):
        self.unit_name = unit_name
        self.logger = logging.getLogger(unit_name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_business_event(self, level: str, customer_id: Optional[str], 
                          action: str, result: str, details: str):
        """Log business events in a non-developer friendly format."""
        message = f"[{customer_id or 'SYSTEM'}] [{action}] [{result}] {details}"
        
        if level.upper() == 'INFO':
            self.logger.info(message)
        elif level.upper() == 'WARNING':
            self.logger.warning(message)
        elif level.upper() == 'ERROR':
            self.logger.error(message)
        else:
            self.logger.info(message)
    
    def log_customer_registration(self, customer_id: str, customer_name: str, tier: str):
        self.log_business_event('INFO', customer_id, 'REGISTRATION', 'SUCCESS', 
                               f'New customer {customer_name} registered successfully, assigned {tier} tier')
    
    def log_transaction_processed(self, customer_id: str, amount: float, 
                                 category: str, points_earned: int, multiplier: float):
        self.log_business_event('INFO', customer_id, 'TRANSACTION', 'SUCCESS',
                               f'Customer earned {points_earned} points from ₹{amount} {category} purchase ({multiplier}x multiplier)')
    
    def log_tier_advancement(self, customer_id: str, old_tier: str, new_tier: str, spending: float):
        self.log_business_event('INFO', customer_id, 'TIER_ADVANCEMENT', 'SUCCESS',
                               f'Customer advanced from {old_tier} to {new_tier} tier after ₹{spending} spending')
    
    def log_redemption(self, customer_id: str, redemption_type: str, 
                      points_used: int, value: str):
        self.log_business_event('INFO', customer_id, 'REDEMPTION', 'SUCCESS',
                               f'Customer redeemed {points_used} points for {value} {redemption_type}')
    
    def log_error(self, customer_id: Optional[str], action: str, error_details: str):
        self.log_business_event('ERROR', customer_id, action, 'FAILED', error_details)