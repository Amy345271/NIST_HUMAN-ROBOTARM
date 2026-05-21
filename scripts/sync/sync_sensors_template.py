"""
Synchronization template for the new NIST_HUMAN-ROBOTARM project.

You should adapt the sensor names to your actual files and HDF5 structure:
- panoramic camera
- close camera
- wrist camera
- skin conductance wristband CSV
- RTDE robot logs
- eye tracker
- microphones
- force / strain gauges

The key idea is to use one reference timeline (usually timestamps from a camera or the
recording computer) and align the other streams to the same start/end interval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import numpy as np


@dataclass
class Segment:
    start: float
    end: float
    label: str


def find_indices_between(timestamps: np.ndarray, start: float, end: float) -> List[int]:
    timestamps = np.asarray(timestamps)
    return np.where((timestamps >= start) & (timestamps <= end))[0].tolist()


def closest_indices(reference_timestamps: np.ndarray, target_timestamps: np.ndarray) -> np.ndarray:
    reference_timestamps = np.asarray(reference_timestamps)
    target_timestamps = np.asarray(target_timestamps)
    diffs = np.abs(reference_timestamps[:, None] - target_timestamps[None, :])
    return np.argmin(diffs, axis=1)


def align_stream_to_segment(timestamps: np.ndarray, segment: Segment) -> List[int]:
    return find_indices_between(timestamps, segment.start, segment.end)


def align_multimodal_streams(
    segment: Segment,
    timestamps_by_sensor: Dict[str, np.ndarray],
) -> Dict[str, List[int]]:
    aligned: Dict[str, List[int]] = {}
    for sensor_name, timestamps in timestamps_by_sensor.items():
        aligned[sensor_name] = align_stream_to_segment(timestamps, segment)
    return aligned


def summarize_alignment(segment: Segment, timestamps_by_sensor: Dict[str, np.ndarray]) -> None:
    print(f"segment={segment.label} start={segment.start:.3f} end={segment.end:.3f}")
    for sensor_name, timestamps in timestamps_by_sensor.items():
        indices = align_stream_to_segment(timestamps, segment)
        print(f"  {sensor_name}: {len(indices)} samples")


if __name__ == "__main__":
    print("Edit this template to match your sensor file formats and timestamp conventions.")
