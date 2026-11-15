"""
ARKASTRA: Solar Time-Series Feature Engineering & EDA Pipeline
Extracts astrophysics-grounded time-series features from GOES X-ray flux and recent flare history:
- Multi-scale rolling extrema (1h, 3h, 6h, 12h, 24h)
- Flux gradients, acceleration, and short-to-long wavelength ratios
- Historical flare counts in lookback windows (6h, 24h, 7d)
- Time since last M-class and X-class events
- Strict prevention of future information leakage
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

# Ensure matplotlib writable temp cache
os.environ["MPLCONFIGDIR"] = os.path.join(os.path.dirname(__file__), "..", ".mpl_cache")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROCESSED_DIR = os.path.join(BASE_DIR, "datasets", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "datasets", "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")
RAW_DIR = os.path.join(BASE_DIR, "datasets", "raw")

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

SAFE_LOG_FLOOR = 1e-9 # W/m^2 positive floor for numerical stability

FEATURE_NAMES = [
    # 1. Direct and Log Flux Features
    "long_flux",
    "short_flux",
    "log_long_flux",
    "log_short_flux",
    "flux_ratio",
    
    # 2. Rolling Lookback Extrema & Averages (Lookback ONLY: closed='left' or shift(1))
    "max_flux_1h",
    "max_flux_3h",
    "max_flux_6h",
    "max_flux_12h",
    "max_flux_24h",
    "mean_flux_6h",
    "mean_flux_12h",
    "mean_flux_24h",
    "std_flux_24h",
    
    # 3. Dynamic Trends, Rate of Increase, & Acceleration
    "flux_change_1h",
    "flux_change_3h",
    "flux_change_6h",
    "flux_derivative_1h",
    "flux_acceleration_3h",
    "flux_volatility_ratio",
    
    # 4. Temporal & Solar Cyclical Features
    "hour_of_day",
    "day_of_year",
    "sin_hour",
    "cos_hour",
    "sin_doy",
    "cos_doy",
    
    # 5. Historical Flare Precursor Features (Lookback ONLY)
    "m_flares_prev_6h",
    "m_flares_prev_24h",
    "m_flares_prev_7d",
    "x_flares_prev_24h",
    "hours_since_last_m_flare",
    "hours_since_last_x_flare"
]

def compute_solar_features(
    df_observations: pd.DataFrame, 
    df_historical_flares: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Computes genuine astrophysics-grounded features for each observation timestamp t.
    All rolling windows look STRICTLY BACKWARD (t - lookback to t) to guarantee zero leakage.
    """
    df = df_observations.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # 1. Base Flux & Safe Log Transforms
    df["long_flux"] = np.clip(df["long_flux"].fillna(SAFE_LOG_FLOOR), SAFE_LOG_FLOOR, 0.1)
    df["short_flux"] = np.clip(df["short_flux"].fillna(SAFE_LOG_FLOOR * 0.2), SAFE_LOG_FLOOR * 0.1, 0.05)
    
    df["log_long_flux"] = np.log10(df["long_flux"])
    df["log_short_flux"] = np.log10(df["short_flux"])
    df["flux_ratio"] = df["short_flux"] / df["long_flux"]

    # 2. Multi-scale Rolling Features (computed along chronological index)
    # Note: assuming hourly cadence in training dataset; rolling(window=k) covers k hours
    df["max_flux_1h"] = df["long_flux"].rolling(window=2, min_periods=1).max()
    df["max_flux_3h"] = df["long_flux"].rolling(window=3, min_periods=1).max()
    df["max_flux_6h"] = df["long_flux"].rolling(window=6, min_periods=1).max()
    df["max_flux_12h"] = df["long_flux"].rolling(window=12, min_periods=1).max()
    df["max_flux_24h"] = df["long_flux"].rolling(window=24, min_periods=1).max()

    df["mean_flux_6h"] = df["long_flux"].rolling(window=6, min_periods=1).mean()
    df["mean_flux_12h"] = df["long_flux"].rolling(window=12, min_periods=1).mean()
    df["mean_flux_24h"] = df["long_flux"].rolling(window=24, min_periods=1).mean()
    df["std_flux_24h"] = df["long_flux"].rolling(window=24, min_periods=2).std().fillna(0.0)

    # 3. Dynamic Trends & Rate of Increase
    df["flux_change_1h"] = df["long_flux"] - df["long_flux"].shift(1).fillna(df["long_flux"])
    df["flux_change_3h"] = df["long_flux"] - df["long_flux"].shift(3).fillna(df["long_flux"])
    df["flux_change_6h"] = df["long_flux"] - df["long_flux"].shift(6).fillna(df["long_flux"])
    
    # First derivative (rate of increase per hour)
    df["flux_derivative_1h"] = df["flux_change_1h"] / 1.0
    
    # Second derivative (acceleration: change in derivative over 3h)
    deriv_prev = df["flux_derivative_1h"].shift(3).fillna(df["flux_derivative_1h"])
    df["flux_acceleration_3h"] = (df["flux_derivative_1h"] - deriv_prev) / 3.0
    
    # Volatility ratio: current flux relative to 24h background mean
    df["flux_volatility_ratio"] = df["long_flux"] / (df["mean_flux_24h"] + 1e-12)

    # 4. Temporal Features
    hours = df["timestamp"].dt.hour
    doy = df["timestamp"].dt.dayofyear
    df["hour_of_day"] = hours
    df["day_of_year"] = doy
    df["sin_hour"] = np.sin(2.0 * np.pi * hours / 24.0)
    df["cos_hour"] = np.cos(2.0 * np.pi * hours / 24.0)
    df["sin_doy"] = np.sin(2.0 * np.pi * doy / 365.25)
    df["cos_doy"] = np.cos(2.0 * np.pi * doy / 365.25)

    # 5. Historical Flare Precursors (Computed STRICTLY from past events before timestamp t)
    m_flares_6h = np.zeros(len(df), dtype=int)
    m_flares_24h = np.zeros(len(df), dtype=int)
    m_flares_7d = np.zeros(len(df), dtype=int)
    x_flares_24h = np.zeros(len(df), dtype=int)
    since_m_hours = np.full(len(df), 168.0, dtype=float) # Cap default at 7 days (168h)
    since_x_hours = np.full(len(df), 720.0, dtype=float) # Cap default at 30 days (720h)

    if df_historical_flares is not None and not df_historical_flares.empty:
        flares = df_historical_flares.copy()
        flares["begin_time"] = pd.to_datetime(flares["begin_time"], utc=True)
        flares = flares.sort_values("begin_time").reset_index(drop=True)

        m_times = flares[flares["is_m_plus"]]["begin_time"].values
        x_times = flares[flares["is_x_plus"]]["begin_time"].values
        ts_values = df["timestamp"].values

        delta_6h = np.timedelta64(6, 'h')
        delta_24h = np.timedelta64(24, 'h')
        delta_7d = np.timedelta64(7 * 24, 'h')

        for i, t in enumerate(ts_values):
            # STRICT PAST ONLY: flare_begin_time <= t
            past_m = m_times[m_times <= t]
            if len(past_m) > 0:
                m_flares_6h[i] = np.sum(past_m >= (t - delta_6h))
                m_flares_24h[i] = np.sum(past_m >= (t - delta_24h))
                m_flares_7d[i] = np.sum(past_m >= (t - delta_7d))
                last_m = past_m[-1]
                since_m_hours[i] = min(168.0, (t - last_m) / np.timedelta64(1, 'h'))

            past_x = x_times[x_times <= t]
            if len(past_x) > 0:
                x_flares_24h[i] = np.sum(past_x >= (t - delta_24h))
                last_x = past_x[-1]
                since_x_hours[i] = min(720.0, (t - last_x) / np.timedelta64(1, 'h'))

    df["m_flares_prev_6h"] = m_flares_6h
    df["m_flares_prev_24h"] = m_flares_24h
    df["m_flares_prev_7d"] = m_flares_7d
    df["x_flares_prev_24h"] = x_flares_24h
    df["hours_since_last_m_flare"] = since_m_hours
    df["hours_since_last_x_flare"] = since_x_hours

    # Fill any remaining NaNs in numeric features with finite defaults
    for col in FEATURE_NAMES:
        if col in df.columns:
            df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    return df

def generate_eda_figures(df: pd.DataFrame, df_flares: pd.DataFrame, figures_dir: str):
    """
    Generates 9 scientific EDA figures examining solar activity, flare distributions,
    feature correlation matrix, and pre-flare dynamics.
    """
    logger.info("Generating 9 Scientific EDA Visualizations...")

    # Figure 1: Historical Solar X-Ray Flux
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    ax.semilogy(df["timestamp"], df["long_flux"], color='#f59e0b', lw=0.9, label="GOES-16/18 Long Flux (0.1-0.8nm)")
    ax.axhline(1e-4, color='#ef4444', ls='--', alpha=0.8, label="X-Class Threshold (1e-4 W/m²)")
    ax.axhline(1e-5, color='#f97316', ls='--', alpha=0.8, label="M-Class Threshold (1e-5 W/m²)")
    ax.axhline(1e-6, color='#eab308', ls=':', alpha=0.6, label="C-Class Threshold (1e-6 W/m²)")
    ax.set_title("Figure 1: Chronological Solar X-Ray Flux Telemetry", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_ylabel("Flux (W/m²)", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, which="both", color='#1e293b', alpha=0.4)
    ax.legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', loc='upper right')
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eda_historical_flux.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # Figure 2: Flare Class Distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    if not df_flares.empty:
        counts = df_flares["class_category"].value_counts()
        colors = {'X': '#ef4444', 'M': '#f97316', 'C': '#eab308', 'B': '#38bdf8'}
        b_colors = [colors.get(c, '#64748b') for c in counts.index]
        bars = ax.bar(counts.index, counts.values, color=b_colors, width=0.5, edgecolor='#000000')
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f'{h}', xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points", ha='center', color='#f8fafc', fontweight='bold')
    ax.set_title("Figure 2: Solar Flare Events by Class Category", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_ylabel("Recorded Events", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, axis='y', color='#1e293b', alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eda_flare_classes.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # Figure 3: M/X Flare Occurrence Over Time
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    if not df_flares.empty:
        mx_flares = df_flares[df_flares["is_m_plus"]]
        ax.scatter(mx_flares["begin_time"], mx_flares["peak_flux"], c='#ef4444', s=16, alpha=0.7, label="M/X Flares")
        ax.set_yscale("log")
    ax.set_title("Figure 3: Temporal Occurrence of Strong Flares (M & X Class)", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_ylabel("Peak Flux (W/m²)", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, which="both", color='#1e293b', alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eda_flare_timeline.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # Figure 4: X-Ray Flux Distribution & Log Distribution
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor('#060913')
    ax1.set_facecolor('#0d1224')
    ax2.set_facecolor('#0d1224')
    ax1.hist(df["long_flux"], bins=50, color='#f59e0b', edgecolor='#000000', alpha=0.8)
    ax1.set_title("Linear Flux Distribution", color='#f8fafc', fontsize=11)
    ax1.set_xlabel("W/m²", color='#94a3b8')
    ax1.tick_params(colors='#94a3b8')
    ax2.hist(df["log_long_flux"], bins=50, color='#38bdf8', edgecolor='#000000', alpha=0.8)
    ax2.set_title("Log10 Flux Distribution", color='#f8fafc', fontsize=11)
    ax2.set_xlabel("log10(W/m²)", color='#94a3b8')
    ax2.tick_params(colors='#94a3b8')
    fig.suptitle("Figure 4: Solar X-Ray Flux Probability Densities", color='#f8fafc', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eda_flux_distribution.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # Figure 5: Feature Correlation Matrix
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    key_feats = ["long_flux", "log_long_flux", "flux_ratio", "max_flux_6h", "mean_flux_24h", "std_flux_24h", "m_flares_prev_24h", "target_m_plus"]
    corr = df[key_feats].corr()
    cax = ax.matshow(corr, cmap="inferno", vmin=-0.3, vmax=1.0)
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xticks(range(len(key_feats)))
    ax.set_yticks(range(len(key_feats)))
    ax.set_xticklabels(key_feats, rotation=45, ha="left", color='#94a3b8', fontsize=9)
    ax.set_yticklabels(key_feats, color='#94a3b8', fontsize=9)
    ax.set_title("Figure 5: Feature Correlation Matrix", color='#f8fafc', fontsize=12, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eda_feature_correlation.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # Figure 6 & 7: Pre-flare dynamics (Average flux profile leading up to M-events)
    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    # Positive target vs negative target mean rolling flux
    pos = df[df["target_m_plus"] == 1]["max_flux_6h"]
    neg = df[df["target_m_plus"] == 0]["max_flux_6h"]
    ax.boxplot([neg.dropna(), pos.dropna()], labels=["Quiet Sun (0)", "Pre-M+ Flare (1)"], patch_artist=True,
               boxprops=dict(facecolor='#1e293b', color='#38bdf8'),
               medianprops=dict(color='#f59e0b', lw=2))
    ax.set_yscale("log")
    ax.set_title("Figure 6: 6h Max Flux in Quiet vs Pre-M+ Windows", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_ylabel("Flux (W/m²)", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, which="both", color='#1e293b', alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eda_preflare_m_flux.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # Figure 7: Pre-flare dynamics for X-class events
    fig, ax = plt.subplots(figsize=(9, 4))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    pos_x = df[df["target_x_plus"] == 1]["max_flux_24h"]
    neg_x = df[df["target_x_plus"] == 0]["max_flux_24h"]
    ax.boxplot([neg_x.dropna(), pos_x.dropna()], labels=["Non-X Window (0)", "Pre-X Flare Window (1)"], patch_artist=True,
               boxprops=dict(facecolor='#1e293b', color='#ef4444'),
               medianprops=dict(color='#f59e0b', lw=2))
    ax.set_yscale("log")
    ax.set_title("Figure 7: 24h Max Flux in Non-X vs Pre-X Windows", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_ylabel("Flux (W/m²)", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, which="both", color='#1e293b', alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eda_preflare_x_flux.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # Figure 8: Target Class Balance (Positive vs Negative)
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    t_counts = df["target_m_plus"].value_counts()
    ax.bar(["No Flare (0)", "M+ Flare in 24h (1)"], t_counts.values, color=['#3b82f6', '#ef4444'], width=0.4, edgecolor='#000000')
    for i, v in enumerate(t_counts.values):
        ax.text(i, v + 50, f"{v} ({v/len(df)*100:.1f}%)", ha='center', color='#f8fafc', fontweight='bold')
    ax.set_title("Figure 8: 24-Hour Forecast Target Distribution", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_ylabel("Sample Count", color='#94a3b8')
    ax.tick_params(colors='#94a3b8')
    ax.grid(True, axis='y', color='#1e293b', alpha=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eda_target_balance.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    # Figure 9: Data Coverage Visualization
    fig, ax = plt.subplots(figsize=(12, 3))
    fig.patch.set_facecolor('#060913')
    ax.set_facecolor('#0d1224')
    for s, c in [('train', '#3b82f6'), ('val', '#f59e0b'), ('test', '#10b981'), ('PURGED_EMBARGO', '#ef4444')]:
        sub = df[df["split"] == s]
        if not sub.empty:
            ax.plot(sub["timestamp"], np.ones(len(sub)), label=s.upper(), color=c, lw=6)
    ax.set_title("Figure 9: Chronological Train / Val / Test & 24h Embargo Coverage", color='#f8fafc', fontsize=12, fontweight='bold')
    ax.set_yticks([])
    ax.tick_params(colors='#94a3b8')
    ax.legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', loc='center right')
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "eda_data_coverage.png"), dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)

    logger.info("All 9 EDA figures saved successfully.")

def build_features():
    logger.info("Building Arkastra Feature Engineering Dataset...")
    dataset_path = os.path.join(PROCESSED_DIR, "solar_forecasting_dataset.parquet")
    donki_path = os.path.join(RAW_DIR, "donki_flares_raw.json")

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Processed dataset {dataset_path} not found. Run Phase 3 first.")

    df_base = pd.read_parquet(dataset_path)
    df_flares = pd.read_json(donki_path) if os.path.exists(donki_path) else pd.DataFrame()

    # Compute astrophysics features
    df_features = compute_solar_features(df_base, df_flares)

    # Save feature schema
    feature_schema = {
        "version": "1.0.0",
        "created_at_utc": datetime.utcnow().isoformat() + "Z",
        "feature_count": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "target_col": "target_m_plus",
        "target_x_col": "target_x_plus",
        "split_col": "split",
        "timestamp_col": "timestamp"
    }

    schema_path = os.path.join(PROCESSED_DIR, "feature_schema.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(feature_schema, f, indent=2)
    logger.info(f"Saved feature schema to {schema_path}")

    # Save feature matrix
    output_features_path = os.path.join(PROCESSED_DIR, "features.parquet")
    df_features.to_parquet(output_features_path, index=False)
    logger.info(f"Saved engineered features to {output_features_path} ({len(df_features)} rows x {len(FEATURE_NAMES)} features)")

    # Generate 9 EDA figures
    generate_eda_figures(df_features, df_flares, FIGURES_DIR)

    logger.info("==================================================")
    logger.info("PHASE 4 FEATURE ENGINEERING COMPLETED")
    logger.info(f"Total Features: {len(FEATURE_NAMES)}")
    logger.info(f"Dataset Size: {df_features.shape}")
    logger.info("==================================================")
    return df_features, feature_schema

if __name__ == "__main__":
    from typing import Optional
    logging.basicConfig(level=logging.INFO)
    build_features()
