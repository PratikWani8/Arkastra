"""
ARKASTRA: Real Solar Data Collection Pipeline
Orchestrates downloading, validating, and persisting genuine solar observation data
from NOAA GOES and NASA DONKI APIs.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

# Ensure matplotlib uses a writable temp cache directory
os.environ["MPLCONFIGDIR"] = os.path.join(os.path.dirname(__file__), "..", ".mpl_cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Add training and app root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from training.data_sources.goes_client import GoesClient, PRIMARY_XRAYS_URL, SECONDARY_XRAYS_URL
from training.data_sources.donki_client import DonkiClient
from training.data_sources.noaa_client import NoaaClient
from training.data_sources.source_registry import SourceRegistry

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ArkastraDataCollector")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_DATA_DIR = os.path.join(BASE_DIR, "datasets", "raw")
REPORTS_DIR = os.path.join(BASE_DIR, "datasets", "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")

os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

def run_collection(start_date: str = "2023-01-01", end_date: Optional[str] = None):
    if end_date is None:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")

    logger.info("==================================================")
    logger.info("ARKASTRA DATA COLLECTION PIPELINE INITIATED")
    logger.info(f"Target Range: {start_date} -> {end_date}")
    logger.info("==================================================")

    # 1. Collect Real GOES XRS flux data
    logger.info("1/3 Collecting real GOES X-ray flux telemetry from NOAA SWPC...")
    goes_client = GoesClient()
    df_primary_flux = goes_client.fetch_recent_flux(PRIMARY_XRAYS_URL)
    df_secondary_flux = pd.DataFrame()
    try:
        df_secondary_flux = goes_client.fetch_recent_flux(SECONDARY_XRAYS_URL)
    except Exception as e:
        logger.warning(f"Secondary GOES stream unavailable ({e}), proceeding with primary.")

    # Combine primary and secondary observations with deduplication
    df_flux = pd.concat([df_primary_flux, df_secondary_flux], ignore_index=True)
    if not df_flux.empty:
        df_flux = df_flux.drop_duplicates(subset=["timestamp", "satellite_id"]).sort_values("timestamp").reset_index(drop=True)
    
    # Save raw GOES flux
    goes_parquet_path = os.path.join(RAW_DATA_DIR, "goes_xray_raw.parquet")
    df_flux.to_parquet(goes_parquet_path, index=False)
    logger.info(f"Saved {len(df_flux)} GOES flux observations to {goes_parquet_path}")

    # 2. Collect Real NASA DONKI solar flare event catalog
    logger.info(f"2/3 Collecting real NASA DONKI flare catalog ({start_date} to {end_date})...")
    donki_client = DonkiClient()
    df_donki_flares = donki_client.fetch_flares_daterange(start_date, end_date)
    
    donki_json_path = os.path.join(RAW_DATA_DIR, "donki_flares_raw.json")
    if not df_donki_flares.empty:
        df_donki_flares.to_json(donki_json_path, orient="records", date_format="iso", indent=2)
    logger.info(f"Saved {len(df_donki_flares)} NASA DONKI flare events to {donki_json_path}")

    # 3. Collect Real NOAA SWPC Daily Solar Indices & Flare Counts
    logger.info("3/3 Collecting NOAA SWPC Daily Solar Indices & Flare statistics...")
    noaa_client = NoaaClient()
    df_noaa_indices = noaa_client.fetch_daily_indices()
    
    noaa_parquet_path = os.path.join(RAW_DATA_DIR, "noaa_flares_raw.parquet")
    if not df_noaa_indices.empty:
        df_noaa_indices.to_parquet(noaa_parquet_path, index=False)
    logger.info(f"Saved {len(df_noaa_indices)} NOAA daily solar records to {noaa_parquet_path}")

    # 4. Generate Comprehensive Data Quality Report
    logger.info("Generating Data Quality and Provenance Report...")
    flare_classes = df_donki_flares["class_category"].value_counts().to_dict() if not df_donki_flares.empty else {}
    m_count = int(flare_classes.get("M", 0))
    x_count = int(flare_classes.get("X", 0))
    c_count = int(flare_classes.get("C", 0))
    b_count = int(flare_classes.get("B", 0))

    flux_min = float(df_flux["long_flux"].min()) if not df_flux.empty and "long_flux" in df_flux else 0.0
    flux_max = float(df_flux["long_flux"].max()) if not df_flux.empty and "long_flux" in df_flux else 0.0
    flux_mean = float(df_flux["long_flux"].mean()) if not df_flux.empty and "long_flux" in df_flux else 0.0
    satellite_dist = df_flux["satellite_id"].value_counts().to_dict() if not df_flux.empty else {}

    report = {
        "report_generated_utc": datetime.utcnow().isoformat() + "Z",
        "dataset_version": "1.0.0",
        "collection_window": {
            "requested_start": start_date,
            "requested_end": end_date,
            "flux_start": df_flux["timestamp"].min().isoformat() if not df_flux.empty else None,
            "flux_end": df_flux["timestamp"].max().isoformat() if not df_flux.empty else None,
        },
        "goes_flux_telemetry": {
            "total_observations": len(df_flux),
            "satellites_present": {str(k): int(v) for k, v in satellite_dist.items()},
            "quality_status_distribution": df_flux["quality_status"].value_counts().to_dict() if not df_flux.empty else {},
            "long_flux_stats_w_m2": {
                "min": flux_min,
                "max": flux_max,
                "mean": flux_mean
            },
            "missing_long_flux": int(df_flux["long_flux"].isna().sum()) if not df_flux.empty else 0,
            "missing_short_flux": int(df_flux["short_flux"].isna().sum()) if not df_flux.empty else 0,
        },
        "nasa_donki_flare_catalog": {
            "total_flare_events": len(df_donki_flares),
            "class_distribution": flare_classes,
            "strong_flare_events": {
                "m_class_count": m_count,
                "x_class_count": x_count,
                "total_m_plus": m_count + x_count,
                "c_class_count": c_count,
                "b_class_count": b_count
            },
            "first_flare_event": df_donki_flares["begin_time"].min().isoformat() if not df_donki_flares.empty else None,
            "last_flare_event": df_donki_flares["begin_time"].max().isoformat() if not df_donki_flares.empty else None
        },
        "noaa_swpc_indices": {
            "total_daily_records": len(df_noaa_indices),
            "date_range": {
                "start": df_noaa_indices["date"].min() if not df_noaa_indices.empty else None,
                "end": df_noaa_indices["date"].max() if not df_noaa_indices.empty else None,
            }
        },
        "provenance_metadata": SourceRegistry.get_provenance_manifest()
    }

    report_path = os.path.join(REPORTS_DIR, "collection_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved collection report to {report_path}")

    # 5. Generate Data Coverage Visualization
    generate_coverage_figure(df_flux, df_donki_flares, FIGURES_DIR)

    logger.info("==================================================")
    logger.info("PHASE 2 DATA COLLECTION COMPLETED SUCCESSFULLY")
    logger.info(f"Summary: {len(df_flux)} GOES observations, {len(df_donki_flares)} NASA DONKI flares ({m_count + x_count} M/X class flares)")
    logger.info("==================================================")
    return report

def generate_coverage_figure(df_flux: pd.DataFrame, df_flares: pd.DataFrame, figures_dir: str):
    """
    Plots historical solar X-ray flux and recorded flare events.
    """
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=False, gridspec_kw={'height_ratios': [2, 1]})
        fig.patch.set_facecolor('#080d1a')
        ax1.set_facecolor('#0d1326')
        ax2.set_facecolor('#0d1326')

        # Top Plot: GOES X-ray Flux
        if not df_flux.empty and "long_flux" in df_flux:
            sample_step = max(1, len(df_flux) // 2000)
            sub_flux = df_flux.iloc[::sample_step]
            ax1.semilogy(sub_flux["timestamp"], sub_flux["long_flux"], color='#f59e0b', label="GOES Long Flux 0.1-0.8nm", lw=1.2)
            if "short_flux" in sub_flux and sub_flux["short_flux"].notna().any():
                ax1.semilogy(sub_flux["timestamp"], sub_flux["short_flux"], color='#38bdf8', label="GOES Short Flux 0.05-0.4nm", lw=0.9, alpha=0.8)

            # Draw flare threshold lines
            ax1.axhline(1e-4, color='#ef4444', linestyle='--', alpha=0.8, label="X-Class Flare (1e-4 W/m²)")
            ax1.axhline(1e-5, color='#f97316', linestyle='--', alpha=0.8, label="M-Class Flare (1e-5 W/m²)")
            ax1.axhline(1e-6, color='#eab308', linestyle=':', alpha=0.6, label="C-Class Flare (1e-6 W/m²)")

            ax1.set_title("ARKASTRA: NOAA GOES Primary Solar X-Ray Flux Telemetry", color='#f8fafc', fontsize=13, fontweight='bold')
            ax1.set_ylabel("X-Ray Flux (W/m²)", color='#94a3b8')
            ax1.tick_params(colors='#94a3b8')
            ax1.grid(True, which="both", color='#1e293b', alpha=0.5)
            ax1.legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', loc='upper right')

        # Bottom Plot: NASA DONKI Flare Event Distribution by Class
        if not df_flares.empty:
            class_counts = df_flares["class_category"].value_counts()
            colors = {'X': '#ef4444', 'M': '#f97316', 'C': '#eab308', 'B': '#38bdf8', 'UNKNOWN': '#64748b'}
            bar_colors = [colors.get(c, '#64748b') for c in class_counts.index]
            bars = ax2.bar(class_counts.index, class_counts.values, color=bar_colors, edgecolor='#000000', width=0.5)
            
            for bar in bars:
                height = bar.get_height()
                ax2.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), textcoords="offset points",
                            ha='center', va='bottom', color='#f8fafc', fontsize=10, fontweight='bold')

            ax2.set_title("NASA DONKI Historical Solar Flare Catalog by Class Category", color='#f8fafc', fontsize=12)
            ax2.set_ylabel("Event Count", color='#94a3b8')
            ax2.tick_params(colors='#94a3b8')
            ax2.grid(True, axis='y', color='#1e293b', alpha=0.5)

        plt.tight_layout()
        output_fig = os.path.join(figures_dir, "data_coverage.png")
        plt.savefig(output_fig, dpi=160, facecolor=fig.get_facecolor())
        plt.close(fig)
        logger.info(f"Saved data coverage figure to {output_fig}")
    except Exception as e:
        logger.warning(f"Failed generating coverage figure: {e}")

if __name__ == "__main__":
    from typing import Optional
    start = sys.argv[1] if len(sys.argv) > 1 else "2023-01-01"
    end = sys.argv[2] if len(sys.argv) > 2 else "2024-06-01"
    run_collection(start, end)
