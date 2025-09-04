from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os

# Import all API routers
from customer_account_management.api.customer_api import router as customer_router
from transaction_rewards_engine.api.transaction_api import router as transaction_router
from redemption_fulfillment.api.redemption_api import router as redemption_router
from analytics_engagement.api.analytics_api import router as analytics_router
from administration_operations.api.admin_api import router as admin_router

# Initialize FastAPI app
app = FastAPI(
    title="PremiumCard Loyalty & Rewards Program",
    description="Comprehensive loyalty and rewards management system",
    version="1.0.0"
)

# Include all API routers
app.include_router(customer_router)
app.include_router(transaction_router)
app.include_router(redemption_router)
app.include_router(analytics_router)
app.include_router(admin_router)

# Mount static files for demo UI
static_dir = os.path.join(os.path.dirname(__file__), "demo", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main dashboard page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PremiumCard Loyalty & Rewards Program</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 40px; }
            .header h1 { color: #2c3e50; margin-bottom: 10px; }
            .header p { color: #7f8c8d; font-size: 18px; }
            .units { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px; }
            .unit { background: #ecf0f1; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }
            .unit h3 { color: #2c3e50; margin-bottom: 10px; }
            .unit p { color: #7f8c8d; margin-bottom: 15px; }
            .unit a { display: inline-block; background: #3498db; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; }
            .unit a:hover { background: #2980b9; }
            .api-docs { text-align: center; margin-top: 30px; }
            .api-docs a { background: #27ae60; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; }
            .api-docs a:hover { background: #229954; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
            .stat { background: #3498db; color: white; padding: 20px; border-radius: 8px; text-align: center; }
            .stat h4 { margin: 0 0 10px 0; font-size: 24px; }
            .stat p { margin: 0; opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏆 PremiumCard Loyalty & Rewards Program</h1>
                <p>Comprehensive loyalty management system with 5 integrated business units</p>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <h4>5</h4>
                    <p>Business Units</p>
                </div>
                <div class="stat">
                    <h4>34</h4>
                    <p>User Stories</p>
                </div>
                <div class="stat">
                    <h4>50+</h4>
                    <p>API Endpoints</p>
                </div>
                <div class="stat">
                    <h4>100%</h4>
                    <p>Implementation</p>
                </div>
            </div>
            
            <div class="units">
                <div class="unit">
                    <h3>👤 Customer & Account Management</h3>
                    <p>Customer registration, onboarding, profile management, and tier status tracking</p>
                    <a href="/docs#/Customer%20%26%20Account%20Management">View APIs</a>
                </div>
                
                <div class="unit">
                    <h3>💳 Transaction & Rewards Engine</h3>
                    <p>Transaction processing, point calculation, tier management, and category multipliers</p>
                    <a href="/docs#/Transaction%20%26%20Rewards%20Engine">View APIs</a>
                </div>
                
                <div class="unit">
                    <h3>🎁 Redemption & Fulfillment</h3>
                    <p>Cashback processing, travel bookings, merchandise orders, and partner integrations</p>
                    <a href="/docs#/Redemption%20%26%20Fulfillment">View APIs</a>
                </div>
                
                <div class="unit">
                    <h3>📊 Analytics & Engagement</h3>
                    <p>Customer analytics, personalized recommendations, gamification, and social engagement</p>
                    <a href="/docs#/Analytics%20%26%20Engagement">View APIs</a>
                </div>
                
                <div class="unit">
                    <h3>⚙️ Administration & Operations</h3>
                    <p>Admin management, program configuration, support tickets, and business intelligence</p>
                    <a href="/docs#/Administration%20%26%20Operations">View APIs</a>
                </div>
            </div>
            
            <div class="api-docs">
                <a href="/docs">🚀 Explore Interactive API Documentation</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "PremiumCard Loyalty & Rewards Program is running",
        "units": [
            "Customer & Account Management",
            "Transaction & Rewards Engine", 
            "Redemption & Fulfillment",
            "Analytics & Engagement",
            "Administration & Operations"
        ]
    }

if __name__ == "__main__":
    # Create data directories
    os.makedirs("data/customers", exist_ok=True)
    os.makedirs("data/transactions", exist_ok=True)
    os.makedirs("data/redemption", exist_ok=True)
    os.makedirs("data/admin", exist_ok=True)
    os.makedirs("data/events", exist_ok=True)
    
    print("🏆 Starting PremiumCard Loyalty & Rewards Program")
    print("📊 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/health")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)