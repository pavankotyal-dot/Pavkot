#!/usr/bin/env python3
"""
Demo Script for PremiumCard Loyalty & Rewards Program
Demonstrates all 5 business units with realistic scenarios
"""

import requests
import json
import time
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print('='*60)

def print_step(step, description):
    print(f"\n📋 Step {step}: {description}")

def make_request(method, endpoint, data=None):
    """Make HTTP request and return response"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def demo_customer_management():
    """Demo Customer & Account Management Unit"""
    print_section("CUSTOMER & ACCOUNT MANAGEMENT UNIT")
    
    # Step 1: Register customers
    print_step(1, "Registering customers")
    customers = [
        {
            "full_name": "Alexandra Premium",
            "email": "alexandra@example.com",
            "phone": "+91-9876543210",
            "date_of_birth": "1985-06-15",
            "address": {
                "street": "123 Premium Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "postal_code": "400001",
                "country": "India"
            }
        },
        {
            "full_name": "Marcus Traveler",
            "email": "marcus@example.com", 
            "phone": "+91-9876543211",
            "date_of_birth": "1990-03-22",
            "address": {
                "street": "456 Travel Avenue",
                "city": "Delhi",
                "state": "Delhi",
                "postal_code": "110001",
                "country": "India"
            }
        }
    ]
    
    customer_ids = []
    for customer_data in customers:
        result = make_request("POST", "/api/customer/register", customer_data)
        if result and result.get("success"):
            customer_id = result["customer_id"]
            customer_ids.append(customer_id)
            print(f"✅ Registered customer: {customer_data['full_name']} (ID: {customer_id})")
        else:
            print(f"❌ Failed to register customer: {customer_data['full_name']}")
    
    # Step 2: Complete onboarding
    print_step(2, "Completing customer onboarding")
    for customer_id in customer_ids:
        onboarding_data = {
            "preferences": {
                "communication_channel": "email",
                "categories_of_interest": ["dining", "travel", "shopping"],
                "notification_frequency": "weekly"
            },
            "documents": {
                "pan_card": "ABCDE1234F",
                "bank_account": "1234567890"
            }
        }
        result = make_request("POST", f"/api/customer/{customer_id}/onboarding", onboarding_data)
        if result and result.get("success"):
            print(f"✅ Onboarding completed for customer {customer_id}")
    
    return customer_ids

def demo_transaction_processing(customer_ids):
    """Demo Transaction & Rewards Engine Unit"""
    print_section("TRANSACTION & REWARDS ENGINE UNIT")
    
    # Step 1: Process transactions
    print_step(1, "Processing customer transactions")
    
    transactions = [
        {"customer_id": customer_ids[0], "amount": 5000, "merchant": "Premium Restaurant", "category": "dining"},
        {"customer_id": customer_ids[0], "amount": 15000, "merchant": "Luxury Store", "category": "shopping"},
        {"customer_id": customer_ids[1], "amount": 25000, "merchant": "Travel Agency", "category": "travel"},
        {"customer_id": customer_ids[1], "amount": 3000, "merchant": "Fuel Station", "category": "fuel"},
        {"customer_id": customer_ids[0], "amount": 8000, "merchant": "Electronics Store", "category": "electronics"}
    ]
    
    for transaction in transactions:
        result = make_request("POST", "/api/transaction/process", transaction)
        if result and result.get("success"):
            print(f"✅ Transaction processed: ₹{transaction['amount']} at {transaction['merchant']} - Points: {result.get('points_earned', 0)}")
    
    # Step 2: Check customer points and tier status
    print_step(2, "Checking customer points and tier status")
    for customer_id in customer_ids:
        # Get points balance
        result = make_request("GET", f"/api/transaction/points/{customer_id}")
        if result and result.get("success"):
            print(f"✅ Customer {customer_id} - Points: {result['current_balance']}, Tier: {result.get('current_tier', 'bronze')}")

def demo_redemption_fulfillment(customer_ids):
    """Demo Redemption & Fulfillment Unit"""
    print_section("REDEMPTION & FULFILLMENT UNIT")
    
    # Step 1: Get redemption catalog
    print_step(1, "Viewing redemption catalog")
    result = make_request("GET", "/api/redemption/catalog")
    if result and result.get("success"):
        print(f"✅ Catalog loaded with {len(result['catalogs'][0]['items'])} items")
        for item in result['catalogs'][0]['items'][:3]:
            print(f"   - {item['name']}: {item['points_required']} points")
    
    # Step 2: Process cashback redemption
    print_step(2, "Processing cashback redemption")
    cashback_request = {
        "customer_id": customer_ids[0],
        "points_to_redeem": 1000,
        "bank_account": "1234567890"
    }
    result = make_request("POST", "/api/redemption/cashback/process", cashback_request)
    if result and result.get("success"):
        print(f"✅ Cashback processed: ₹{result['net_amount']} (after ₹{result['processing_fee']} fee)")
    
    # Step 3: Book travel
    print_step(3, "Booking travel through partner")
    travel_request = {
        "customer_id": customer_ids[1],
        "points_used": 5000,
        "booking_type": "flight",
        "travel_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "destination": "Goa",
        "estimated_cost": 8000,
        "booking_details": {
            "departure": "Delhi",
            "passengers": 2
        }
    }
    result = make_request("POST", "/api/redemption/travel/book", travel_request)
    if result and result.get("success"):
        print(f"✅ Travel booked with {result['partner']}: {result['booking_reference']}")

def demo_analytics_engagement(customer_ids):
    """Demo Analytics & Engagement Unit"""
    print_section("ANALYTICS & ENGAGEMENT UNIT")
    
    # Step 1: Analyze customer behavior
    print_step(1, "Analyzing customer behavior")
    for customer_id in customer_ids:
        result = make_request("GET", f"/api/analytics/customer/{customer_id}/behavior")
        if result and result.get("success"):
            analytics = result["analytics"]
            print(f"✅ Customer {customer_id} Analysis:")
            print(f"   - Total Spending: ₹{analytics['total_spending']}")
            print(f"   - Engagement Score: {analytics['engagement_score']}")
            print(f"   - Churn Risk: {analytics['churn_risk']}")
    
    # Step 2: Generate recommendations
    print_step(2, "Generating personalized recommendations")
    for customer_id in customer_ids:
        result = make_request("GET", f"/api/analytics/customer/{customer_id}/recommendations")
        if result and result.get("success"):
            recommendations = result["recommendations"]
            print(f"✅ Generated {len(recommendations)} recommendations for customer {customer_id}")
            for rec in recommendations[:2]:
                print(f"   - {rec['title']}: {rec['description']}")
    
    # Step 3: Initialize gamification
    print_step(3, "Setting up gamification")
    for customer_id in customer_ids:
        result = make_request("POST", f"/api/analytics/customer/{customer_id}/gamification/initialize")
        if result and result.get("success"):
            print(f"✅ Gamification initialized for customer {customer_id} with {result['initialized_elements']} elements")
    
    # Step 4: Record social activity
    print_step(4, "Recording social engagement")
    social_activity = {
        "customer_id": customer_ids[0],
        "activity_type": "share",
        "content": "Just earned amazing rewards with PremiumCard!",
        "platform": "twitter"
    }
    result = make_request("POST", "/api/analytics/social/activity", social_activity)
    if result and result.get("success"):
        print(f"✅ Social activity recorded: {result['engagement_points']} points earned")

def demo_administration_operations():
    """Demo Administration & Operations Unit"""
    print_section("ADMINISTRATION & OPERATIONS UNIT")
    
    # Step 1: Create admin user
    print_step(1, "Creating admin user")
    admin_request = {
        "username": "admin_demo",
        "email": "admin@premiumcard.com",
        "full_name": "Demo Administrator",
        "role": "program_manager",
        "created_by": "system"
    }
    result = make_request("POST", "/api/admin/users", admin_request)
    if result and result.get("success"):
        admin_id = result["user_id"]
        print(f"✅ Admin user created: {admin_request['username']} (ID: {admin_id})")
    
    # Step 2: Update program configuration
    print_step(2, "Updating program configuration")
    config_request = {
        "config_type": "point_rates",
        "config_data": {
            "base_rate": 1.0,
            "bonus_categories": {
                "dining": 2.5,
                "travel": 3.0,
                "fuel": 1.5
            }
        },
        "updated_by": "admin_demo"
    }
    result = make_request("POST", "/api/admin/configuration", config_request)
    if result and result.get("success"):
        print(f"✅ Configuration updated: {result['config_type']}")
    
    # Step 3: Generate business report
    print_step(3, "Generating business intelligence report")
    report_request = {
        "report_type": "customer_summary",
        "parameters": {"period": "monthly"},
        "generated_by": "admin_demo"
    }
    result = make_request("POST", "/api/admin/reports/generate", report_request)
    if result and result.get("success"):
        print(f"✅ Business report generated: {result['report_type']}")
        print(f"   - Total Customers: {result['data']['total_customers']}")
        print(f"   - Active Customers: {result['data']['active_customers']}")
    
    # Step 4: Check system health
    print_step(4, "Checking system health")
    result = make_request("GET", "/api/admin/system/health")
    if result and result.get("success"):
        print(f"✅ System Health Score: {result['health_score']}/100 ({result['status']})")
        print(f"   - Active Admin Users: {result['metrics']['active_admin_users']}")
        print(f"   - System Uptime: {result['metrics']['system_uptime_hours']} hours")

def main():
    """Run complete demo scenario"""
    print("🏆 PremiumCard Loyalty & Rewards Program - Complete Demo")
    print("🚀 Starting comprehensive demonstration of all 5 business units")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server is not running. Please start the application first:")
            print("   python src/main.py")
            return
    except:
        print("❌ Cannot connect to server. Please start the application first:")
        print("   python src/main.py")
        return
    
    print("✅ Server is running. Starting demo...")
    
    # Run all demo units
    customer_ids = demo_customer_management()
    if customer_ids:
        time.sleep(1)  # Brief pause between units
        demo_transaction_processing(customer_ids)
        time.sleep(1)
        demo_redemption_fulfillment(customer_ids)
        time.sleep(1)
        demo_analytics_engagement(customer_ids)
        time.sleep(1)
        demo_administration_operations()
    
    print_section("DEMO COMPLETED SUCCESSFULLY")
    print("🎉 All 5 business units demonstrated successfully!")
    print("📊 Visit http://localhost:8000 for the dashboard")
    print("📚 Visit http://localhost:8000/docs for API documentation")
    print("🔧 Visit http://localhost:8000/health for system status")

if __name__ == "__main__":
    main()