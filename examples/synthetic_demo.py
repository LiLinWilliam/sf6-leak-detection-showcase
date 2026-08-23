"""Synthetic SF6 monitoring demo.

This file is an independently written public baseline for portfolio purposes.
It does not contain private operational data, production thresholds, or code
copied from any private research repository.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


RNG_SEED = 42
REFERENCE_TEMPERATURE_C = 20.0
OUTPUT_DIR = Path("output")


def generate_device_series(
    device_id: str,
    days: int,
    samples_per_day: int,
    base_pressure: float,
    daily_decline: float,
    noise_std: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate a fictional pressure/temperature time series."""
    n = days * samples_per_day
    timestamps = pd.date_range("2026-01-01", periods=n, freq=f"{24 * 60 // samples_per_day}min")

    t = np.arange(n, dtype=float)
    day_fraction = (t % samples_per_day) / samples_per_day
    day_index = t / samples_per_day

    temperature = (
        20.0
        + 7.0 * np.sin(2.0 * np.pi * (day_fraction - 0.25))
        + 2.0 * np.sin(2.0 * np.pi * day_index / 14.0)
        + rng.normal(0.0, 0.7, n)
    )

    # A generic synthetic environmental relationship used only for demonstration.
    temperature_effect = 0.0011 * (temperature - REFERENCE_TEMPERATURE_C)
    degradation = daily_decline * day_index
    pressure = base_pressure + temperature_effect - degradation + rng.normal(0.0, noise_std, n)

    # Inject a few harmless demo imperfections: missing values and isolated spikes.
    missing_idx = rng.choice(n, size=max(1, n // 120), replace=False)
    spike_idx = rng.choice(n, size=max(1, n // 180), replace=False)
    pressure[missing_idx] = np.nan
    pressure[spike_idx] += rng.normal(0.0, 0.018, len(spike_idx))

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "device_id": device_id,
            "temperature_c": temperature,
            "pressure_mpa": pressure,
        }
    )


def build_synthetic_dataset() -> pd.DataFrame:
    """Create several fictional devices with deliberately different behaviors."""
    rng = np.random.default_rng(RNG_SEED)
    scenarios = [
        ("DEMO-STABLE", 0.610, 0.00000, 0.0015),
        ("DEMO-NOISY", 0.607, 0.00003, 0.0028),
        ("DEMO-WATCH", 0.612, 0.00022, 0.0017),
        ("DEMO-DECLINE", 0.614, 0.00055, 0.0016),
    ]

    frames = [
        generate_device_series(
            device_id=device_id,
            days=45,
            samples_per_day=24,
            base_pressure=base_pressure,
            daily_decline=daily_decline,
            noise_std=noise_std,
            rng=rng,
        )
        for device_id, base_pressure, daily_decline, noise_std in scenarios
    ]
    return pd.concat(frames, ignore_index=True)


def robust_clean_pressure(series: pd.Series) -> pd.Series:
    """Interpolate missing samples and clip isolated extremes using robust statistics."""
    x = series.astype(float).interpolate(limit_direction="both")
    median = x.median()
    mad = np.median(np.abs(x - median))
    if mad == 0 or np.isnan(mad):
        return x

    robust_sigma = 1.4826 * mad
    lower = median - 5.0 * robust_sigma
    upper = median + 5.0 * robust_sigma
    return x.clip(lower=lower, upper=upper)


def temperature_normalize(group: pd.DataFrame) -> pd.DataFrame:
    """Estimate and remove a simple linear temperature relationship per device."""
    g = group.sort_values("timestamp").copy()
    g["pressure_clean_mpa"] = robust_clean_pressure(g["pressure_mpa"])

    temp = g["temperature_c"].to_numpy()
    pressure = g["pressure_clean_mpa"].to_numpy()
    slope, intercept = np.polyfit(temp, pressure, deg=1)

    expected_at_reference = slope * REFERENCE_TEMPERATURE_C + intercept
    g["pressure_normalized_mpa"] = pressure - slope * (temp - REFERENCE_TEMPERATURE_C)
    g["environment_slope"] = slope
    g["reference_pressure_mpa"] = expected_at_reference
    g["pressure_smoothed_mpa"] = g["pressure_normalized_mpa"].rolling(
        window=24,
        min_periods=6,
        center=True,
    ).median()
    g["pressure_smoothed_mpa"] = g["pressure_smoothed_mpa"].bfill().ffill()
    return g


def score_device(group: pd.DataFrame) -> dict[str, float | str]:
    """Compute transparent illustrative features and a demo risk score."""
    g = group.sort_values("timestamp")
    y = g["pressure_smoothed_mpa"].to_numpy()
    x_days = (g["timestamp"] - g["timestamp"].iloc[0]).dt.total_seconds().to_numpy() / 86400.0

    slope_per_day, _ = np.polyfit(x_days, y, deg=1)

    baseline_n = max(24, len(g) // 8)
    recent_n = max(24, len(g) // 8)
    baseline = float(np.median(y[:baseline_n]))
    recent = float(np.median(y[-recent_n:]))
    drop_from_baseline = baseline - recent
    recent_volatility = float(np.std(y[-recent_n:]))

    # Deliberately simple public baseline. Constants are illustrative only.
    risk_logit = (
        9.0 * max(0.0, drop_from_baseline * 100.0)
        + 8.0 * max(0.0, -slope_per_day * 1000.0)
        + 1.5 * max(0.0, recent_volatility * 1000.0 - 1.0)
        - 4.0
    )
    risk_score = float(1.0 / (1.0 + np.exp(-risk_logit)))

    if risk_score >= 0.80:
        status = "high-demo-risk"
    elif risk_score >= 0.45:
        status = "review"
    else:
        status = "low-demo-risk"

    return {
        "device_id": str(g["device_id"].iloc[0]),
        "trend_mpa_per_day": float(slope_per_day),
        "drop_from_baseline_mpa": drop_from_baseline,
        "recent_volatility_mpa": recent_volatility,
        "demo_risk_score": risk_score,
        "demo_status": status,
    }


def run_demo() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the full synthetic workflow and persist inspectable CSV outputs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw = build_synthetic_dataset()
    processed = (
        raw.groupby("device_id", group_keys=False)
        .apply(temperature_normalize, include_groups=False)
        .reset_index(drop=True)
    )

    # groupby.apply with include_groups=False removes the grouping column in recent pandas;
    # restore it deterministically from the original per-device processing if needed.
    if "device_id" not in processed.columns:
        processed_frames = []
        for device_id, group in raw.groupby("device_id", sort=False):
            frame = temperature_normalize(group)
            frame["device_id"] = device_id
            processed_frames.append(frame)
        processed = pd.concat(processed_frames, ignore_index=True)

    summaries = [score_device(group) for _, group in processed.groupby("device_id")]
    summary = pd.DataFrame(summaries).sort_values("demo_risk_score", ascending=False)

    processed.to_csv(OUTPUT_DIR / "synthetic_sensor_data.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "risk_summary.csv", index=False)

    print("\nSynthetic SF6 monitoring demo")
    print("=" * 60)
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    print("\nOutputs written to:")
    print(f"- {OUTPUT_DIR / 'synthetic_sensor_data.csv'}")
    print(f"- {OUTPUT_DIR / 'risk_summary.csv'}")
    print("\nDemo only — not an operational or safety decision system.")

    return processed, summary


if __name__ == "__main__":
    run_demo()
