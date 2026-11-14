"""
ARKASTRA: NOAA GOES XRS Sensor Client
Collects real solar X-ray flux measurements (0.05-0.4nm and 0.1-0.8nm) from NOAA SWPC.
"""

import logging
import time
import requests
import pandas as pd
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

PRIMARY_XRAYS_URL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json"
SECONDARY_XRAYS_URL = "https://services.swpc.noaa.gov/json/goes/secondary/xrays-7-day.json"
PRIMARY_6HR_URL = "https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json"

class GoesClient:
    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def fetch_recent_flux(self, endpoint: str = PRIMARY_XRAYS_URL) -> pd.DataFrame:
        """
        Fetch real GOES X-ray sensor observations from NOAA SWPC.
        Raw records contain short (0.05-0.4nm) and long (0.1-0.8nm) wavelength fluxes.
        """
        logger.info(f"Fetching GOES X-ray data from {endpoint}...")
        headers = {"User-Agent": "Arkastra-Solar-Forecaster/1.0"}
        
        response = requests.get(endpoint, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        raw_data = response.json()
        
        if not raw_data:
            logger.warning("Empty response received from NOAA GOES endpoint.")
            return pd.DataFrame()

        df_raw = pd.DataFrame(raw_data)
        logger.info(f"Retrieved {len(df_raw)} raw measurement points.")
        return self._normalize_goes_measurements(df_raw)

    def _normalize_goes_measurements(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Pivots and aligns 0.05-0.4nm (short) and 0.1-0.8nm (long) flux measurements
        onto a clean chronological grid.
        """
        if df_raw.empty or 'time_tag' not in df_raw.columns:
            return pd.DataFrame()

        df_raw['timestamp'] = pd.to_datetime(df_raw['time_tag'], utc=True)
        satellite_id = df_raw['satellite'].iloc[0] if 'satellite' in df_raw.columns else 16

        # Short flux: energy == "0.05-0.4nm"
        # Long flux: energy == "0.1-0.8nm"
        short_df = df_raw[df_raw['energy'] == '0.05-0.4nm'][['timestamp', 'flux']].rename(columns={'flux': 'short_flux'})
        long_df = df_raw[df_raw['energy'] == '0.1-0.8nm'][['timestamp', 'flux', 'observed_flux']].rename(columns={'flux': 'long_flux', 'observed_flux': 'long_flux_observed'})

        merged = pd.merge(short_df, long_df, on='timestamp', how='outer').sort_values('timestamp').reset_index(drop=True)
        merged['satellite_id'] = int(satellite_id) if pd.notna(satellite_id) else 16
        merged['source'] = 'NOAA_SWPC_GOES'

        # Physical validity checks: solar X-ray flux is strictly positive (typically 1e-9 to 1e-2 W/m^2)
        valid_mask = (merged['long_flux'] > 0) & (merged['long_flux'] < 0.1)
        merged['quality_status'] = 'GOOD'
        merged.loc[~valid_mask, 'quality_status'] = 'BAD'

        # Compute flux ratio where both are valid
        valid_both = valid_mask & (merged['short_flux'] > 0)
        merged['flux_ratio'] = None
        merged.loc[valid_both, 'flux_ratio'] = merged.loc[valid_both, 'short_flux'] / merged.loc[valid_both, 'long_flux']

        return merged

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = GoesClient()
    df = client.fetch_recent_flux()
    print(f"Loaded {len(df)} records. Sample:")
    print(df.head())
