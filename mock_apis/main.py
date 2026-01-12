"""
Mock API Server

Simulates:
1. Warehouse stock API (serves CSV data)
2. Logistics shipment tracking API
3. FX rate API (USD to ZAR)

Run with: uvicorn mock_apis.main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

app = FastAPI(
    title="Aura Mock APIs",
    description="Mock data sources for knowledge engineering demo",
    version="1.0.0"
)


# ==============================================================================
# ENDPOINT 1: Logistics Shipments
# ==============================================================================

@app.get("/api/shipments/active")
def get_active_shipments(
    scenario: Optional[str] = Query(None, description="Test scenario: normal, shadow_stock, low_reliability, stale")
) -> Dict[str, Any]:
    """
    Returns currently active shipments (in-transit or recently delivered).
    
    Scenarios supported:
    - normal: Standard shipments with good data
    - shadow_stock: Delivered shipment not yet in warehouse (P003)
    - low_reliability: Includes shipments with data quality issues
    - stale: All timestamps are old (>24 hours)
    """
    
    now = datetime.now()
    
    # Base shipments - always present
    shipments = [
        # Scenario: Normal in-transit shipment for P001
        {
            "shipment_id": "SHP-2024-001",
            "supplier": "Caterpillar Mining SA",
            "parts": [
                {
                    "part_id": "P001",
                    "quantity_shipped": 20,
                    "unit_cost_usd": 675.00  # ~R12,500 at 18.5 rate
                }
            ],
            "estimated_arrival": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
            "status": "in_transit",
            "last_updated": (now - timedelta(hours=2)).isoformat() + "Z"
        },
        # Scenario: Normal in-transit for P002
        {
            "shipment_id": "SHP-2024-002",
            "supplier": "Komatsu Parts Ltd",
            "parts": [
                {
                    "part_id": "P002",
                    "quantity_shipped": 15,
                    "unit_cost_usd": 481.08  # ~R8,900 at 18.5 rate
                }
            ],
            "estimated_arrival": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            "status": "in_transit",
            "last_updated": (now - timedelta(hours=4)).isoformat() + "Z"
        },
        # Scenario: SHADOW STOCK - Delivered but not scanned into warehouse
        # P003 shows as delivered 8 hours ago, but warehouse CSV still shows old count
        {
            "shipment_id": "SHP-2024-003",
            "supplier": "SafetyFirst Industrial",
            "parts": [
                {
                    "part_id": "P003",
                    "quantity_shipped": 50,
                    "unit_cost_usd": 172.97  # ~R3,200 at 18.5 rate
                }
            ],
            "estimated_arrival": now.strftime("%Y-%m-%d"),
            "status": "delivered",  # CRITICAL: Creates shadow stock scenario!
            "last_updated": (now - timedelta(hours=8)).isoformat() + "Z"
        },
        # Scenario 3 (P004): Low stock - NO in-transit to show urgent reorder needed
        # Scenario 4 (P005): Out of stock - NO in-transit to show critical situation
        # These scenarios should trigger reorder recommendations without any pending shipments
    ]
    
    # Modify based on scenario
    if scenario == "stale":
        # Make all timestamps old (>24 hours)
        for shipment in shipments:
            shipment["last_updated"] = (now - timedelta(hours=36)).isoformat() + "Z"
    
    return {
        "shipments": shipments,
        "meta": {
            "total_shipments": len(shipments),
            "generated_at": now.isoformat(),
            "scenario": scenario or "normal"
        }
    }


# ==============================================================================
# ENDPOINT 2: FX Rate (USD to ZAR)
# ==============================================================================

@app.get("/api/fx/usd-zar")
def get_fx_rate() -> Dict[str, Any]:
    """
    Returns current USD to ZAR exchange rate.
    
    In production, this would call a real FX API.
    For demo, we use a realistic rate with slight variation.
    """
    
    # Realistic ZAR rate with small variation
    base_rate = 18.50
    variation = random.uniform(-0.10, 0.10)  # ±0.10 ZAR variation
    
    return {
        "rate": round(base_rate + variation, 4),
        "currency_pair": "USD/ZAR",
        "timestamp": datetime.now().isoformat(),
        "source": "Mock FX Provider",
        "bid": round(base_rate + variation - 0.05, 4),
        "ask": round(base_rate + variation + 0.05, 4)
    }


# ==============================================================================
# ENDPOINT 3: Health Check
# ==============================================================================

@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Aura Mock APIs",
        "version": "1.0.0"
    }


# ==============================================================================
# ENDPOINT 4: Supplier Ratings (Future Enhancement)
# ==============================================================================

@app.get("/api/suppliers/ratings")
def get_supplier_ratings() -> Dict[str, Any]:
    """
    Returns supplier quality and delivery ratings.
    
    This endpoint demonstrates how easy it is to add new data sources
    using the extensible template pattern.
    """
    
    suppliers = [
        {
            "supplier_id": "SUP-001",
            "name": "Caterpillar Mining SA",
            "on_time_delivery_pct": 0.94,
            "quality_score": 0.97,
            "avg_lead_time_days": 5,
            "total_orders_ytd": 156
        },
        {
            "supplier_id": "SUP-002",
            "name": "Komatsu Parts Ltd",
            "on_time_delivery_pct": 0.89,
            "quality_score": 0.92,
            "avg_lead_time_days": 7,
            "total_orders_ytd": 89
        },
        {
            "supplier_id": "SUP-003",
            "name": "SafetyFirst Industrial",
            "on_time_delivery_pct": 0.96,
            "quality_score": 0.99,
            "avg_lead_time_days": 3,
            "total_orders_ytd": 234
        },
        {
            "supplier_id": "SUP-004",
            "name": "DrillTech Solutions",
            "on_time_delivery_pct": 0.78,  # Lower reliability
            "quality_score": 0.85,
            "avg_lead_time_days": 10,
            "total_orders_ytd": 45
        },
        {
            "supplier_id": "SUP-005",
            "name": "Bearing World",
            "on_time_delivery_pct": 0.91,
            "quality_score": 0.94,
            "avg_lead_time_days": 4,
            "total_orders_ytd": 178
        }
    ]
    
    return {
        "suppliers": suppliers,
        "last_updated": datetime.now().isoformat()
    }


# ==============================================================================
# ENDPOINT 5: API Documentation
# ==============================================================================

@app.get("/")
def root():
    """API documentation and available endpoints"""
    return {
        "service": "Aura Mock APIs",
        "description": "Mock data sources for the Aura Knowledge Engineering Pipeline",
        "endpoints": {
            "/health": "Health check",
            "/api/shipments/active": "Active logistics shipments",
            "/api/fx/usd-zar": "USD to ZAR exchange rate",
            "/api/suppliers/ratings": "Supplier quality ratings"
        },
        "documentation": "/docs"
    }
