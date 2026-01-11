"""
Base Source Template for Extensibility

To add a new data source:
1. Create a new class that inherits from BaseSource
2. Implement load_raw_data() method
3. Add configuration to sources.yaml
4. The pipeline will automatically pick it up
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Iterator, Dict, Any
import dlt


class BaseSource(ABC):
    """
    Abstract base class for all data sources.
    
    This template ensures consistent metadata and reliability tracking
    across all sources, making it easy to add new sources with minimal code.
    """
    
    def __init__(
        self, 
        name: str, 
        reliability_score: float,
        source_type: str,
        update_frequency: str = "unknown"
    ):
        """
        Args:
            name: Unique identifier for this source
            reliability_score: 0.0-1.0, indicates data quality
            source_type: "csv", "api", "database", etc.
            update_frequency: How often data refreshes
        """
        self.name = name
        self.reliability_score = reliability_score
        self.source_type = source_type
        self.update_frequency = update_frequency
        
        # Validate reliability score
        if not 0.0 <= reliability_score <= 1.0:
            raise ValueError(f"Reliability score must be between 0 and 1, got {reliability_score}")
    
    @abstractmethod
    def load_raw_data(self) -> Iterator[Dict[str, Any]]:
        """
        Load raw data from the source.
        
        Must yield dictionaries with at least:
        - A unique identifier field
        - A timestamp field
        - Business data fields
        
        Returns:
            Iterator of dictionaries (one per record)
        """
        pass
    
    @dlt.resource(name="raw_data", write_disposition="append")
    def to_dlt_resource(self) -> Iterator[Dict[str, Any]]:
        """
        Converts source data into a DLT resource with standardized metadata.
        
        This is what DLT will actually ingest. It automatically adds:
        - Source system identifier
        - Reliability score
        - Ingestion timestamp
        - Source type
        
        This metadata is critical for downstream conflict resolution.
        """
        for record in self.load_raw_data():
            yield {
                **record,  # Original data
                # Standard metadata (used in Silver/Gold layers)
                "_source_system": self.name,
                "_source_type": self.source_type,
                "_reliability_score": self.reliability_score,
                "_update_frequency": self.update_frequency,
                "_ingested_at": datetime.now(timezone.utc).isoformat(),
            }
    
    def get_metadata(self) -> Dict[str, Any]:
        """Returns source metadata for documentation/debugging"""
        return {
            "name": self.name,
            "type": self.source_type,
            "reliability_score": self.reliability_score,
            "update_frequency": self.update_frequency,
        }