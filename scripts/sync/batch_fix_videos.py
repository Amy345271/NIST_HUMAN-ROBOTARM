#!/usr/bin/env python3
"""Batch re-register video metadata for all existing data/*.h5 files.

For each data/<basename>.h5 found, this script calls import_video.py with
`--timestamps` for each camera in ('cam1','cam2','cam3'), letting the
importer probe the MP4 files and write correct `frame_rate`/`num_frames`
(and per-frame timestamps) into the HDF5.
"""

from __future__ import annotations

import glob
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = Path(__file__).resolve().parent
IMPORT_VIDEO = SCRIPTS_DIR / "import_video.py"
DATA_DIR = ROOT / "data"
VIDEOS_DIR = DATA_DIR / "videos"
CAMERAS = ("cam1", "cam2", "cam3")
PYTHON = sys.executable


def find_h5_basenames() -> list[str]:
    paths = sorted(glob.glob(str(DATA_DIR / "*.h5")))
    return [os.path.splitext(os.path.basename(p))[0] for p in paths]


def run_for_basename(basename: str) -> dict:
    h5_path = str(DATA_DIR / f"{basename}.h5")
    results = {cam: {"rc": None, "cmd": None} for cam in CAMERAS}

    for cam in CAMERAS:
        cmd = [
            PYTHON,
            str(IMPORT_VIDEO),
            "--basename",
            basename,
            "--camera",
            cam,
            "--h5",
            h5_path,
            "--video-root",
            str(VIDEOS_DIR),
            "--timestamps",
        ]
        results[cam]["cmd"] = cmd
        print(f"[run] {basename} {cam}")
        proc = subprocess.run(cmd, check=False)
        results[cam]["rc"] = proc.returncode
        if proc.returncode != 0:
            print(f"[error] {basename} {cam} -> exit {proc.returncode}")
    return results


def main() -> None:
    basenames = find_h5_basenames()
    if not basenames:
        print("No data/*.h5 files found; nothing to do.")
        return

    summary = {}
    for b in basenames:
        summary[b] = run_for_basename(b)

    # Print brief report
    print("\nBatch complete. Summary:")
    for b, cams in summary.items():
        statuses = {cam: (cams[cam]["rc"] == 0) for cam in cams}
        print(f" {b}: {statuses}")


if __name__ == "__main__":
    main()
