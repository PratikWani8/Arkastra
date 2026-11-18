"""
Unit tests for target generation, future window boundaries, and chronological splitting.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from training.build_dataset import generate_targets_for_timeline, apply_chronological_splits

def test_target_generation_logic():
    # Construct synthetic timeline spanning 48 hours
    base_time = pd.to_datetime("2024-01-01T00:00:00Z")
    timestamps = [base_time + pd.Timedelta(hours=i) for i in range(48)]
    df_timeline = pd.DataFrame({"timestamp": timestamps, "long_flux": 1e-6})

    # Flare occurs at hour 10 (M2.0)
    flare_time = base_time + pd.Timedelta(hours=10)
    df_flares = pd.DataFrame([
        {
            "event_id": "FLR_001",
            "begin_time": flare_time,
            "peak_time": flare_time + pd.Timedelta(minutes=15),
            "flare_class": "M2.0",
            "class_category": "M",
            "peak_flux": 2e-5,
            "is_m_plus": True,
            "is_x_plus": False
        }
    ])

    df_labeled = generate_targets_for_timeline(df_timeline, df_flares, horizon_hours=24)

    # For an observation at hour 0, the flare is at hour 10 in (0, 24] -> target_m_plus must be 1
    t0 = df_labeled[df_labeled["timestamp"] == base_time]
    assert t0["target_m_plus"].iloc[0] == 1
    assert t0["future_m_flare_count"].iloc[0] == 1
    assert t0["hours_to_next_m_flare"].iloc[0] == pytest.approx(10.0)

    # For an observation at hour 11, the flare is at hour 10 (which is in the past) -> target_m_plus must be 0
    t11 = df_labeled[df_labeled["timestamp"] == (base_time + pd.Timedelta(hours=11))]
    assert t11["target_m_plus"].iloc[0] == 0
    assert np.isnan(t11["hours_to_next_m_flare"].iloc[0])

def test_chronological_embargo_isolation():
    # Verify train, val, and test splits have 24-hour temporal separation
    base_time = pd.to_datetime("2024-01-01T00:00:00Z")
    timestamps = [base_time + pd.Timedelta(hours=i) for i in range(200)]
    df = pd.DataFrame({
        "timestamp": timestamps,
        "target_m_plus": np.random.randint(0, 2, 200),
        "target_x_plus": np.zeros(200)
    })

    df_split, meta = apply_chronological_splits(df, train_pct=0.70, val_pct=0.15, test_pct=0.15, embargo_hours=24)
    
    train_max = df_split[df_split["split"] == "train"]["timestamp"].max()
    val_min = df_split[df_split["split"] == "val"]["timestamp"].min()
    val_max = df_split[df_split["split"] == "val"]["timestamp"].max()
    test_min = df_split[df_split["split"] == "test"]["timestamp"].min()

    # Verify 24h gap between train max and val min
    gap_train_val = (val_min - train_max).total_seconds() / 3600.0
    assert gap_train_val >= 24.0

    # Verify 24h gap between val max and test min
    gap_val_test = (test_min - val_max).total_seconds() / 3600.0
    assert gap_val_test >= 24.0
