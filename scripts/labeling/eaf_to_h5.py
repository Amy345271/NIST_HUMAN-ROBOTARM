#!/usr/bin/env python3
"""
Convert ELAN .eaf annotations into the HDF5 `segments_info` structure.

High-level annotations are written as `segments_info/<index>` with:
- `index` (int)
- `start` / `end` (seconds, float)
- `success` (0/1)
- `text` (UTF-8 bytes)

Low-level annotations are written under `segments_info/<index>/low_level/<subindex>`.

ELAN uses milliseconds internally, so times are converted to seconds before writing.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

import h5py

try:
    import pympi
except Exception as exc:  # pragma: no cover - dependency error path
    raise SystemExit(
        "Missing dependency `pympi-ling`. Install it with: pip install pympi-ling"
    ) from exc


Annotation = Tuple[float, float, str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert ELAN .eaf to HDF5 segments_info")
    parser.add_argument("--eaf", required=True, help="Path to ELAN .eaf file")
    parser.add_argument("--h5", required=True, help="Target HDF5 file")
    parser.add_argument("--high-tier", required=True, help="High-level tier name")
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
        help="Optional labels that count as success; if omitted, success=1 for all segments",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing segments_info group",
    )
    return parser.parse_args()


def ms_to_s(value_ms: float) -> float:
    return float(value_ms) / 1000.0


def load_tier_annotations(eaf_path: str, tier_name: str) -> List[Annotation]:
    eaf = pympi.Elan.Eaf(eaf_path)
    if tier_name not in eaf.get_tier_names():
        return []
    annotations = eaf.get_annotation_data_for_tier(tier_name)
    return [(float(start), float(end), str(text)) for start, end, text in annotations]


def build_low_level_map(low_annotations: Dict[str, List[Annotation]]) -> Dict[int, List[Annotation]]:
    """Flatten low-level annotations by integer insertion order.

    This helper is used to keep low-level annotations grouped later by the high-level segment
    that contains them.
    """
    grouped: Dict[int, List[Annotation]] = defaultdict(list)
    idx = 0
    for tier_name, annotations in low_annotations.items():
        _ = tier_name
        for ann in annotations:
            grouped[idx].append(ann)
            idx += 1
    return grouped


def assign_low_level_annotations(high_segment: Annotation, low_annotations: Dict[str, List[Annotation]]) -> List[Annotation]:
    start_ms, end_ms, _ = high_segment
    collected: List[Annotation] = []
    for tier_name, annotations in low_annotations.items():
        _ = tier_name
        for low_start, low_end, low_text in annotations:
            if low_start >= start_ms and low_end <= end_ms:
                collected.append((low_start, low_end, low_text))
    return sorted(collected, key=lambda item: item[0])


def write_segments_info(
    h5_path: str,
    high_annotations: List[Annotation],
    low_annotations: Dict[str, List[Annotation]],
    overwrite: bool,
    success_labels: List[str] | None,
) -> None:
    if not os.path.exists(h5_path):
        with h5py.File(h5_path, "w"):
            pass

    high_sorted = sorted(high_annotations, key=lambda item: item[0])

    with h5py.File(h5_path, "a") as h5_file:
        if "segments_info" in h5_file:
            if overwrite:
                del h5_file["segments_info"]
            else:
                raise SystemExit(
                    f"`segments_info` already exists in {h5_path}. Re-run with --overwrite to replace it."
                )

        segments_group = h5_file.create_group("segments_info")

        for index, (start_ms, end_ms, text) in enumerate(high_sorted):
            segment_group = segments_group.create_group(str(index))
            segment_group.create_dataset("index", data=index)
            segment_group.create_dataset("start", data=ms_to_s(start_ms))
            segment_group.create_dataset("end", data=ms_to_s(end_ms))

            if success_labels is None:
                success = 1
            else:
                success = 1 if text in success_labels else 0
            segment_group.create_dataset("success", data=success)
            segment_group.create_dataset("text", data=text.encode("utf-8"))

            low_level = assign_low_level_annotations((start_ms, end_ms, text), low_annotations)
            if low_level:
                low_group = segment_group.create_group("low_level")
                for low_index, (low_start, low_end, low_text) in enumerate(low_level):
                    low_group_item = low_group.create_group(str(low_index))
                    low_group_item.create_dataset("start", data=ms_to_s(low_start))
                    low_group_item.create_dataset("end", data=ms_to_s(low_end))
                    low_group_item.create_dataset("success", data=1)
                    low_group_item.create_dataset("text", data=low_text.encode("utf-8"))


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.eaf):
        raise SystemExit(f"EAF file not found: {args.eaf}")

    high_annotations = load_tier_annotations(args.eaf, args.high_tier)
    if not high_annotations:
        raise SystemExit(f"No annotations found in high tier: {args.high_tier}")

    low_annotations: Dict[str, List[Annotation]] = {}
    for tier_name in args.low_tier:
        low_annotations[tier_name] = load_tier_annotations(args.eaf, tier_name)

    write_segments_info(
        h5_path=args.h5,
        high_annotations=high_annotations,
        low_annotations=low_annotations,
        overwrite=args.overwrite,
        success_labels=args.success_labels,
    )

    print(f"Converted {len(high_annotations)} high-level segments into {args.h5}")


if __name__ == "__main__":
    main()
