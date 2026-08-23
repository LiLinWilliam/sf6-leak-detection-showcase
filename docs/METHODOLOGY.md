# Methodology

This document explains the **public demonstration methodology only**. It is not a description of any private implementation and should not be interpreted as a patent specification, production algorithm, or safety procedure.

## 1. Synthetic scenarios

The demo generates four fictional device traces over 45 days:

| Scenario | Purpose |
|---|---|
| `DEMO-STABLE` | Stable baseline with ordinary noise |
| `DEMO-NOISY` | Higher measurement noise without meaningful decline |
| `DEMO-WATCH` | Mild persistent decline |
| `DEMO-DECLINE` | Stronger persistent decline |

All names, values, and timestamps are artificial.

## 2. Data imperfections

A small number of missing samples and isolated spikes are injected deliberately. This makes the example closer to a real data-engineering task than a perfectly clean toy dataset.

The public baseline then:

1. interpolates sparse missing measurements;
2. estimates a robust scale using median absolute deviation;
3. clips isolated extremes conservatively.

## 3. Environmental normalization

For each fictional device, the demo estimates a simple linear relationship between temperature and pressure. Measurements are then expressed relative to a fixed reference temperature.

This is an intentionally generic statistical example. It does **not** claim to represent the full thermodynamic behavior of SF₆ equipment and does not reproduce any private correction model.

## 4. Temporal smoothing

A centered rolling median reduces the influence of short-lived fluctuations while preserving gradual changes. The demo focuses on persistent behavior rather than single-point threshold crossings.

## 5. Explainable features

Three simple device-level features are calculated:

- **trend** — fitted change in normalized pressure per day;
- **baseline drop** — difference between an early-period median and a recent-period median;
- **recent volatility** — standard deviation in the recent period.

## 6. Demonstration score

The public script combines the three features with a logistic function to produce an illustrative score between 0 and 1.

The weights and category boundaries are selected solely so the synthetic scenarios are easy to inspect. They are **not validated alarm thresholds**, are not intended for field use, and are not derived from protected implementation parameters.

## 7. What a production project would add

Depending on the application, a real engagement could include:

- formal sensor and schema validation;
- domain-specific normalization and calibration;
- labeled-event strategy and leakage ground truth;
- time-based train/validation/test splits;
- leakage and anomaly models with calibrated probabilities;
- uncertainty estimation;
- false-alarm cost analysis;
- drift and data-quality monitoring;
- explainability reports;
- deployment APIs or scheduled batch pipelines;
- operational review with qualified engineering personnel.

The purpose of this repository is to show the ability to structure that kind of data problem without publishing confidential R&D.
