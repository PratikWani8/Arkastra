"""
ARKASTRA: NASA DONKI Solar Flare Event Client
Collects genuine solar flare events from NASA Space Weather CCMC DONKI API.
Features automatic date-range chunking, retries, and unit conversions.
"""

import logging
import time
import re
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DONKI_BASE_URL = "https://ccmc.gsfc.nasa.gov/DONKI/WS/get/FLR"

def parse_flare_class_to_flux(class_str: Optional[str]) -> Optional[float]:
    """
    Converts astronomical flare classification string (e.g. M1.5, X2.1, C8.4, B5.0)
    to peak X-ray flux in W/m^2.
    A1.0 = 1e-8 W/m^2
    B1.0 = 1e-7 W/m^2
    C1.0 = 1e-6 W/m^2
    M1.0 = 1e-5 W/m^2
    X1.0 = 1e-4 W/m^2
    """
    if not class_str or not isinstance(class_str, str):
        return None
    
    match = re.match(r"^([ABCMX])([0-9]+(?:\.[0-9]+)?)$", class_str.strip().upper())
    if not match:
        return None
    
    letter, magnitude_str = match.groups()
    try:
        magnitude = float(magnitude_str)
    except ValueError:
        return None

    multipliers = {
        'A': 1e-8,
        'B': 1e-7,
        'C': 1e-6,
        'M': 1e-5,
        'X': 1e-4
    }
    return magnitude * multipliers.get(letter, 1e-6)

class DonkiClient:
    def __init__(self, api_key: str = "DEMO_KEY", timeout: int = 25):
        self.api_key = api_key
        self.timeout = timeout

    def fetch_flares_chunk(self, start_date: str, end_date: str, retries: int = 3) -> List[Dict[str, Any]]:
        """
        Fetches flare records for a single sub-window (<= 30 days) from DONKI API.
        """
        params = {
            "startDate": start_date,
            "endDate": end_date,
        }
        headers = {"User-Agent": "Arkastra-Solar-Forecaster/1.0"}

        for attempt in range(1, retries + 1):
            try:
                response = requests.get(DONKI_BASE_URL, params=params, headers=headers, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, list) else []
                elif response.status_code == 429:
                    wait_sec = attempt * 5
                    logger.warning(f"DONKI rate limit hit (429). Retrying in {wait_sec}s...")
                    time.sleep(wait_sec)
                else:
                    logger.warning(f"DONKI query returned status {response.status_code}: {response.text[:200]}")
                    time.sleep(attempt * 2)
            except Exception as e:
                logger.warning(f"Error querying DONKI ({start_date} to {end_date}), attempt {attempt}/{retries}: {e}")
                time.sleep(attempt * 2)

        return []

    def fetch_flares_daterange(self, start_date: str, end_date: str, chunk_days: int = 28) -> pd.DataFrame:
        """
        Retrieves all solar flare events over a large date range by chunking into <= 28 day windows.
        """
        dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        dt_end = datetime.strptime(end_date, "%Y-%m-%d")
        
        all_records: List[Dict[str, Any]] = []
        current_start = dt_start

        logger.info(f"Collecting DONKI solar flares from {start_date} to {end_date} in {chunk_days}-day chunks...")

        while current_start < dt_end:
            current_end = min(current_start + timedelta(days=chunk_days), dt_end)
            s_str = current_start.strftime("%Y-%m-%d")
            e_str = current_end.strftime("%Y-%m-%d")
            
            chunk_data = self.fetch_flares_chunk(s_str, e_str)
            logger.info(f"DONKI chunk [{s_str} -> {e_str}]: found {len(chunk_data)} flares.")
            all_records.extend(chunk_data)
            
            current_start = current_end + timedelta(days=1)
            time.sleep(0.5) # Gentle rate-limit respect

        if not all_records:
            logger.warning("No DONKI flare records found for requested range.")
            return pd.DataFrame()

        # Parse into standardized DataFrame
        parsed_rows = []
        for flr in all_records:
            flr_id = flr.get("flrID", "")
            begin_time_str = flr.get("beginTime")
            peak_time_str = flr.get("peakTime")
            end_time_str = flr.get("endTime")
            class_type = flr.get("classType", "")
            source_loc = flr.get("sourceLocation", "")
            instruments = flr.get("instruments", [])
            inst_name = instruments[0].get("displayName", "") if instruments else ""

            # Class letter & flux
            class_letter = class_type[0].upper() if class_type else "UNKNOWN"
            peak_flux = parse_flare_class_to_flux(class_type)

            parsed_rows.append({
                "event_id": flr_id,
                "begin_time": pd.to_datetime(begin_time_str, utc=True) if begin_time_str else None,
                "peak_time": pd.to_datetime(peak_time_str, utc=True) if peak_time_str else None,
                "end_time": pd.to_datetime(end_time_str, utc=True) if end_time_str else None,
                "flare_class": class_type.strip() if class_type else "UNKNOWN",
                "class_category": class_letter,
                "peak_flux": peak_flux,
                "source_location": source_loc,
                "instrument": inst_name,
                "source": "NASA_DONKI",
                "is_m_plus": class_letter in ["M", "X"],
                "is_x_plus": class_letter == "X"
            })

        df = pd.DataFrame(parsed_rows)
        # Drop duplicates by event_id or near-identical begin/peak time
        df = df.drop_duplicates(subset=["event_id"]).sort_values("begin_time").reset_index(drop=True)
        logger.info(f"Total deduplicated DONKI flares: {len(df)} (M/X flares: {df['is_m_plus'].sum()})")
        return df

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = DonkiClient()
    df = client.fetch_flares_daterange("2024-01-01", "2024-02-15")
    print(df.head())
