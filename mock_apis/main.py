"""
Mock API Server

Simulates:
1. Warehouse stock API (serves CSV data)
2. Logistics shipment tracking API
3. FX rate API (USD to ZAR)

Run with: uvicorn mock_apis.main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any
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
def get_active_shipments() -> Dict[str, Any]:
    """
    Returns currently active shipments (in-transit or recently delivered).
    
    TODO: Enhance this with more realistic data
    - Add multiple suppliers
    - Include varied statuses
    - Simulate the "shadow stock" scenario
    """
    
    # Generate mock shipments
    shipments = [
        {
            "shipment_id": "SHP-2024-001",
            "supplier": "Supplier_A",
            "parts": [
                {
                    "part_id": "P001",
                    "quantity_shipped": 20,
                    "unit_cost_usd": 145.50
                },
                {
                    "part_id": "P002",
                    "quantity_shipped": 15,
                    "unit_cost_usd": 98.75
                }
            ],
            "estimated_arrival": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "status": "in_transit",
            "last_updated": (datetime.now() - timedelta(hours=2)).isoformat() + "Z"
        },
        {
            "shipment_id": "SHP-2024-002",
            "supplier": "Supplier_B",
            "parts": [
                {
                    "part_id": "P003",
                    "quantity_shipped": 50,
                    "unit_cost_usd": 42.30
                }
            ],
            "estimated_arrival": datetime.now().strftime("%Y-%m-%d"),
            "status": "delivered",  # This creates the shadow stock scenario!
            "last_updated": (datetime.now() - timedelta(hours=8)).isoformat() + "Z"
        }
    ]
    
    return {"shipments": shipments}


# ==============================================================================
# ENDPOINT 2: FX Rate (USD to ZAR)
# ==============================================================================

@app.get("/api/fx/usd-zar")
def get_fx_rate() -> Dict[str, Any]:
    """
    Returns current USD to ZAR exchange rate.
    
    In production, this would call a real FX API.
    For demo, we use a realistic but static rate.
    """
    
    # TODO: You could make this fluctuate slightly on each call
    # to simulate real FX rate changes
    
    base_rate = 18.50
    variation = random.uniform(-0.05, 0.05)  # ±0.05 ZAR variation
    
    return {
        "rate": round(base_rate + variation, 4),
        "currency_pair": "USD/ZAR",
        "timestamp": datetime.now().isoformat(),
        "source": "Mock FX Provider"
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
        "service": "Aura Mock APIs"
    }
