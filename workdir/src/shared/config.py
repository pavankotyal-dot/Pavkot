"""Configuration management for the loyalty program."""
import os
from typing import Dict, Any

class Config:
    # Business Rules
    POINTS_PER_INR = 1
    CASHBACK_RATE = 0.5  # 100 points = 50 INR
    
    # Tier Thresholds (Annual spending in INR)
    TIER_THRESHOLDS = {
        'BRONZE': 0,
        'SILVER': 50000,
        'GOLD': 200000,
        'PLATINUM': 500000
    }
    
    # Category Multipliers (configurable)
    DEFAULT_CATEGORY_MULTIPLIERS = {
        'DINING': 3.0,
        'TRAVEL': 2.5,
        'GROCERY': 2.0,
        'FUEL': 2.0,
        'ENTERTAINMENT': 1.5,
        'SHOPPING': 1.0,
        'OTHER': 1.0
    }
    
    # Data Storage
    DATA_DIR = os.getenv('DATA_DIR', 'workdir/data')
    
    # API Configuration
    API_HOST = os.getenv('API_HOST', '127.0.0.1')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    
    # External Service Mocks
    MOCK_PAYMENT_GATEWAY = True
    MOCK_EMAIL_SERVICE = True
    MOCK_SMS_SERVICE = True
    MOCK_SOCIAL_MEDIA = True
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '[%(asctime)s] [%(name)s] [%(levelname)s] [%(customer_id)s] [%(action)s] [%(result)s] %(message)s'
    
    @classmethod
    def get_tier_for_spending(cls, annual_spending: float) -> str:
        if annual_spending >= cls.TIER_THRESHOLDS['PLATINUM']:
            return 'PLATINUM'
        elif annual_spending >= cls.TIER_THRESHOLDS['GOLD']:
            return 'GOLD'
        elif annual_spending >= cls.TIER_THRESHOLDS['SILVER']:
            return 'SILVER'
        else:
            return 'BRONZE'
    
    @classmethod
    def get_tier_multiplier(cls, tier: str) -> float:
        multipliers = {
            'BRONZE': 1.0,
            'SILVER': 1.25,
            'GOLD': 1.5,
            'PLATINUM': 2.0
        }
        return multipliers.get(tier, 1.0)