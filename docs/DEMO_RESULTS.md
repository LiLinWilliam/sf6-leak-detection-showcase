# Reproducible Demo Results

This page records the deterministic output of the public synthetic demo using the repository's fixed random seed (`42`).

The results below were recomputed from `examples/synthetic_demo.py` and are included as a reproducibility reference for reviewers.

| Synthetic device | Trend (MPa/day) | Demo risk score | Demo status |
|---|---:|---:|---|
| `DEMO-DECLINE` | -0.000542 | 0.885683 | `high-demo-risk` |
| `DEMO-WATCH` | -0.000224 | 0.336009 | `review` |
| `DEMO-NOISY` | -0.000029 | 0.090162 | `low-demo-risk` |
| `DEMO-STABLE` | -0.000002 | 0.076018 | `low-demo-risk` |

## Interpretation

The synthetic scenarios are deliberately constructed so that persistent decline ranks above ordinary noise. The public baseline therefore demonstrates a useful engineering property: a noisy-but-stable series remains low risk, while persistent degradation raises the score.

These values are **demo-only outputs**. They are not field validation metrics, safety thresholds, production alarm levels, or evidence of real-world diagnostic performance.

## How to reproduce

```bash
pip install -r requirements.txt
python examples/synthetic_demo.py
```

The script writes:

- `output/synthetic_sensor_data.csv`
- `output/risk_summary.csv`

Because the demo uses a fixed random seed, the qualitative ranking and numerical results should remain stable unless the public demo implementation changes.
