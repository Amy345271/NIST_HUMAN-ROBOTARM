#!/usr/bin/env python3
"""Build a time-synchronized archive HDF5 in a layout closer to the reference image.

This script stores raw streams at the root level and keeps a shared `/timestamps`
group with time axes for each modality.

Compared with `run_multisensor_pipeline.py`, this format is closer to an archive:
- sensor tables live at root groups such as `/wrist`, `/robot_state`, `/eye`, `/force`
- audio/video metadata live at root groups such as `/audio_people`, `/cam1`
- `/timestamps/<name>` stores each stream's time axis

It does not write segment-level indices. Use `align_segments.py` for the
annotation-driven alignment format.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from import_audio import read_audio_info
from import_video import probe_video_metadata
from import_sensor_csv import (
    SENSOR_SCHEMAS,
    build_records_dataset,
    ensure_columns,
    extract_timestamps,
    promote_first_row_to_header_if_needed,
    read_csv_with_fallback,
)

try:
    import soundfile as sf
except Exception:
    sf = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a time-synchronized archive HDF5")
    parser.add_argument("--basename", required=True, help="Recording basename, e.g. 2")
    parser.add_argument("--h5", default=None, help="Target HDF5 file; defaults to data/<basename>_timesync.h5")
    parser.add_argument("--data-root", default="data", help="Root folder containing sensor/audio/video files")
    parser.add_argument("--video-root", default=None, help="Directory containing <basename>_camX.mp4 files")
    parser.add_argument("--skip-audio", action="store_true", help="Skip audio streams")
    parser.add_argument("--skip-videos", action="store_true", help="Skip video streams")
    parser.add_argument("--video-frame-rate", type=float, default=None, help="Frame rate used to generate timestamps")
    parser.add_argument("--video-num-frames", type=int, default=None, help="Number of video frames")
    parser.add_argument("--video-start-time", type=float, default=0.0, help="Timestamp of the first video frame")
    parser.add_argument(
        "--cameras",
        nargs="*",
        default=("cam1", "cam2", "cam3"),
        help="Which cameras to archive",
    )
    return parser.parse_args()


def sensor_path(data_root: str, sensor: str, basename: str) -> str | None:
    if sensor == "force":
        candidates = [
            os.path.join(data_root, sensor, f"{basename}_force.xlsx"),
            os.path.join(data_root, sensor, f"{basename}_force.xlsm"),
            os.path.join(data_root, sensor, f"{basename}_force.xls"),
            os.path.join(data_root, sensor, f"{basename}_force.csv"),
        ]
    else:
        suffix = {
            "wrist": "_wrist.csv",
            "robot": "_rtde.csv",
            "eye": "_eyetracker.csv",
        }[sensor]
        candidates = [os.path.join(data_root, sensor, f"{basename}{suffix}")]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def store_table_stream(
    h5_file: h5py.File,
    root_timestamps: h5py.Group,
    stream_name: str,
    df: pd.DataFrame,
    time_col: str,
    keep_cols: list[str],
    source_path: str,
    time_scale: float,
) -> None:
    df = promote_first_row_to_header_if_needed(df, [time_col, *keep_cols])
    ensure_columns(df, [time_col, *keep_cols], source_path)

    timestamps = extract_timestamps(df, "robot" if stream_name == "robot_state" else stream_name, time_col, time_scale)
    records, field_map = build_records_dataset(df, keep_cols)

    group = h5_file.require_group(stream_name)
    if "timestamps" in group:
        del group["timestamps"]
    if "records" in group:
        del group["records"]
    group.create_dataset("timestamps", data=timestamps, dtype="f8")
    group.create_dataset("records", data=records)
    group.attrs["source_path"] = os.path.abspath(source_path)
    group.attrs["time_col"] = time_col
    group.attrs["time_scale"] = float(time_scale)
    group.attrs["field_map"] = str(field_map)

    if stream_name in root_timestamps:
        del root_timestamps[stream_name]
    root_timestamps[stream_name] = group["timestamps"]


def store_audio_stream(
    h5_file: h5py.File,
    root_timestamps: h5py.Group,
    stream_name: str,
    audio_path: str,
) -> None:
    if sf is not None:
        info = sf.info(audio_path)
        sample_rate = int(info.samplerate)
        num_samples = int(info.frames)
    else:
        import wave

        with wave.open(audio_path, "rb") as wf:
            sample_rate = int(wf.getframerate())
            num_samples = int(wf.getnframes())

    group = h5_file.require_group(stream_name)
    group.attrs["source_path"] = os.path.abspath(audio_path)
    group.attrs["sample_rate"] = sample_rate
    group.attrs["num_samples"] = num_samples

    if "audio_path" in group:
        del group["audio_path"]
    group.create_dataset("audio_path", data=os.path.abspath(audio_path), dtype=h5py.string_dtype(encoding="utf-8"))

    timestamps = np.arange(num_samples, dtype=np.float64) / float(sample_rate)
    if "timestamps" in group:
        del group["timestamps"]
    group.create_dataset("timestamps", data=timestamps, dtype="f8")

    if stream_name in root_timestamps:
        del root_timestamps[stream_name]
    root_timestamps[stream_name] = group["timestamps"]


def store_video_stream(
    h5_file: h5py.File,
    root_timestamps: h5py.Group,
    stream_name: str,
    video_path: str,
    frame_rate: float | None,
    num_frames: int | None,
    start_time: float,
) -> None:
    if frame_rate is None or num_frames is None:
        probed_frame_rate, probed_num_frames = probe_video_metadata(video_path)
        frame_rate = frame_rate or probed_frame_rate
        num_frames = num_frames or probed_num_frames

    group = h5_file.require_group(stream_name)
    group.attrs["source_path"] = os.path.abspath(video_path)
    group.attrs["start_time"] = float(start_time)

    if "video_path" in group:
        del group["video_path"]
    group.create_dataset("video_path", data=os.path.abspath(video_path), dtype=h5py.string_dtype(encoding="utf-8"))

    group.attrs["frame_rate"] = float(frame_rate)
    group.attrs["num_frames"] = int(num_frames)

    timestamps = start_time + np.arange(num_frames, dtype=np.float64) / float(frame_rate)
    if "timestamps" in group:
        del group["timestamps"]
    group.create_dataset("timestamps", data=timestamps, dtype="f8")

    if stream_name in root_timestamps:
        del root_timestamps[stream_name]
    root_timestamps[stream_name] = group["timestamps"]


def main() -> None:
    args = parse_args()
    h5_path = args.h5 or os.path.join(args.data_root, f"{args.basename}_timesync.h5")
    video_root = args.video_root or os.path.join(args.data_root, "videos")

    sensor_map = {
        "wrist": ("wrist", SENSOR_SCHEMAS["wrist"].time_col, list(SENSOR_SCHEMAS["wrist"].keep_cols), 1.0),
        "robot": ("robot_state", SENSOR_SCHEMAS["robot"].time_col, list(SENSOR_SCHEMAS["robot"].keep_cols), 1.0),
        "eye": ("eye", SENSOR_SCHEMAS["eye"].time_col, list(SENSOR_SCHEMAS["eye"].keep_cols), 1.0),
        "force": ("force", SENSOR_SCHEMAS["force"].time_col, list(SENSOR_SCHEMAS["force"].keep_cols), 0.001),
    }

    with h5py.File(h5_path, "a") as h5_file:
        root_timestamps = h5_file.require_group("timestamps")

        for sensor_name, (group_name, time_col, keep_cols, time_scale) in sensor_map.items():
            source_path = sensor_path(args.data_root, sensor_name, args.basename)
            if not source_path:
                print(f"[skip] missing {sensor_name}")
                continue

            df = read_csv_with_fallback(source_path)
            store_table_stream(h5_file, root_timestamps, group_name, df, time_col, keep_cols, source_path, time_scale)
            print(f"[run] archived {sensor_name}: {source_path}")

        if not args.skip_audio:
            for kind in ("audio_people", "audio_environment"):
                audio_path = os.path.join(args.data_root, kind, f"{args.basename}.wav")
                if not os.path.exists(audio_path):
                    print(f"[skip] missing {kind}")
                    continue
                store_audio_stream(h5_file, root_timestamps, kind, audio_path)
                print(f"[run] archived {kind}: {audio_path}")

        if not args.skip_videos:
            for camera in args.cameras:
                video_path = os.path.join(video_root, f"{args.basename}_{camera}.mp4")
                if not os.path.exists(video_path):
                    print(f"[skip] missing {camera}")
                    continue
                store_video_stream(
                    h5_file,
                    root_timestamps,
                    camera,
                    video_path,
                    args.video_frame_rate,
                    args.video_num_frames,
                    args.video_start_time,
                )
                print(f"[run] archived {camera}: {video_path}")

        h5_file.attrs["layout"] = "time_sync_archive"
        h5_file.attrs["basename"] = args.basename

    print(f"Time-sync archive complete: {h5_path}")


if __name__ == "__main__":
    main()