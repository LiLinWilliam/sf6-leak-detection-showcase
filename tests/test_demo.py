"""Behavior checks for the public synthetic demo.

These tests validate only the independently written public showcase baseline.
They do not encode production thresholds or private research behavior.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
if str(EXAMPLES) not in sys.path:
    sys.path.insert(0, str(EXAMPLES))

import synthetic_demo  # noqa: E402


class SyntheticDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, cls.summary = synthetic_demo.run_demo()
        cls.by_device = cls.summary.set_index("device_id")

    def test_expected_statuses(self) -> None:
        self.assertEqual(
            self.by_device.loc["DEMO-STABLE", "demo_status"],
            "low-demo-risk",
        )
        self.assertEqual(
            self.by_device.loc["DEMO-NOISY", "demo_status"],
            "low-demo-risk",
        )
        self.assertEqual(
            self.by_device.loc["DEMO-WATCH", "demo_status"],
            "review",
        )
        self.assertEqual(
            self.by_device.loc["DEMO-DECLINE", "demo_status"],
            "high-demo-risk",
        )

    def test_persistent_decline_ranks_above_noise(self) -> None:
        decline = float(
            self.by_device.loc["DEMO-DECLINE", "demo_risk_score"]
        )
        watch = float(self.by_device.loc["DEMO-WATCH", "demo_risk_score"])
        noisy = float(self.by_device.loc["DEMO-NOISY", "demo_risk_score"])
        stable = float(self.by_device.loc["DEMO-STABLE", "demo_risk_score"])

        self.assertGreater(decline, watch)
        self.assertGreater(watch, noisy)
        self.assertGreater(noisy, stable)

    def test_scores_are_probabilistic_range(self) -> None:
        scores = self.summary["demo_risk_score"]
        self.assertTrue(((scores >= 0.0) & (scores <= 1.0)).all())


if __name__ == "__main__":
    unittest.main()
