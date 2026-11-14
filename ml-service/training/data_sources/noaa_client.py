"""
ARKASTRA: NOAA SWPC Solar Flare Event Client
Collects solar flare event reports and indices from NOAA Space Weather Prediction Center.
"""

import logging
import re
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

SWPC_DAILY_INDICES_URL = "https://services.swpc.noaa.gov/text/daily-solar-indices.txt"
SWPC_SOLAR_PROBS_URL = "https://services.swpc.noaa.gov/text/solar-probabilities.txt"

class NoaaClient:
    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def fetch_daily_indices(self) -> pd.DataFrame:
        """
        Parses NOAA daily solar activity indices text file containing daily flare counts (C, M, X).
        """
        logger.info(f"Fetching NOAA daily solar indices from {SWPC_DAILY_INDICES_URL}...")
        headers = {"User-Agent": "Arkastra-Solar-Forecaster/1.0"}
        response = requests.get(SWPC_DAILY_INDICES_URL, headers=headers, timeout=self.timeout)
        response.raise_for_status()

        rows = []
        for line in response.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(":"):
                continue
            parts = line.split()
            # Standard SWPC format: YYYY MM DD  RadioFlux  SunspotNo  SunspotArea  NewRegions  ... C M X flares
            if len(parts) >= 12 and parts[0].isdigit() and len(parts[0]) == 4:
                try:
                    date_str = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                    radio_flux = float(parts[3]) if parts[3] != "-1" else None
                    sunspot_num = int(parts[4]) if parts[4] != "-1" else None
                    c_flares = int(parts[8]) if len(parts) > 8 and parts[8].isdigit() else 0
                    m_flares = int(parts[9]) if len(parts) > 9 and parts[9].isdigit() else 0
                    x_flares = int(parts[10]) if len(parts) > 10 and parts[10].isdigit() else 0

                    rows.append({
                        "date": date_str,
                        "radio_flux_10cm": radio_flux,
                        "sunspot_number": sunspot_num,
                        "c_flares": c_flares,
                        "m_flares": m_flares,
                        "x_flares": x_flares,
                        "has_m_plus": (m_flares + x_flares) > 0,
                        "source": "NOAA_SWPC_INDICES"
                    })
                except Exception as e:
                    continue

        df = pd.DataFrame(rows)
        logger.info(f"Parsed {len(df)} daily index records from NOAA SWPC.")
        return df

    def fetch_current_flare_probabilities(self) -> Dict[str, Any]:
        """
        Parses NOAA official space weather flare probabilities (24h/48h/72h C, M, X class probabilities).
        Useful for benchmark comparison against official space weather forecasters.
        """
        logger.info(f"Fetching official NOAA solar probabilities from {SWPC_SOLAR_PROBS_URL}...")
        headers = {"User-Agent": "Arkastra-Solar-Forecaster/1.0"}
        try:
            response = requests.get(SWPC_SOLAR_PROBS_URL, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                text = response.text
                probs = {}
                # Match e.g., Class M    25/25/20 or Class X    05/05/01
                m_match = re.search(r"Class M\s+(\d+)/(\d+)/(\d+)", text)
                x_match = re.search(r"Class X\s+(\d+)/(\d+)/(\d+)", text)
                if m_match:
                    probs["noaa_prob_m_24h"] = int(m_match.group(1)) / 100.0
                if x_match:
                    probs["noaa_prob_x_24h"] = int(x_match.group(1)) / 100.0
                return probs
        except Exception as e:
            logger.warning(f"Could not fetch NOAA solar probabilities: {e}")
        return {}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = NoaaClient()
    df = client.fetch_daily_indices()
    print(df.tail())
    print("Probabilities:", client.fetch_current_flare_probabilities())
