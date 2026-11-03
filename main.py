import math
import os
import sys
from pathlib import Path

import numpy as np


# Locate the model during development and in the packaged application.
RESOURCE_DIR = Path(__file__).resolve().parent
MODEL_PATH = RESOURCE_DIR / "face_landmarker.task"

# Choose a writable directory for session logs.
if getattr(sys, "frozen", False):
    PROJECT_DIR = (
        Path(
            os.environ.get(
                "LOCALAPPDATA",
                str(Path.home())
            )
        )
        / "Wachsam"
        / "logs"
    )
else:
    PROJECT_DIR = RESOURCE_DIR



# Eye-closure thresholds.
EYE_THRESHOLD = 0.20
ALERT_SECONDS = 1.0

# Neutral head-pose calibration settings.
CALIBRATION_SECONDS = 2.0
MIN_CALIBRATION_SAMPLES = 20
MAX_CALIBRATION_SPREAD = 5.0

# Experimental head-pose limits for eye measurement.
# Passing these limits does not guarantee that both eyes are visible.
MAX_EYE_PITCH = 15.0
MAX_EYE_YAW = 20.0
MAX_EYE_ROLL = 15.0

# Reset the closure timer after an interruption in frame processing.
MAX_FRAME_GAP = 0.5

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


def get_rotation(matrix):
    """Extract a proper rotation from the facial transformation matrix."""
    matrix = np.asarray(matrix, dtype=float)

    if matrix.ndim != 2:
        return None

    if matrix.shape[0] < 3 or matrix.shape[1] < 3:
        return None

    raw = matrix[:3, :3]

    if not np.isfinite(raw).all():
        return None

    try:
        u, _, vt = np.linalg.svd(raw)
    except np.linalg.LinAlgError:
        return None

    correction = np.eye(3)
    correction[2, 2] = np.linalg.det(u @ vt)

    return u @ correction @ vt


def get_angles(rotation):
    """Return estimated pitch, yaw and roll in degrees."""
    pitch = math.atan2(
        rotation[2, 1],
        rotation[2, 2]
    )

    yaw = math.atan2(
        -rotation[2, 0],
        math.hypot(
            rotation[0, 0],
            rotation[1, 0]
        )
    )

    roll = math.atan2(
        rotation[1, 0],
        rotation[0, 0]
    )

    return tuple(
        math.degrees(value)
        for value in (pitch, yaw, roll)
    )


def rotation_distance(first, second):
    """Return the angular distance between two rotation matrices."""
    relative = first @ second.T

    cosine = (
        np.trace(relative) - 1.0
    ) / 2.0

    return math.degrees(
        math.acos(
            float(np.clip(cosine, -1.0, 1.0))
        )
    )


def pose_within_eye_limits(angles):
    """Check whether estimated angles are inside the experimental limits."""
    if angles is None:
        return False

    pitch, yaw, roll = angles

    if not all(
        math.isfinite(value)
        for value in (pitch, yaw, roll)
    ):
        return False

    return (
        abs(pitch) <= MAX_EYE_PITCH
        and abs(yaw) <= MAX_EYE_YAW
        and abs(roll) <= MAX_EYE_ROLL
    )


def eye_ratio(face, indices, width, height):
    """Calculate the eye aspect ratio from six facial landmarks."""
    points = np.array([
        (
            face[index].x * width,
            face[index].y * height
        )
        for index in indices
    ], dtype=float)

    if not np.isfinite(points).all():
        return None

    # Reject non-finite points or points outside the image.
    if (
        (points[:, 0] < 0).any()
        or (points[:, 0] >= width).any()
        or (points[:, 1] < 0).any()
        or (points[:, 1] >= height).any()
    ):
        return None

    horizontal = math.dist(
        points[0],
        points[3]
    )

    # Reject eye geometry with insufficient horizontal resolution.
    if horizontal < 8:
        return None

    vertical_1 = math.dist(
        points[1],
        points[5]
    )

    vertical_2 = math.dist(
        points[2],
        points[4]
    )

    ratio = (
        vertical_1 + vertical_2
    ) / (2 * horizontal)

    # Apply a preliminary geometry check; this is not a visibility score.
    if not 0 <= ratio <= 0.8:
        return None

    return ratio



def update_eye_closure(now, left, right, measurement_valid, closed_since):
    """Update the closure timer; unavailable measurements always reset it.

    The caller must also reset closed_since after a frame-processing gap.
    This function uses EAR values, not a verified eye-visibility estimate.
    """
    if not measurement_valid or left is None or right is None:
        return None, 0.0, False
    if not all(math.isfinite(value) for value in (now, left, right)):
        return None, 0.0, False
    if left >= EYE_THRESHOLD or right >= EYE_THRESHOLD:
        return None, 0.0, False
    if closed_since is None or now < closed_since:
        closed_since = now
    duration = now - closed_since
    return closed_since, duration, duration >= ALERT_SECONDS


def csv_number(value):
    """Leave unavailable measurements empty in CSV output."""
    if value is None:
        return ""

    return round(float(value), 4)


def display_number(value):
    """Format an estimated head angle for the interface."""
    if value is None:
        return "--"

    return f"{value:+.1f}"


def display_ear(value):
    """Format an EAR measurement for the interface."""
    if value is None:
        return "--"

    return f"{value:.3f}"


if __name__ == "__main__":
    print("Start the interface with: python app.py")