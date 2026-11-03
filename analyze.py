"""Plot an eye or GUI session without modifying the original CSV file."""
import argparse
import csv
from pathlib import Path

import main as detector


def load_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError("The recording has no measurement rows.")
    required = {"elapsed_seconds", "left_ear", "right_ear", "alert_active", "status"}
    if not required.issubset(rows[0]):
        raise ValueError("Expected an app_log or eye_log CSV with eye measurements.")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, help="Choose a specific session CSV.")
    parser.add_argument("--output", type=Path, help="Save the figure instead of opening a window.")
    args = parser.parse_args()

    path = args.csv
    if path is None:
        candidates = [
            path for pattern in ("app_log_*.csv", "eye_log_*.csv")
            for path in detector.PROJECT_DIR.glob(pattern)
        ]
        if not candidates:
            parser.error("No app_log or eye_log files found. Use --csv PATH.")
        path = max(candidates, key=lambda item: item.stat().st_mtime)
    try:
        rows = load_rows(path)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    import matplotlib
    if args.output:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def number(value):
        return float(value) if value else float("nan")

    seconds = [float(row["elapsed_seconds"]) for row in rows]
    figure, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    for field, label, color in (
        ("left_ear", "Eye L", "#1769E8"),
        ("right_ear", "Eye R", "#65B5E8")
    ):
        axes[0].plot(seconds, [number(row[field]) for row in rows],
                     label=label, color=color, linewidth=1)
    thresholds = {row.get("eye_threshold") for row in rows if row.get("eye_threshold")}
    if len(thresholds) == 1:
        threshold = float(next(iter(thresholds)))
        axes[0].axhline(threshold, linestyle="--", color="#555555", label=f"Threshold {threshold}")
    axes[0].set_ylabel("Raw EAR")
    axes[0].legend()
    axes[1].step(seconds, [int(row["alert_active"]) for row in rows], where="post", color="#1769E8")
    axes[1].set_yticks([0, 1], ["Off", "On"])
    axes[1].set_ylabel("Alarm")
    valid = [int(row["status"] in {"OPEN", "CLOSED", "ALERT"}) for row in rows]
    axes[2].step(seconds, valid, where="post", color="#1769E8")
    axes[2].set_yticks([0, 1], ["Unavailable", "Accepted"])
    axes[2].set_ylabel("Measurement")
    axes[2].set_xlabel("Seconds since session start")
    for axis in axes:
        axis.grid(alpha=0.2)
    figure.suptitle(path.name + " — internal measurements, not ground truth")
    figure.tight_layout()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(args.output)
        plt.close(figure)
        print(f"Saved: {args.output}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
