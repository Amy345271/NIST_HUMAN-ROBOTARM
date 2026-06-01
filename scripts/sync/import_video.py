#!/usr/bin/env python3
"""Register a video file using the current directory naming convention.

Expected layout:
- `data/videos/<basename>_cam1.mp4`
- `data/videos/<basename>_cam2.mp4`
- `data/videos/<basename>_cam3.mp4`

The script stores the video path and, when enough metadata is provided, writes
frame timestamps so the synchronization step can align video frames directly.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import h5py
import numpy as np
import cv2


def probe_video_metadata(video_path: str) -> tuple[float, int]:
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise SystemExit(f"Unable to open video file: {video_path}")

    frame_rate = float(capture.get(cv2.CAP_PROP_FPS))
    num_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()

    if frame_rate <= 0:
        raise SystemExit(f"Could not determine frame rate for: {video_path}")
    if num_frames <= 0:
        raise SystemExit(f"Could not determine frame count for: {video_path}")

    return frame_rate, num_frames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a video into HDF5")
    parser.add_argument("--h5", required=True, help="Target HDF5 file")
    parser.add_argument("--video", default=None, help="Explicit MP4 path; overrides basename/camera resolution")
    parser.add_argument("--basename", default=None, help="Recording basename used with --camera")
    parser.add_argument(
        "--camera",
        choices=("cam1", "cam2", "cam3"),
        default="cam1",
        help="Which video camera to use when --video is not provided",
    )
    parser.add_argument(
        "--video-root",
        default="data/videos",
        help="Root directory containing <basename>_camX.mp4 files",
    )
    parser.add_argument(
        "--sensor",
        default=None,
        help="Sensor group name under /sensors/ (defaults to the camera name)",
    )
    parser.add_argument("--frame-rate", type=float, default=None, help="Frame rate in Hz")
    parser.add_argument("--num-frames", type=int, default=None, help="Number of frames")
    parser.add_argument(
        "--start-time",
        type=float,
        default=0.0,
        help="Starting timestamp in seconds for the first frame",
    )
    parser.add_argument(
        "--timestamps",
        action="store_true",
        help="Write per-frame timestamps (requires --frame-rate and --num-frames if --video has no metadata)",
    )
    return parser.parse_args()


def resolve_video_path(args: argparse.Namespace) -> tuple[str, str]:
    if args.video:
        path = args.video
        sensor_name = args.sensor or Path(path).stem.rsplit("_", 1)[-1]
        return path, sensor_name

    if not args.basename:
        raise SystemExit("Provide either --video or --basename")

    sensor_name = args.sensor or args.camera
    path = os.path.join(args.video_root, f"{args.basename}_{args.camera}.mp4")
    return path, sensor_name


def main() -> None:
    args = parse_args()
    video_path, sensor_name = resolve_video_path(args)
    video_path = os.path.abspath(video_path)

    if not os.path.exists(video_path):
        raise SystemExit(f"Video file not found: {video_path}")

    frame_rate = args.frame_rate
    num_frames = args.num_frames
    # If timestamps requested, always probe the video metadata and prefer the
    # probed values. If the user explicitly provided values that disagree with
    # the probed metadata, warn and prefer the probed metadata to avoid silent
    # mismatches where HDF5 stores incorrect durations.
    if args.timestamps:
        probed_frame_rate, probed_num_frames = probe_video_metadata(video_path)
        if frame_rate is None and num_frames is None:
            frame_rate = probed_frame_rate
            num_frames = probed_num_frames
        else:
            # User provided values; compare and warn if they differ substantially.
            try:
                if frame_rate is not None and abs(float(frame_rate) - probed_frame_rate) / max(1.0, probed_frame_rate) > 0.01:
                    print(f"[warn] provided --frame-rate={frame_rate} differs from probed={probed_frame_rate}; using probed value")
                    frame_rate = probed_frame_rate
            except Exception:
                frame_rate = probed_frame_rate
            try:
                if num_frames is not None and abs(int(num_frames) - probed_num_frames) > max(5, 0.05 * probed_num_frames):
                    print(f"[warn] provided --num-frames={num_frames} differs from probed={probed_num_frames}; using probed value")
                    num_frames = probed_num_frames
            except Exception:
                num_frames = probed_num_frames

    write_timestamps = args.timestamps and frame_rate is not None and num_frames is not None
    if args.timestamps and not write_timestamps:
        raise SystemExit("--timestamps requires a readable video file or explicit --frame-rate and --num-frames")

    with h5py.File(args.h5, "a") as h5_file:
        sensors_group = h5_file.require_group("sensors")
        sensor_group = sensors_group.require_group(sensor_name)

        if "video_path" in sensor_group:
            del sensor_group["video_path"]
        sensor_group.create_dataset(
            "video_path",
            data=video_path,
            dtype=h5py.string_dtype(encoding="utf-8"),
        )
        sensor_group.attrs["source_path"] = video_path
        sensor_group.attrs["camera"] = sensor_name
        sensor_group.attrs["start_time"] = float(args.start_time)

        if frame_rate is not None:
            sensor_group.attrs["frame_rate"] = float(frame_rate)
        if num_frames is not None:
            sensor_group.attrs["num_frames"] = int(num_frames)

        if write_timestamps:
            timestamps = args.start_time + np.arange(num_frames, dtype=np.float64) / float(frame_rate)
            if "timestamps" in sensor_group:
                del sensor_group["timestamps"]
            sensor_group.create_dataset("timestamps", data=timestamps, dtype="f8")

    print(
        f"Registered {sensor_name}: path={video_path}, frame_rate={frame_rate}, num_frames={num_frames}"
    )


if __name__ == '__main__':
    main()
