"""
Logistics API Source

Characteristics:
- Real-time API updates (every 2 hours)
- Nested JSON structure
- Higher reliability (0.9)
- Represents "in-transit" inventory
- Requires flattening and USD→ZAR conversion
"""

import requests
from typing import Iterator, Dict, Any
from datetime import datetime
from .base_source import BaseSource


class LogisticsSource(BaseSource):
    """
    Ingests shipment tracking data from logistics provider API.
    
    API returns nested JSON:
    {
      "shipments": [
        {
          "shipment_id": "SHP-001",
          "supplier": "Supplier_A",
          "parts": [
            {"part_id": "P001", "quantity_shipped": 20, "unit_cost_usd": 145.50}
          ],
          "estimated_arrival": "2024-01-08",
          "status": "in_transit",
          "last_updated": "2024-01-06T10:30:00Z"
        }
      ]
    }
    """
    
    def __init__(
        self, 
        api_endpoint: str,
        fx_rate_endpoint: str,
        reliability_score: float = 0.9
    ):
        super().__init__(
            name="logistics_shipments",
            reliability_score=reliability_score,
            source_type="api",
            update_frequency="realtime"
        )
        self.api_endpoint = api_endpoint
        self.fx_rate_endpoint = fx_rate_endpoint
    
    def load_raw_data(self) -> Iterator[Dict[str, Any]]:
        """
        Fetch shipment data from API and flatten nested structure.
        
        TODO: Implement this method:
        1. Fetch data from self.api_endpoint
        2. Get current USD→ZAR rate from self.fx_rate_endpoint
        3. Flatten nested "parts" array
        4. Convert USD costs to ZAR
        5. Yield one record per part (not per shipment)
        """
        try:
            # Fetch shipment data
            response = requests.get(self.api_endpoint, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Fetch FX rate
            fx_response = requests.get(self.fx_rate_endpoint, timeout=10)
            fx_response.raise_for_status()
            fx_rate = fx_response.json()["rate"]
            
            # TODO: Flatten and yield records
            # Hint: Loop through shipments, then loop through parts within each shipment
            # Each part becomes a separate record
            
            for shipment in data.get("shipments", []):
                shipment_id = shipment["shipment_id"]
                supplier = shipment["supplier"]
                status = shipment["status"]
                estimated_arrival = shipment["estimated_arrival"]
                last_updated = shipment["last_updated"]
                
                # Flatten parts
                for part in shipment.get("parts", []):
                    # Convert USD to ZAR
                    unit_cost_usd = part["unit_cost_usd"]
                    unit_cost_zar = unit_cost_usd * fx_rate
                    
                    yield {
                        "shipment_id": shipment_id,
                        "part_id": part["part_id"],
                        "quantity": part["quantity_shipped"],
                        "unit_cost_zar": round(unit_cost_zar, 2),
                        "unit_cost_usd": unit_cost_usd,
                        "fx_rate_used": fx_rate,
                        "supplier": supplier,
                        "status": status,
                        "estimated_arrival": estimated_arrival,
                        "last_updated": last_updated,
                        # Add semantic context
                        "quantity_semantic": "in_transit",  # Critical for conflict resolution
                    }
        
        except requests.RequestException as e:
            # TODO: Implement proper error handling
            # In production, you'd want to:
            # - Log the error
            # - Maybe retry with exponential backoff
            # - Store failed fetches for manual review
            print(f"Error fetching logistics data: {e}")
            raise
