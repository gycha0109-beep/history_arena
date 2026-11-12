from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from author_mocap_composite import (
    ANKLE_CLEARANCE_DEGREES,
    ANKLE_WINDOW,
    clearance,
    quat_mul,
    slerp,
)


class AuthoredGaitTests(unittest.TestCase):
    def test_clearance_window_zero_at_edges(self) -> None:
        start, end = ANKLE_WINDOW
        self.assertEqual(0.0, clearance(start))
        self.assertEqual(0.0, clearance(end))
        self.assertEqual(0.0, clearance(start - .05))
        self.assertEqual(0.0, clearance(end + .05))

    def test_clearance_peaks_at_mid_swing(self) -> None:
        start, end = ANKLE_WINDOW
        self.assertAlmostEqual(1.0, clearance((start + end) / 2.0), places=6)
        self.assertGreater(ANKLE_CLEARANCE_DEGREES, 0)
        self.assertLessEqual(ANKLE_CLEARANCE_DEGREES, 30)

    def test_quaternion_interpolation_is_normalized(self) -> None:
        identity = [0.0, 0.0, 0.0, 1.0]
        turn = [0.0, math.sin(math.pi/4), 0.0, math.cos(math.pi/4)]
        for i in range(11):
            q = slerp(identity, turn, float(i) / 10.0)
            self.assertAlmostEqual(sum(value*value for value in q), 1.0, places=6)

    def test_quaternion_multiplication_identity(self) -> None:
        q = [0.21, -0.41, 0.22, 0.86]
        self.assertEqual(quat_mul([0,0,0,1], q), q)


if __name__ == "__main__":
    unittest.main()
