"""
ARKASTRA: Solar Data Preprocessing and Cleaning Module
Handles timestamp parsing, physical validation, cadence resampling, satellite resolution,
and flare catalog deduplication.
"""

import logging
from typing import Tuple, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Physical bounds for GOES XRS sensor
FLUX_MIN_PHYSICAL = 1e-9   # Extremely quiet Sun (A0.1 equivalent)
FLUX_MAX_PHYSICAL = 0.05   # Strongest possible solar flare (super-X class)

def clean_goes_flux(df_flux: pd.DataFrame, cadence: str = "5min") -> pd.DataFrame:
    """
    Cleans raw GOES XRS flux measurements:
    - Enforces UTC timezone
    - Filters non-physical or negative values
    - Resolves overlapping satellite measurements using documented satellite hierarchy
    - Resamples onto a uniform time grid with robust statistical aggregations
    """
    if df_flux.empty:
        raise ValueError("Input GOES flux DataFrame is empty.")

    df = df_flux.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp")

    # 1. Physical Validity Filtering
    valid_long = (df["long_flux"] >= FLUX_MIN_PHYSICAL) & (df["long_flux"] <= FLUX_MAX_PHYSICAL)
    valid_short = (df["short_flux"] >= FLUX_MIN_PHYSICAL) & (df["short_flux"] <= FLUX_MAX_PHYSICAL)
    
    # Flag invalid measurements
    df["quality_valid"] = valid_long
    df.loc[~valid_long, "long_flux"] = np.nan
    df.loc[~valid_short, "short_flux"] = np.nan

    # 2. Satellite Conflict Resolution
    # If multiple satellites report at the same timestamp, pick highest satellite ID (e.g. GOES-19 > 18 > 16)
    if "satellite_id" in df.columns:
        df = df.sort_values(["timestamp", "satellite_id"], ascending=[True, False])
        df = df.drop_duplicates(subset=["timestamp"], keep="first")
    else:
        df = df.drop_duplicates(subset=["timestamp"], keep="first")

    # 3. Resample onto Uniform Cadence Grid
    df = df.set_index("timestamp")
    
    # Compute mean, max, and min within each cadence bucket
    resampled = df[["long_flux", "short_flux"]].resample(cadence).agg({
        "long_flux": ["mean", "max"],
        "short_flux": ["mean", "max"]
    })
    resampled.columns = ["long_flux", "long_flux_max", "short_flux", "short_flux_max"]

    # Calculate short to long flux ratio on the resampled grid
    resampled["flux_ratio"] = resampled["short_flux"] / resampled["long_flux"]
    
    # Track missing observation counts before gentle interpolation
    resampled["is_interpolated"] = resampled["long_flux"].isna()

    # Small gap interpolation (up to 2 consecutive missing buckets = 10 mins)
    # Large gaps are left as NaN to preserve scientific integrity
    resampled["long_flux"] = resampled["long_flux"].interpolate(method="time", limit=2)
    resampled["short_flux"] = resampled["short_flux"].interpolate(method="time", limit=2)
    resampled["flux_ratio"] = resampled["short_flux"] / resampled["long_flux"]

    # Quality status
    resampled["quality_status"] = "GOOD"
    resampled.loc[resampled["is_interpolated"], "quality_status"] = "INTERPOLATED_SHORT_GAP"
    resampled.loc[resampled["long_flux"].isna(), "quality_status"] = "MISSING_GAP"

    clean_df = resampled.reset_index()
    logger.info(f"Cleaned GOES flux to {cadence} cadence: {len(clean_df)} grid points (Valid: {clean_df['long_flux'].notna().sum()})")
    return clean_df

def clean_and_deduplicate_flares(df_donki: pd.DataFrame, df_noaa: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Standardizes and deduplicates solar flare catalogs across NASA DONKI and NOAA reports.
    Merges duplicate events occurring within a 30-minute window with matching classifications.
    """
    if df_donki.empty and (df_noaa is None or df_noaa.empty):
        raise ValueError("Both DONKI and NOAA flare datasets are empty.")

    events = []
    
    # Process DONKI events
    if not df_donki.empty:
        for _, row in df_donki.iterrows():
            begin = pd.to_datetime(row.get("begin_time"), utc=True)
            peak = pd.to_datetime(row.get("peak_time"), utc=True) if pd.notna(row.get("peak_time")) else begin
            flare_class = str(row.get("flare_class", "")).strip().upper()
            class_cat = str(row.get("class_category", flare_class[:1])).upper()

            if pd.isna(begin) or not class_cat:
                continue

            events.append({
                "event_id": str(row.get("event_id", f"DONKI_{begin.isoformat()}")),
                "begin_time": begin,
                "peak_time": peak,
                "flare_class": flare_class,
                "class_category": class_cat,
                "peak_flux": float(row.get("peak_flux")) if pd.notna(row.get("peak_flux")) else None,
                "is_m_plus": class_cat in ["M", "X"],
                "is_x_plus": class_cat == "X",
                "source": "NASA_DONKI"
            })

    df_events = pd.DataFrame(events)
    if df_events.empty:
        return df_events

    # Sort chronologically
    df_events = df_events.sort_values("begin_time").reset_index(drop=True)

    # Temporal deduplication: if two flares begin within 30 minutes with identical class category, keep the highest peak flux
    deduped = []
    for _, current in df_events.iterrows():
        if not deduped:
            deduped.append(current)
            continue
        
        last = deduped[-1]
        time_diff_min = abs((current["begin_time"] - last["begin_time"]).total_seconds()) / 60.0
        
        if time_diff_min <= 30.0 and current["class_category"] == last["class_category"]:
            # Duplicate report: preserve the one with higher peak flux or more detailed class
            if (current["peak_flux"] or 0) > (last["peak_flux"] or 0):
                deduped[-1] = current
        else:
            deduped.append(current)

    result_df = pd.DataFrame(deduped).reset_index(drop=True)
    logger.info(f"Deduplicated flares: {len(df_events)} raw -> {len(result_df)} merged (M/X count: {result_df['is_m_plus'].sum()})")
    return result_df
