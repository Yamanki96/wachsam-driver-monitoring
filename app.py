import csv
import queue
import threading
import time
import tkinter as tk
import winsound
from datetime import datetime
from tkinter import messagebox

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageTk

import main as detector


BG = "#05070A"
PANEL = "#0C121C"
BORDER = "#193453"
WHITE = "#FFFFFF"
LIGHT_BLUE = "#79C7FF"
BLUE = "#1769E8"
FONT = "Segoe UI"


class WachsamApp:
    def __init__(self, root):
        self.root = root
        root.title("WACHSAM")
        root.configure(bg=BG)

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = min(1100, screen_width - 60)
        height = min(720, screen_height - 100)
        root.geometry(f"{width}x{height}")
        root.minsize(800, 560)

        self.worker = None
        self.stop_event = threading.Event()
        self.calibrate_event = threading.Event()
        self.sound_lock = threading.Lock()

        self.updates = queue.Queue(maxsize=1)
        self.events = queue.Queue()
        self.photo = None
        self.closing = False
        self.was_running = False

        self.build_interface()
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(100, self.poll)

    def make_label(self, parent, text, size=12, bold=False):
        return tk.Label(
            parent,
            text=text,
            font=(FONT, size, "bold" if bold else "normal"),
            bg=PANEL,
            fg=WHITE,
            wraplength=340,
            justify="center"
        )

    def make_button(self, parent, text, command, primary=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=(FONT, 10, "bold"),
            bg=BLUE if primary else PANEL,
            fg=WHITE,
            activebackground=BLUE,
            activeforeground=WHITE,
            disabledforeground="#57799B",
            relief="flat",
            padx=15,
            pady=12,
            cursor="hand2"
        )

    def build_interface(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = tk.Frame(self.root, bg=BG)
        header.grid(
            row=0, column=0, sticky="ew",
            padx=24, pady=(16, 10)
        )

        tk.Label(
            header,
            text="W A C H S A M",
            font=(FONT, 23, "bold"),
            bg=BG,
            fg=WHITE
        ).pack(side="left")

        tk.Label(
            header,
            text="DRIVER MONITORING",
            font=(FONT, 10),
            bg=BG,
            fg=LIGHT_BLUE
        ).pack(side="right")

        content = tk.Frame(self.root, bg=BG)
        content.grid(
            row=1, column=0, sticky="nsew",
            padx=24, pady=8
        )
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=1, uniform="cards")
        content.columnconfigure(1, weight=1, uniform="cards")

        self.card = tk.Frame(
            content,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.card.grid(
            row=0, column=0, sticky="nsew", padx=(0, 8)
        )

        # Keep card contents from expanding the window layout.
        self.card.grid_propagate(False)
        self.card.columnconfigure(0, weight=1)
        self.card.rowconfigure(1, weight=1)

        heading = self.make_label(
            self.card, "FAHRERASSISTENZ", 10, True
        )
        heading.config(fg=LIGHT_BLUE)
        heading.grid(row=0, column=0, pady=(20, 5))

        status_area = tk.Frame(self.card, bg=PANEL)
        status_area.grid(row=1, column=0, sticky="nsew")
        status_area.columnconfigure(0, weight=1)
        status_area.rowconfigure(0, weight=1)
        status_area.rowconfigure(4, weight=1)

        self.symbol = self.make_label(status_area, "◎", 48)
        self.symbol.config(fg=LIGHT_BLUE)
        self.symbol.grid(row=1, column=0, pady=5)

        self.title = self.make_label(
            status_area, "Bereit", 23, True
        )
        self.title.grid(row=2, column=0, padx=12, pady=10)

        self.description = self.make_label(
            status_area, "Starten Sie die Überwachung.", 12
        )
        self.description.config(fg=LIGHT_BLUE)
        self.description.grid(
            row=3, column=0, padx=16, pady=10
        )

        video_card = tk.Frame(
            content,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        video_card.grid(
            row=0, column=1, sticky="nsew", padx=(8, 0)
        )
        video_card.grid_propagate(False)
        video_card.columnconfigure(0, weight=1)
        video_card.rowconfigure(1, weight=1)

        heading = self.make_label(
            video_card, "LIVE-KAMERA", 10, True
        )
        heading.config(fg=LIGHT_BLUE)
        heading.grid(row=0, column=0, pady=20)

        self.video = tk.Label(
            video_card,
            text="Kamera ausgeschaltet",
            bg=PANEL,
            fg=LIGHT_BLUE,
            font=(FONT, 12),
            width=1,
            height=1
        )
        self.video.grid(
            row=1, column=0, sticky="nsew",
            padx=12, pady=(0, 12)
        )

        # Keep controls outside the resizable camera area.
        footer = tk.Frame(self.root, bg=BG)
        footer.grid(
            row=2, column=0, sticky="ew",
            padx=20, pady=(8, 12)
        )

        self.metrics = tk.Label(
            footer,
            text="EAR L: --   |   EAR R: --   |   Augenschluss: --",
            font=(FONT, 10),
            bg=BG,
            fg=LIGHT_BLUE
        )
        self.metrics.pack(pady=4)

        self.pose = tk.Label(
            footer,
            text="Kopfposition: --",
            font=(FONT, 10),
            bg=BG,
            fg=LIGHT_BLUE
        )
        self.pose.pack(pady=2)

        controls = tk.Frame(footer, bg=BG)
        controls.pack(pady=12)

        self.start_button = self.make_button(
            controls, "STARTEN", self.start, True
        )
        self.start_button.pack(side="left", padx=5)

        self.calibrate_button = self.make_button(
            controls, "KALIBRIEREN", self.calibrate
        )
        self.calibrate_button.pack(side="left", padx=5)

        self.stop_button = self.make_button(
            controls, "STOPPEN", self.stop
        )
        self.stop_button.pack(side="left", padx=5)

        self.sound_button = self.make_button(
            controls, "TON TESTEN", self.play_sound
        )
        self.sound_button.pack(side="left", padx=5)

        self.calibrate_button.config(state="disabled")
        self.stop_button.config(state="disabled")

        self.file_text = tk.Label(
            footer,
            text="Experimenteller Prototyp · Keine Videoaufzeichnung",
            font=(FONT, 9),
            bg=BG,
            fg=LIGHT_BLUE,
            wraplength=760
        )
        self.file_text.pack(pady=3)

    def play_sound(self):
        if not self.sound_lock.acquire(blocking=False):
            return

        def sound_worker():
            try:
                winsound.Beep(1200, 180)
                winsound.Beep(1500, 180)
            except Exception as error:
                self.events.put(("sound_error", str(error)))
            finally:
                self.sound_lock.release()

        threading.Thread(
            target=sound_worker, daemon=True
        ).start()

    def start(self):
        if self.worker and self.worker.is_alive():
            return

        self.stop_event.clear()
        self.calibrate_event.clear()

        while True:
            try:
                self.updates.get_nowait()
            except queue.Empty:
                break

        while True:
            try:
                self.events.get_nowait()
            except queue.Empty:
                break

        self.start_button.config(state="disabled")
        self.calibrate_button.config(state="normal")
        self.stop_button.config(state="normal")

        self.title.config(text="Kamera startet")
        self.description.config(text="Bitte kurz warten.")
        self.file_text.config(text="Neue Sitzung wird gestartet ...")

        self.worker = threading.Thread(
            target=self.monitor, daemon=True
        )
        self.was_running = True
        self.worker.start()

    def calibrate(self):
        self.calibrate_event.set()

    def stop(self):
        self.stop_event.set()
        self.calibrate_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        self.title.config(text="Wird beendet")
        self.description.config(text="Kamera wird freigegeben.")

    def close(self):
        self.closing = True
        self.stop()

    def publish(self, data):
        try:
            self.updates.get_nowait()
        except queue.Empty:
            pass

        try:
            self.updates.put_nowait(data)
        except queue.Full:
            pass

    def render(self, data):
        state = data["state"]

        if state == "ALERT":
            title = "Längerer Augenschluss"
            detail = (
                "Mögliche Anzeichen von Müdigkeit.\n"
                "An einem sicheren Ort anhalten "
                "und eine Pause machen."
            )
            symbol = "!"
        elif state == "OPEN":
            title = "Überwachung aktiv"
            detail = (
                "Augen als offen gemessen.\n"
                "Keine Bestätigung der Fahrtüchtigkeit."
            )
            symbol = "◎"
        elif state == "CLOSED":
            title = "Augen geschlossen"
            detail = "Die Schließdauer wird gemessen."
            symbol = "◎"
        elif state == "CALIBRATING":
            title = "Kalibrierung"
            detail = data["notice"]
            symbol = "◎"
        elif state == "NOT_CALIBRATED":
            title = "Bitte kalibrieren"
            detail = (
                "Gerade zur Kamera schauen.\n"
                "Dann KALIBRIEREN drücken."
            )
            symbol = "◎"
        elif state == "NO_FACE":
            title = "Gesicht nicht erkannt"
            detail = "Bitte zur Kamera schauen."
            symbol = "—"
        elif state == "CAMERA_READ_FAILED":
            title = "Kein Kamerabild"
            detail = "Die Verbindung wird geprüft."
            symbol = "—"
        else:
            title = "Messung nicht verfügbar"
            detail = (
                "Augenmessung wegen Kopfposition "
                "oder Bildqualität nicht zuverlässig."
            )
            symbol = "—"

        self.title.config(text=title)
        self.description.config(text=detail)
        self.symbol.config(text=symbol)

        self.card.config(
            highlightbackground=LIGHT_BLUE if state == "ALERT" else BORDER,
            highlightthickness=3 if state == "ALERT" else 1
        )

        self.metrics.config(text=(
            f"EAR L: {detector.display_ear(data['left'])}   |   "
            f"EAR R: {detector.display_ear(data['right'])}   |   "
            f"Augenschluss: {data['duration']:.1f} s"
        ))

        pitch, yaw, roll = data["angles"]
        self.pose.config(text=(
            f"Pitch: {detector.display_number(pitch)}°   |   "
            f"Yaw: {detector.display_number(yaw)}°   |   "
            f"Roll: {detector.display_number(roll)}°"
        ))

        frame = data.get("frame")
        if frame is None and state == "CAMERA_READ_FAILED":
            self.video.config(image="", text="Kamerabild nicht verfügbar")
            self.photo = None
        if frame is not None:
            image = Image.fromarray(
                cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            )

            # Fit the image to the available area without expanding the widget.
            width = max(1, min(480, self.video.winfo_width()))
            height = max(1, min(320, self.video.winfo_height()))
            image.thumbnail((width, height))

            self.photo = ImageTk.PhotoImage(image)
            self.video.config(image=self.photo, text="")

    def poll(self):
        try:
            data = self.updates.get_nowait()
        except queue.Empty:
            data = None

        if data is not None and not self.stop_event.is_set():
            self.render(data)

        while True:
            try:
                kind, value = self.events.get_nowait()
            except queue.Empty:
                break

            if kind == "finished":
                self.file_text.config(text=f"Messdatei: {value}")
            elif kind == "error":
                self.title.config(text="Überwachung nicht verfügbar")
                self.description.config(text=value)
                if not self.closing:
                    messagebox.showerror("Wachsam", value)
            elif kind == "sound_error" and not self.closing:
                messagebox.showerror("Ton nicht verfügbar", value)

        running = self.worker is not None and self.worker.is_alive()

        if self.was_running and not running:
            self.was_running = False
            self.start_button.config(state="normal")
            self.calibrate_button.config(state="disabled")
            self.stop_button.config(state="disabled")

            if self.stop_event.is_set():
                self.title.config(text="Überwachung beendet")
                self.description.config(text="Kamera ausgeschaltet.")
                self.symbol.config(text="◎")

            self.video.config(image="", text="Kamera ausgeschaltet")
            self.photo = None
            self.card.config(
                highlightbackground=BORDER,
                highlightthickness=1
            )

        if self.closing and not running:
            self.root.destroy()
            return

        self.root.after(100, self.poll)

    def monitor(self):
        camera = None
        log_path = None
        log_created = False

        try:
            detector.PROJECT_DIR.mkdir(parents=True, exist_ok=True)
            log_path = detector.PROJECT_DIR / (
                f"app_log_{datetime.now():%Y%m%d_%H%M%S_%f}.csv"
            )
            if not detector.MODEL_PATH.is_file():
                raise FileNotFoundError(
                    "face_landmarker.task fehlt im Projektordner."
                )

            options = mp.tasks.vision.FaceLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(
                    model_asset_path=str(detector.MODEL_PATH)
                ),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_faces=1,
                output_facial_transformation_matrixes=True
            )

            camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not camera.isOpened():
                raise RuntimeError(
                    "Kamera konnte nicht geöffnet werden. "
                    "Andere Kamera-Programme schließen."
                )

            neutral = None
            calibrating = False
            samples = []
            calibration_started = None
            calibration_id = 0
            closed_since = None
            previous_time = None
            last_timestamp = -1
            last_sound = float("-inf")
            started = time.monotonic()
            last_flush = started
            failed_reads = 0

            fields = [
                "elapsed_seconds",
                "left_ear", "right_ear", "average_ear",
                "closed_seconds", "status", "alert_active",
                "pitch_deg", "yaw_deg", "roll_deg",
                "raw_pitch_deg", "raw_yaw_deg", "raw_roll_deg",
                "calibration_id", "eye_threshold", "alert_seconds",
                "max_eye_pitch", "max_eye_yaw", "max_eye_roll"
            ]

            with log_path.open(
                "w", newline="", encoding="utf-8"
            ) as log_file:
                writer = csv.DictWriter(
                    log_file, fieldnames=fields
                )
                writer.writeheader()
                log_file.flush()
                log_created = True

                with mp.tasks.vision.FaceLandmarker.create_from_options(
                    options
                ) as model:
                    while not self.stop_event.is_set():
                        if self.calibrate_event.is_set():
                            self.calibrate_event.clear()
                            neutral = None
                            calibrating = True
                            samples.clear()
                            calibration_started = None
                            closed_since = None

                        success, frame = camera.read()
                        now = time.monotonic()

                        if not success or frame is None:
                            closed_since = None
                            previous_time = None
                            samples.clear()
                            calibration_started = None
                            failed_reads += 1

                            writer.writerow({
                                "elapsed_seconds": round(now - started, 3),
                                "status": "CAMERA_READ_FAILED",
                                "closed_seconds": 0,
                                "alert_active": 0
                            })
                            log_file.flush()

                            self.publish({
                                "state": "CAMERA_READ_FAILED",
                                "notice": "",
                                "left": None,
                                "right": None,
                                "duration": 0,
                                "angles": (None, None, None),
                                "frame": None
                            })

                            if failed_reads >= 20:
                                raise RuntimeError(
                                    "Kein Kamerabild verfügbar."
                                )

                            self.stop_event.wait(0.1)
                            continue

                        failed_reads = 0
                        timestamp = max(
                            time.monotonic_ns() // 1_000_000,
                            last_timestamp + 1
                        )
                        last_timestamp = timestamp

                        image = mp.Image(
                            image_format=mp.ImageFormat.SRGB,
                            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        )
                        result = model.detect_for_video(image, timestamp)
                        now = time.monotonic()

                        gap = (
                            previous_time is not None
                            and now - previous_time > detector.MAX_FRAME_GAP
                        )
                        previous_time = now

                        if gap:
                            closed_since = None
                            samples.clear()
                            calibration_started = None

                        face = (
                            result.face_landmarks[0]
                            if result.face_landmarks else None
                        )
                        rotation = None

                        if (
                            face is not None
                            and len(result.facial_transformation_matrixes) > 0
                        ):
                            rotation = detector.get_rotation(
                                result.facial_transformation_matrixes[0]
                            )

                        raw_angles = (
                            detector.get_angles(rotation)
                            if rotation is not None else None
                        )
                        notice = "Gerade schauen und ruhig halten."

                        if calibrating:
                            if rotation is None or gap:
                                samples.clear()
                                calibration_started = None
                                notice = (
                                    "Messung unterbrochen. "
                                    "Bitte gerade zur Kamera schauen."
                                )
                            else:
                                if calibration_started is None:
                                    calibration_started = now

                                samples.append(rotation.copy())
                                progress = now - calibration_started
                                notice = (
                                    f"Kopf ruhig halten: "
                                    f"{min(progress, detector.CALIBRATION_SECONDS):.1f}"
                                    f"/{detector.CALIBRATION_SECONDS:.1f} s"
                                )

                                if (
                                    progress >= detector.CALIBRATION_SECONDS
                                    and len(samples)
                                    >= detector.MIN_CALIBRATION_SAMPLES
                                ):
                                    candidate = detector.get_rotation(
                                        np.mean(samples, axis=0)
                                    )

                                    if candidate is not None:
                                        spread = max(
                                            detector.rotation_distance(
                                                sample, candidate
                                            )
                                            for sample in samples
                                        )
                                        frontal = detector.pose_within_eye_limits(
                                            detector.get_angles(candidate)
                                        )

                                        if (
                                            frontal
                                            and spread
                                            <= detector.MAX_CALIBRATION_SPREAD
                                        ):
                                            neutral = candidate
                                            calibration_id += 1
                                            calibrating = False
                                        else:
                                            notice = (
                                                "Neuer Versuch: gerade "
                                                "schauen und ruhig halten."
                                            )
                                    else:
                                        notice = (
                                            "Kalibrierung fehlgeschlagen. "
                                            "Neuer Versuch."
                                        )

                                    samples.clear()
                                    calibration_started = None

                        angles = None
                        if (
                            not calibrating
                            and neutral is not None
                            and rotation is not None
                        ):
                            angles = detector.get_angles(
                                rotation @ neutral.T
                            )

                        left = right = average = None
                        if face is not None:
                            height, width = frame.shape[:2]
                            left = detector.eye_ratio(
                                face, detector.LEFT_EYE, width, height
                            )
                            right = detector.eye_ratio(
                                face, detector.RIGHT_EYE, width, height
                            )
                            if left is not None and right is not None:
                                average = (left + right) / 2

                        pose_ok = (
                            raw_angles is not None
                            and angles is not None
                            and detector.pose_within_eye_limits(raw_angles)
                            and detector.pose_within_eye_limits(angles)
                        )

                        if face is None:
                            state = "NO_FACE"
                        elif calibrating:
                            state = "CALIBRATING"
                        elif neutral is None:
                            state = "NOT_CALIBRATED"
                        elif rotation is None:
                            state = "HEAD_UNAVAILABLE"
                        elif not pose_ok:
                            state = "EYE_MEASUREMENT_UNCERTAIN_HEAD_POSE"
                        elif left is None or right is None:
                            state = "EYE_GEOMETRY_UNAVAILABLE"
                        else:
                            state = "OPEN"

                        closed_since, duration, alert = detector.update_eye_closure(
                            now, left, right,
                            measurement_valid=(state == "OPEN"),
                            closed_since=closed_since
                        )
                        if state == "OPEN" and closed_since is not None:
                            state = "ALERT" if alert else "CLOSED"

                        if (
                            alert
                            and now - last_sound >= 1.0
                            and not self.stop_event.is_set()
                        ):
                            self.play_sound()
                            last_sound = now

                        pitch, yaw, roll = (
                            angles if angles is not None
                            else (None, None, None)
                        )
                        raw_pitch, raw_yaw, raw_roll = (
                            raw_angles if raw_angles is not None
                            else (None, None, None)
                        )

                        writer.writerow({
                            "elapsed_seconds": round(now - started, 3),
                            "left_ear": detector.csv_number(left),
                            "right_ear": detector.csv_number(right),
                            "average_ear": detector.csv_number(average),
                            "closed_seconds": round(duration, 3),
                            "status": state,
                            "alert_active": int(alert),
                            "pitch_deg": detector.csv_number(pitch),
                            "yaw_deg": detector.csv_number(yaw),
                            "roll_deg": detector.csv_number(roll),
                            "raw_pitch_deg": detector.csv_number(raw_pitch),
                            "raw_yaw_deg": detector.csv_number(raw_yaw),
                            "raw_roll_deg": detector.csv_number(raw_roll),
                            "calibration_id": calibration_id,
                            "eye_threshold": detector.EYE_THRESHOLD,
                            "alert_seconds": detector.ALERT_SECONDS,
                            "max_eye_pitch": detector.MAX_EYE_PITCH,
                            "max_eye_yaw": detector.MAX_EYE_YAW,
                            "max_eye_roll": detector.MAX_EYE_ROLL
                        })

                        if now - last_flush >= 1.0:
                            log_file.flush()
                            last_flush = now

                        self.publish({
                            "state": state,
                            "notice": notice,
                            "left": left,
                            "right": right,
                            "duration": duration,
                            "angles": (pitch, yaw, roll),
                            "frame": frame.copy()
                        })

        except Exception as error:
            self.events.put(("error", str(error)))

        finally:
            if camera is not None:
                camera.release()
            self.events.put((
                "finished",
                str(log_path) if log_created else "Keine Messdatei erstellt."
            ))


if __name__ == "__main__":
    root = tk.Tk()
    app = WachsamApp(root)
    root.mainloop()