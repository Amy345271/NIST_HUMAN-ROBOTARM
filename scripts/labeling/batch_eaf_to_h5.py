#!/usr/bin/env python3
"""
Batch convert ELAN .eaf files from annotation/eaf into matching HDF5 files.

For each `annotation/eaf/<name>.eaf`, this script looks for `--h5-dir/<name>.h5`.
If the HDF5 file exists, it converts the annotation into `segments_info`.

This is the quickest path when you already have annotations placed in annotation/eaf.
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import h5py


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch convert EAF files to HDF5 segments_info")
    parser.add_argument("--eaf-dir", required=True, help="Directory containing .eaf files")
    parser.add_argument("--h5-dir", required=True, help="Directory containing matching .h5 files")
    parser.add_argument("--high-tier", required=True, help="High-level tier name")
    parser.add_argument("--low-tier", action="append", default=[], help="Low-level tier name; can be repeated")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing segments_info")
    parser.add_argument("--python", default=sys.executable, help="Python executable to run the converter")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    eaf_paths = sorted(glob.glob(os.path.join(args.eaf_dir, "*.eaf")))
    if not eaf_paths:
        raise SystemExit(f"No .eaf files found in {args.eaf_dir}")

    converter = os.path.join(os.path.dirname(__file__), "eaf_to_h5.py")

    converted = 0
    skipped = 0
    for eaf_path in eaf_paths:
        base_name = os.path.splitext(os.path.basename(eaf_path))[0]
        h5_path = os.path.join(args.h5_dir, base_name + ".h5")
        if not os.path.exists(h5_path):
            # create an empty HDF5 placeholder so converter can write segments_info
            try:
                with h5py.File(h5_path, 'w'):
                    pass
                print(f"[create] placeholder HDF5 created: {h5_path}")
            except Exception as exc:
                print(f"[skip] could not create HDF5: {h5_path} ({exc})")
                skipped += 1
                continue

        cmd = [
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
            cmd.extend(["--low-tier", low_tier])
        if args.overwrite:
            cmd.append("--overwrite")

        print(f"[run] {os.path.basename(eaf_path)} -> {os.path.basename(h5_path)}")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            raise SystemExit(f"Conversion failed for {eaf_path} (exit code {result.returncode})")
        converted += 1

    print(f"Done. Converted={converted}, skipped={skipped}")


if __name__ == "__main__":
    main()
