"""
Template utilities for synchronizing multimodal sensors to annotation segments.
Sensors expected in this project:
- Cameras: panoramic, close, wrist (stored as HDF5 datasets / frames with timestamps)
- Wristband (skin conductance): CSV with timestamp and value
- Robot RTDE logs: CSV or HDF5 with timestamps
- Eye tracker: CSV with timestamps
- Two microphones: audio files or arrays with timestamps; human voice mic annotated in ELAN
- Force/strain gauge: CSV/HDF5 with timestamps

Approach:
1. Ensure all sensors have timestamps in the same reference (seconds since epoch or recording start).
2. Load annotation segments (HDF5 `segments_info`) as reference segments.
3. For each segment, find timestamps/indices in each sensor that fall within [start, end].
4. Align sensors to reference using nearest-timestamp or linear interpolation for continuous signals.

This file contains small helper functions you'll expand for your data formats.
"""

import numpy as np
import h5py
from typing import List


def find_indices_between(timestamps: np.ndarray, start: float, end: float) -> List[int]:
    # timestamps: 1D numpy array in seconds
    return np.where((timestamps >= start) & (timestamps <= end))[0].tolist()


def find_closest_indices(reference: np.ndarray, target: np.ndarray) -> np.ndarray:
    """For each value in reference, find index in target with closest timestamp."""
    reference = np.array(reference)
    target = np.array(target)
    diffs = np.abs(reference[:, None] - target[None, :])
    return np.argmin(diffs, axis=1)


def load_csv_timestamps(csv_path: str, time_col: str = 'timestamp') -> np.ndarray:
    import pandas as pd
    df = pd.read_csv(csv_path)
    return df[time_col].to_numpy()


def extract_segment_data(h5_path: str, segment_start: float, segment_end: float):
    with h5py.File(h5_path, 'r') as f:
        timestamps = f['timestamps']
        # example: get hand camera timestamps
        hand_ts = timestamps['hand'][...]
        indices = find_indices_between(hand_ts, segment_start, segment_end)
        # extract frames, robot states, etc. similarly
        return indices


if __name__ == '__main__':
    print('Template sync utilities. Edit to match your file formats.')
