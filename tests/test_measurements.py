"""Synthetic regression tests; these do not validate real-world drowsiness detection."""
import math
import unittest
from types import SimpleNamespace

import numpy as np
import main as detector


class MeasurementTests(unittest.TestCase):
    def eye(self, ear):
        # 100 px eye width and symmetric vertical distances.
        coordinates = [(100, 100), (125, 100 - 50 * ear),
                       (175, 100 - 50 * ear), (200, 100),
                       (175, 100 + 50 * ear), (125, 100 + 50 * ear)]
        return [SimpleNamespace(x=x / 640, y=y / 480) for x, y in coordinates]

    def test_open_eye_geometry(self):
        self.assertAlmostEqual(detector.eye_ratio(self.eye(.3), range(6), 640, 480), .3)

    def test_closed_eye_geometry(self):
        self.assertAlmostEqual(detector.eye_ratio(self.eye(.1), range(6), 640, 480), .1)

    def test_outside_image_is_unavailable(self):
        face = self.eye(.3)
        face[0].x = -1
        self.assertIsNone(detector.eye_ratio(face, range(6), 640, 480))

    def test_nonfinite_eye_is_unavailable(self):
        face = self.eye(.3)
        face[1].y = float('nan')
        self.assertIsNone(detector.eye_ratio(face, range(6), 640, 480))

    def test_degenerate_eye_is_unavailable(self):
        face = self.eye(.3)
        face[3].x = face[0].x
        self.assertIsNone(detector.eye_ratio(face, range(6), 640, 480))

    def test_identity_rotation(self):
        np.testing.assert_allclose(detector.get_rotation(np.eye(4)), np.eye(3))
        self.assertEqual(detector.get_angles(np.eye(3)), (0, 0, 0))

    def test_scaled_rotation_projection(self):
        np.testing.assert_allclose(detector.get_rotation(np.diag([2., 3., 4., 1.])), np.eye(3))

    def test_reflection_is_not_returned(self):
        result = detector.get_rotation(np.diag([-1., 1., 1., 1.]))
        self.assertAlmostEqual(np.linalg.det(result), 1)

    def test_invalid_rotation(self):
        self.assertIsNone(detector.get_rotation([[float('nan')] * 3] * 3))
        self.assertIsNone(detector.get_rotation([1, 2, 3]))

    def test_yaw_rotation_and_distance(self):
        a = math.radians(30)
        rotation = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        self.assertAlmostEqual(detector.get_angles(rotation)[1], 30)
        self.assertAlmostEqual(detector.rotation_distance(rotation, np.eye(3)), 30)

    def test_pose_limits_and_nonfinite_angles(self):
        self.assertTrue(detector.pose_within_eye_limits((15, 20, 15)))
        self.assertFalse(detector.pose_within_eye_limits((15.01, 0, 0)))
        self.assertFalse(detector.pose_within_eye_limits((0, -20.01, 0)))
        self.assertFalse(detector.pose_within_eye_limits((0, 0, float('nan'))))

    def test_short_closure_does_not_alert(self):
        since, _, _ = detector.update_eye_closure(10, .1, .1, True, None)
        _, duration, alert = detector.update_eye_closure(10.2, .1, .1, True, since)
        self.assertAlmostEqual(duration, .2)
        self.assertFalse(alert)

    def test_alarm_at_one_second(self):
        since, _, _ = detector.update_eye_closure(10, .1, .1, True, None)
        _, duration, alert = detector.update_eye_closure(11, .1, .1, True, since)
        self.assertEqual(duration, 1)
        self.assertTrue(alert)

    def test_open_eye_resets_timer(self):
        self.assertEqual(detector.update_eye_closure(11, .3, .1, True, 10), (None, 0, False))

    def test_threshold_equality_is_not_closed(self):
        self.assertEqual(detector.update_eye_closure(11, .2, .1, True, 10), (None, 0, False))

    def test_invalid_pose_resets_even_for_low_ear(self):
        self.assertEqual(detector.update_eye_closure(12, .1, .1, False, 10), (None, 0, False))

    def test_missing_and_nonfinite_ear_reset(self):
        self.assertEqual(detector.update_eye_closure(12, None, .1, True, 10), (None, 0, False))
        self.assertEqual(detector.update_eye_closure(12, float('nan'), .1, True, 10), (None, 0, False))

    def test_reset_does_not_accumulate_old_closure(self):
        # The worker passes None after a frame gap or camera-read failure.
        _, duration, alert = detector.update_eye_closure(20, .1, .1, True, None)
        self.assertEqual(duration, 0)
        self.assertFalse(alert)


if __name__ == '__main__':
    unittest.main()
