import csv
import math
import time
from datetime import datetime
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

FOLDER = Path(__file__).parent
MODEL_PATH = FOLDER / "face_landmarker.task"
LOG_PATH = FOLDER / (
    f"head_log_{datetime.now():%Y%m%d_%H%M%S_%f}.csv"
)

CALIBRATION_SECONDS = 2.0
MIN_CALIBRATION_SAMPLES = 20

# Experimental calibration rejection limit for excessive head movement.
MAX_CALIBRATION_SPREAD = 5.0


def get_rotation(matrix):
    raw = np.asarray(matrix, dtype=float)[:3, :3]

    if raw.shape != (3, 3) or not np.isfinite(raw).all():
        return None

    u, _, vt = np.linalg.svd(raw)
    correction = np.eye(3)
    correction[2, 2] = np.linalg.det(u @ vt)

    return u @ correction @ vt


def average_rotation(rotations):
    return get_rotation(np.mean(rotations, axis=0))


def rotation_distance(first, second):
    relative = first @ second.T
    cosine = (np.trace(relative) - 1.0) / 2.0
    return math.degrees(
        math.acos(float(np.clip(cosine, -1.0, 1.0)))
    )


def get_angles(rotation):
    pitch = math.atan2(rotation[2, 1], rotation[2, 2])
    yaw = math.atan2(
        -rotation[2, 0],
        math.hypot(rotation[0, 0], rotation[1, 0])
    )
    roll = math.atan2(rotation[1, 0], rotation[0, 0])

    return tuple(
        math.degrees(angle)
        for angle in (pitch, yaw, roll)
    )


def log_number(value):
    return "" if value is None else round(value, 3)


options = mp.tasks.vision.FaceLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(
        model_asset_path=str(MODEL_PATH)
    ),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_faces=1,
    output_facial_transformation_matrixes=True
)

labels = {
    ord("0"): "UNLABELED",
    ord("1"): "STRAIGHT",
    ord("2"): "DOWN",
    ord("3"): "TURN_LEFT",
    ord("4"): "TURN_RIGHT",
    ord("5"): "TILT"
}

neutral_rotation = None
calibration_id = 0
calibrating = False
calibration_started = None
calibration_samples = []

last_timestamp = -1
previous_frame_time = None
started_at = time.monotonic()
label = "UNLABELED"
notice = "Look straight, then press C"

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

try:
    if not camera.isOpened():
        raise RuntimeError(
            "Could not open camera. Close other camera apps."
        )

    with LOG_PATH.open(
        "w", newline="", encoding="utf-8"
    ) as log_file:
        writer = csv.writer(log_file)
        writer.writerow([
            "elapsed_seconds",
            "pitch_deg",
            "yaw_deg",
            "roll_deg",
            "face_detected",
            "calibrated",
            "calibration_id",
            "user_label",
            "tracking_status",
            "calibrating"
        ])

        print(f"Recording to: {LOG_PATH}")

        with mp.tasks.vision.FaceLandmarker.create_from_options(
            options
        ) as model:
            while True:
                success, frame = camera.read()

                if not success or frame is None:
                    print("Could not read camera image.")
                    break

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb
                )

                timestamp = max(
                    time.monotonic_ns() // 1_000_000,
                    last_timestamp + 1
                )
                last_timestamp = timestamp

                result = model.detect_for_video(image, timestamp)

                now = time.monotonic()
                elapsed = now - started_at
                frame_gap = (
                    previous_frame_time is not None
                    and now - previous_frame_time > 0.5
                )
                previous_frame_time = now

                rotation = None
                pitch = yaw = roll = None
                face_detected = bool(result.face_landmarks)

                if (
                    face_detected
                    and len(result.facial_transformation_matrixes) > 0
                ):
                    rotation = get_rotation(
                        result.facial_transformation_matrixes[0]
                    )

                if calibrating:
                    if rotation is None or frame_gap:
                        calibration_samples.clear()
                        calibration_started = None
                        notice = "Tracking interrupted - hold still"
                    else:
                        if calibration_started is None:
                            calibration_started = now

                        calibration_samples.append(rotation.copy())
                        progress = now - calibration_started
                        notice = (
                            f"Hold straight: "
                            f"{min(progress, CALIBRATION_SECONDS):.1f}"
                            f"/{CALIBRATION_SECONDS:.1f}s"
                        )

                        if (
                            progress >= CALIBRATION_SECONDS
                            and len(calibration_samples)
                            >= MIN_CALIBRATION_SAMPLES
                        ):
                            candidate = average_rotation(
                                calibration_samples
                            )
                            spread = max(
                                rotation_distance(sample, candidate)
                                for sample in calibration_samples
                            )

                            if spread <= MAX_CALIBRATION_SPREAD:
                                neutral_rotation = candidate
                                calibration_id += 1
                                calibrating = False
                                label = "UNLABELED"
                                notice = "Calibration OK - select a label"
                                print(
                                    f"Calibration {calibration_id} OK: "
                                    f"{len(calibration_samples)} samples"
                                )
                            else:
                                notice = "Too much movement - hold straight"

                            calibration_samples.clear()
                            calibration_started = None

                if not face_detected:
                    tracking_status = "NO_FACE"
                elif rotation is None:
                    tracking_status = "POSE_UNAVAILABLE"
                elif calibrating:
                    tracking_status = "CALIBRATING"
                elif neutral_rotation is None:
                    tracking_status = "NOT_CALIBRATED"
                else:
                    relative = rotation @ neutral_rotation.T
                    pitch, yaw, roll = get_angles(relative)
                    tracking_status = "TRACKING"

                if tracking_status == "TRACKING":
                    color = (0, 255, 0)
                elif tracking_status in ("NO_FACE", "POSE_UNAVAILABLE"):
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 255)

                lines = [
                    f"Status: {tracking_status}",
                    (
                        f"Pitch: {pitch:+.1f} deg"
                        if pitch is not None else "Pitch: --"
                    ),
                    (
                        f"Yaw: {yaw:+.1f} deg"
                        if yaw is not None else "Yaw: --"
                    ),
                    (
                        f"Roll: {roll:+.1f} deg"
                        if roll is not None else "Roll: --"
                    ),
                    notice,
                    f"Your label: {label}",
                    "1: Straight | 2: Down",
                    "3: Left | 4: Right | 5: Tilt",
                    "0: Transition | C: Calibrate | Q: Exit"
                ]

                # Use a dark background to keep diagnostic text readable.
                panel_bottom = min(
                    frame.shape[0], 20 + len(lines) * 28
                )
                overlay = frame.copy()
                cv2.rectangle(
                    overlay,
                    (0, 0),
                    (frame.shape[1], panel_bottom),
                    (0, 0, 0),
                    -1
                )
                frame = cv2.addWeighted(
                    overlay, 0.6, frame, 0.4, 0
                )

                for index, text in enumerate(lines):
                    cv2.putText(
                        frame,
                        text,
                        (12, 28 + index * 28),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.52,
                        color if index == 0 else (255, 255, 255),
                        1,
                        cv2.LINE_AA
                    )

                writer.writerow([
                    round(elapsed, 3),
                    log_number(pitch),
                    log_number(yaw),
                    log_number(roll),
                    int(face_detected),
                    int(neutral_rotation is not None),
                    calibration_id,
                    label,
                    tracking_status,
                    int(calibrating)
                ])

                cv2.imshow("Head tracking", frame)
                key = cv2.waitKey(1) & 0xFF

                # Accept both lowercase and uppercase shortcut keys.
                if key in (ord("q"), ord("Q")):
                    break

                if key in (ord("c"), ord("C")):
                    neutral_rotation = None
                    calibrating = True
                    calibration_started = None
                    calibration_samples.clear()
                    label = "UNLABELED"
                    notice = "Hold straight for calibration"

                elif key in labels:
                    if neutral_rotation is not None and not calibrating:
                        label = labels[key]
                    else:
                        notice = "Finish calibration before labeling"

finally:
    camera.release()
    cv2.destroyAllWindows()

print(f"Saved: {LOG_PATH}")