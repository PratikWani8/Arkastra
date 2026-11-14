"""
ARKASTRA: Solar Data Source Registry
Maintains provenance records, configuration, metadata, and status across all external data sources.
"""

from typing import Dict, Any
from datetime import datetime

class SourceRegistry:
    SOURCES: Dict[str, Dict[str, Any]] = {
        "NOAA_SWPC_GOES": {
            "name": "NOAA Space Weather Prediction Center - GOES Primary X-ray Sensor",
            "url": "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json",
            "cadence": "1 minute",
            "wavelengths": ["0.05-0.4nm", "0.1-0.8nm"],
            "unit": "W/m^2",
            "time_standard": "UTC",
            "satellites": ["GOES-16", "GOES-18"],
        },
        "NASA_DONKI": {
            "name": "NASA Space Weather CCMC - Database of Notifications, Knowledge, Information (DONKI)",
            "url": "https://ccmc.gsfc.nasa.gov/DONKI/WS/get/FLR",
            "event_types": ["Solar Flares (FLR)"],
            "flare_classes": ["B", "C", "M", "X"],
            "time_standard": "UTC",
        },
        "NOAA_SWPC_INDICES": {
            "name": "NOAA SWPC Daily Solar Indices",
            "url": "https://services.swpc.noaa.gov/text/daily-solar-indices.txt",
            "cadence": "Daily summary",
            "time_standard": "UTC",
        },
        "NOAA_NCEI_SCIENCE": {
            "name": "NOAA NCEI GOES Space Environment Monitor Science-Quality Archives",
            "url": "https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/science/xrs/",
            "unit": "W/m^2",
            "time_standard": "UTC",
        }
    }

    @classmethod
    def get_provenance_manifest(cls) -> Dict[str, Any]:
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "system": "Arkastra Solar Flare Probability Forecaster",
            "version": "1.0.0",
            "registered_sources": cls.SOURCES
        }
