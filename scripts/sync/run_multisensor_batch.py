#!/usr/bin/env python3
"""Batch run the ELAN conversion and multimodal sync pipeline.

By default this discovers basenames from `annotation/eaf/*.eaf`, converts each
ELAN file into `data/<basename>.h5`, then runs the existing one-click sync
pipeline for the same basename.
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch run ELAN conversion and multimodal sync")
    parser.add_argument(
        "--basenames",
        nargs="*",
        default=None,
        help="Optional list of recording basenames; defaults to all annotation/eaf/*.eaf files",
    )
    parser.add_argument("--eaf-dir", default="annotation/eaf", help="Directory containing .eaf files")
    parser.add_argument("--data-root", default="data", help="Root directory for HDF5 and sensor files")
    parser.add_argument("--high-tier", required=True, help="High-level tier name in ELAN")
    parser.add_argument(
        "--low-tier",
        action="append",
        default=[],
        help="Low-level tier name; can be repeated",
    )
    parser.add_argument(
        "--success-labels",
        nargs="*",
        default=None,
        help="Optional labels that count as success in the high tier",
    )
    parser.add_argument("--skip-videos", action="store_true", help="Skip video import in the sync pipeline")
    parser.add_argument("--skip-audio", action="store_true", help="Skip audio import in the sync pipeline")
    parser.add_argument("--video-frame-rate", type=float, default=None, help="Frame rate for all videos")
    parser.add_argument("--video-num-frames", type=int, default=None, help="Frame count for all videos")
    parser.add_argument(
        "--cameras",
        nargs="*",
        default=("cam1", "cam2", "cam3"),
        help="Which cameras to try importing",
    )
    parser.add_argument("--continue-on-error", action="store_true", help="Keep processing remaining basenames")
    parser.add_argument("--python", default=sys.executable, help="Python executable to use")
    return parser.parse_args()


def script_path(*parts: str) -> str:
    return str(Path(__file__).resolve().parent.joinpath(*parts))


def run_step(cmd: list[str], label: str) -> None:
    print(f"[run] {label}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Step failed: {label} (exit code {result.returncode})")


def discover_basenames(eaf_dir: str) -> list[str]:
    eaf_paths = sorted(glob.glob(os.path.join(eaf_dir, "*.eaf")))
    return [os.path.splitext(os.path.basename(path))[0] for path in eaf_paths]


def main() -> None:
    args = parse_args()

    basenames = args.basenames or discover_basenames(args.eaf_dir)
    if not basenames:
        raise SystemExit(f"No basenames found in {args.eaf_dir}")

    converter = str(Path(__file__).resolve().parent.parent / "labeling" / "eaf_to_h5.py")
    pipeline = script_path("run_multisensor_pipeline.py")

    succeeded: list[str] = []
    failed: list[str] = []

    for basename in basenames:
        eaf_path = os.path.join(args.eaf_dir, f"{basename}.eaf")
        h5_path = os.path.join(args.data_root, f"{basename}.h5")

        try:
            if not os.path.exists(eaf_path):
                raise FileNotFoundError(f"EAF file not found: {eaf_path}")

            convert_cmd = [
                args.python,
                converter,
                "--eaf",
                eaf_path,
                "--h5",
                h5_path,
                "--high-tier",
                args.high_tier,
            ]
            for low_tier in args.low_tier:
                convert_cmd.extend(["--low-tier", low_tier])
            if args.success_labels is not None:
                convert_cmd.extend(["--success-labels", *args.success_labels])
            convert_cmd.append("--overwrite")

            run_step(convert_cmd, f"convert {basename}")

            sync_cmd = [
                args.python,
                pipeline,
                "--basename",
                basename,
                "--h5",
                h5_path,
                "--data-root",
                args.data_root,
            ]
            if args.skip_audio:
                sync_cmd.append("--skip-audio")
            if args.skip_videos:
                sync_cmd.append("--skip-videos")
            else:
                if args.video_frame_rate is not None:
                    sync_cmd.extend(["--video-frame-rate", str(args.video_frame_rate)])
                if args.video_num_frames is not None:
                    sync_cmd.extend(["--video-num-frames", str(args.video_num_frames)])
                sync_cmd.extend(["--cameras", *args.cameras])

            run_step(sync_cmd, f"sync {basename}")
            succeeded.append(basename)
        except Exception as exc:
            failed.append(basename)
            print(f"[fail] {basename}: {exc}")
            if not args.continue_on_error:
                raise SystemExit(1) from exc

    print(f"Batch complete. succeeded={succeeded}, failed={failed}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()