#!/usr/bin/env python3
"""Run the full multimodal import + alignment workflow for one recording.

Expected layout:
- `annotation/eaf/<basename>.eaf`
- `data/<basename>.h5`
- `data/wrist/<basename>_wrist.csv`
- `data/robot/<basename>_rtde.csv`
- `data/eye/<basename>_eyetracker.csv`
- `data/force/<basename>_force.csv`
- `data/audio_people/<basename>.wav`
- `data/audio_environment/<basename>.wav`
- `data/videos/<basename>_cam1.mp4`
- `data/videos/<basename>_cam2.mp4`
- `data/videos/<basename>_cam3.mp4`

The script skips missing files and continues. After importing what is present,
it runs `align_segments.py` so that per-segment indices are written back into
`segments_info/<i>/aligned/<sensor>/indices`.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


SENSOR_FILE_EXTENSIONS = (".csv", ".xlsx", ".xlsm", ".xls")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the multimodal import + align pipeline")
    parser.add_argument("--basename", required=True, help="Recording basename, e.g. 1")
    parser.add_argument("--h5", default=None, help="Target HDF5 file; defaults to data/<basename>.h5")
    parser.add_argument(
        "--data-root",
        default="data",
        help="Root folder containing wrist/, robot/, eye/, force/, audio_people/, audio_environment/, videos/",
    )
    parser.add_argument("--video-frame-rate", type=float, default=None, help="Frame rate for all videos")
    parser.add_argument("--video-num-frames", type=int, default=None, help="Frame count for all videos")
    parser.add_argument(
        "--cameras",
        nargs="*",
        default=("cam1", "cam2", "cam3"),
        help="Which cameras to try importing",
    )
    parser.add_argument(
        "--skip-videos",
        action="store_true",
        help="Do not import video files",
    )
    parser.add_argument(
        "--skip-audio",
        action="store_true",
        help="Do not import audio files",
    )
    return parser.parse_args()


def script_path(name: str) -> str:
    return str(Path(__file__).with_name(name))


def run_step(cmd: list[str], label: str) -> None:
    print(f"[run] {label}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Step failed: {label} (exit code {result.returncode})")


def maybe_run(cmd: list[str], path: str, label: str) -> None:
    if not os.path.exists(path):
        print(f"[skip] missing {label}: {path}")
        return
    run_step(cmd, label)


def find_existing_sensor_file(folder: str, stem: str, preferred_exts: tuple[str, ...] = SENSOR_FILE_EXTENSIONS) -> str | None:
    for ext in preferred_exts:
        candidate = os.path.join(folder, stem + ext)
        if os.path.exists(candidate):
            return candidate
    return None


def main() -> None:
    args = parse_args()
    # Warn if user supplied global video frame-rate/num-frames — prefer probing
    if args.video_frame_rate is not None or args.video_num_frames is not None:
        print("[warn] You supplied --video-frame-rate/--video-num-frames. ")
        print("[warn] It's recommended to omit these and let import_video.py probe the files with --timestamps.")
        print("[warn] When --timestamps is used, import_video.py now prefers probed metadata to avoid incorrect durations.")
    h5_path = args.h5 or os.path.join(args.data_root, f"{args.basename}.h5")
    python = sys.executable

    # Sensor CSVs
    sensor_jobs = [
        (
            os.path.join(args.data_root, "wrist", f"{args.basename}_wrist.csv"),
            [python, script_path("import_sensor_csv.py"), "--csv", os.path.join(args.data_root, "wrist", f"{args.basename}_wrist.csv"), "--h5", h5_path, "--sensor", "wrist"],
            "wrist CSV",
        ),
        (
            os.path.join(args.data_root, "robot", f"{args.basename}_rtde.csv"),
            [python, script_path("import_sensor_csv.py"), "--csv", os.path.join(args.data_root, "robot", f"{args.basename}_rtde.csv"), "--h5", h5_path, "--sensor", "robot"],
            "robot CSV",
        ),
        (
            os.path.join(args.data_root, "eye", f"{args.basename}_eyetracker.csv"),
            [python, script_path("import_sensor_csv.py"), "--csv", os.path.join(args.data_root, "eye", f"{args.basename}_eyetracker.csv"), "--h5", h5_path, "--sensor", "eye"],
            "eye CSV",
        ),
        (
            find_existing_sensor_file(os.path.join(args.data_root, "force"), f"{args.basename}_force") or os.path.join(args.data_root, "force", f"{args.basename}_force.csv"),
            [python, script_path("import_sensor_csv.py"), "--csv", find_existing_sensor_file(os.path.join(args.data_root, "force"), f"{args.basename}_force") or os.path.join(args.data_root, "force", f"{args.basename}_force.csv"), "--h5", h5_path, "--sensor", "force"],
            "force CSV",
        ),
    ]
    for path, cmd, label in sensor_jobs:
        maybe_run(cmd, path, label)

    # Audio files
    if not args.skip_audio:
        audio_jobs = [
            (
                os.path.join(args.data_root, "audio_people", f"{args.basename}.wav"),
                [python, script_path("import_audio.py"), "--basename", args.basename, "--kind", "people", "--h5", h5_path, "--timestamps"],
                "audio_people",
            ),
            (
                os.path.join(args.data_root, "audio_environment", f"{args.basename}.wav"),
                [python, script_path("import_audio.py"), "--basename", args.basename, "--kind", "environment", "--h5", h5_path, "--timestamps"],
                "audio_environment",
            ),
        ]
        for path, cmd, label in audio_jobs:
            maybe_run(cmd, path, label)

    # Video files
    if not args.skip_videos:
        for camera in args.cameras:
            video_path = os.path.join(args.data_root, "videos", f"{args.basename}_{camera}.mp4")
            cmd = [
                python,
                script_path("import_video.py"),
                "--basename",
                args.basename,
                "--camera",
                camera,
                "--h5",
                h5_path,
                "--timestamps",
            ]
            if args.video_frame_rate is not None:
                cmd.extend(["--frame-rate", str(args.video_frame_rate)])
            if args.video_num_frames is not None:
                cmd.extend(["--num-frames", str(args.video_num_frames)])
            maybe_run(cmd, video_path, f"video {camera}")

    # Alignment step
    run_step([python, script_path("align_segments.py"), h5_path], "align segments")

    print(f"Pipeline complete for {args.basename}: {h5_path}")


if __name__ == "__main__":
    main()
