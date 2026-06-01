#!/usr/bin/env python3
"""Align sensors to segments in `segments_info` and write per-segment indices.

For each segment in `/segments_info/<i>` this script looks for sensors under
`/sensors/*` that contain a `timestamps` dataset, or metadata that can be used
to build one (audio: `sample_rate`+`num_samples`, video: `frame_rate`+
`num_frames`), and writes aligned indices to
`/segments_info/<i>/aligned/<sensor>/indices` (int array).

Usage:
  python align_segments.py data/1.h5
"""

from __future__ import annotations

import sys
import h5py
import numpy as np
from typing import Dict


def find_indices_between(timestamps: np.ndarray, start: float, end: float) -> np.ndarray:
    return np.where((timestamps >= start) & (timestamps <= end))[0].astype(np.int64)


def load_sensor_timestamps(sensor_group) -> np.ndarray | None:
    # Prefer explicit 'timestamps' dataset
    if 'timestamps' in sensor_group:
        return sensor_group['timestamps'][()]
    # If audio-style attributes present, build timeline
    if 'sample_rate' in sensor_group.attrs and 'num_samples' in sensor_group.attrs:
        sr = float(sensor_group.attrs['sample_rate'])
        n = int(sensor_group.attrs['num_samples'])
        return np.arange(n) / sr
    # If video metadata present, build frame timeline
    if 'frame_rate' in sensor_group.attrs and 'num_frames' in sensor_group.attrs:
        start_time = float(sensor_group.attrs.get('start_time', 0.0))
        framerate = float(sensor_group.attrs['frame_rate'])
        num_frames = int(sensor_group.attrs['num_frames'])
        return start_time + np.arange(num_frames, dtype=np.float64) / framerate
    # No timestamps available
    return None


def main():
    if len(sys.argv) < 2:
        print('Usage: python align_segments.py <h5_file>')
        raise SystemExit(1)
    h5_path = sys.argv[1]

    with h5py.File(h5_path, 'a') as f:
        if 'segments_info' not in f:
            raise SystemExit('No segments_info found in HDF5')
        sensors = f.get('sensors', {})

        # preload timestamps for sensors
        ts_by_sensor: Dict[str, np.ndarray] = {}
        if isinstance(sensors, h5py.Group):
            for sname, sgroup in sensors.items():
                ts = load_sensor_timestamps(sgroup)
                if ts is not None:
                    ts_by_sensor[sname] = np.asarray(ts)

        segs = f['segments_info']
        for seg_name in sorted(segs.keys(), key=lambda x: int(x)):
            seg = segs[seg_name]
            start = float(seg['start'][()])
            end = float(seg['end'][()])
            aligned_group = seg.require_group('aligned')
            print(f'Aligning segment {seg_name} start={start:.3f} end={end:.3f}')
            for sname, timestamps in ts_by_sensor.items():
                indices = find_indices_between(timestamps, start, end)
                ag = aligned_group.require_group(sname)
                # overwrite existing
                if 'indices' in ag:
                    del ag['indices']
                ag.create_dataset('indices', data=indices, dtype='i8')
                print(f'  {sname}: {len(indices)} samples')

    print('Alignment complete.')


if __name__ == '__main__':
    main()
