"""
Unit tests for ARKASTRA data collection adapters and provenance registry.
"""

import pytest
import pandas as pd
from datetime import datetime
from training.data_sources.donki_client import parse_flare_class_to_flux, DonkiClient
from training.data_sources.goes_client import GoesClient
from training.data_sources.source_registry import SourceRegistry

def test_parse_flare_class_to_flux():
    assert parse_flare_class_to_flux("M1.0") == pytest.approx(1e-5)
    assert parse_flare_class_to_flux("M5.5") == pytest.approx(5.5e-5)
    assert parse_flare_class_to_flux("X1.0") == pytest.approx(1e-4)
    assert parse_flare_class_to_flux("X2.8") == pytest.approx(2.8e-4)
    assert parse_flare_class_to_flux("C2.4") == pytest.approx(2.4e-6)
    assert parse_flare_class_to_flux("B5.0") == pytest.approx(5.0e-7)
    assert parse_flare_class_to_flux(None) is None
    assert parse_flare_class_to_flux("INVALID") is None

def test_source_registry_manifest():
    manifest = SourceRegistry.get_provenance_manifest()
    assert manifest["system"] == "Arkastra Solar Flare Probability Forecaster"
    assert "NOAA_SWPC_GOES" in manifest["registered_sources"]
    assert "NASA_DONKI" in manifest["registered_sources"]
    assert manifest["registered_sources"]["NOAA_SWPC_GOES"]["unit"] == "W/m^2"

def test_goes_normalization():
    client = GoesClient()
    sample_raw = pd.DataFrame([
        {"time_tag": "2024-05-10T12:00:00Z", "satellite": 16, "flux": 2.5e-5, "observed_flux": 2.5e-5, "energy": "0.1-0.8nm"},
        {"time_tag": "2024-05-10T12:00:00Z", "satellite": 16, "flux": 5.0e-6, "observed_flux": 5.0e-6, "energy": "0.05-0.4nm"},
    ])
    norm = client._normalize_goes_measurements(sample_raw)
    assert len(norm) == 1
    assert norm["long_flux"].iloc[0] == pytest.approx(2.5e-5)
    assert norm["short_flux"].iloc[0] == pytest.approx(5.0e-6)
    assert norm["quality_status"].iloc[0] == "GOOD"
    assert norm["flux_ratio"].iloc[0] == pytest.approx(0.2)
