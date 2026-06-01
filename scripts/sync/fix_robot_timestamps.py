#!/usr/bin/env python3
"""Fix robot timestamps in HDF5 by removing large gaps.

This is a conservative, reversible change:
- If `/sensors/robot/timestamps_orig` does not exist, copy the original timestamps there.
- Create a corrected `/sensors/robot/timestamps` where any gap > abs_thresh is removed
  by shifting all subsequent timestamps earlier by (gap - median_dt) so that the timeline
  becomes continuous. The algorithm accumulates shifts for multiple gaps.

Usage: python fix_robot_timestamps.py <h5_path> [--abs 1.0]
"""
from __future__ import annotations
import argparse
import os
import sys

import h5py
import numpy as np


def fix_timestamps(ts: np.ndarray, abs_thresh: float = 1.0, factor: float = 5.0):
    if len(ts) < 2:
        return ts, []
    diffs = np.diff(ts)
    positive = diffs[diffs > 0]
    median = float(np.median(positive)) if len(positive) > 0 else 0.0
    thresh = max(abs_thresh, factor * median)
    gap_idxs = np.where(diffs > thresh)[0]
    shifts = []
    corrected = ts.copy().astype('f8')
    cumulative = 0.0
    for idx in gap_idxs:
        prev = corrected[idx]
        nxt = corrected[idx + 1]
        gap = nxt - prev
        # amount to remove so gap becomes ~median (not zero)
        remove = gap - median
        if remove <= 0:
            continue
        cumulative += remove
        corrected[idx+1:] -= remove
        shifts.append({
            'index': int(idx),
            'prev_ts': float(prev),
            'next_ts': float(nxt),
            'gap_s': float(gap),
            'removed_s': float(remove),
            'median_dt': median,
            'thresh': thresh,
        })
    return corrected, shifts


def main():
    p = argparse.ArgumentParser()
    p.add_argument('h5', help='HDF5 path')
    p.add_argument('--abs', dest='abs_thresh', type=float, default=1.0)
    p.add_argument('--factor', type=float, default=5.0)
    args = p.parse_args()

    if not os.path.exists(args.h5):
        print('Missing', args.h5)
        sys.exit(2)

    with h5py.File(args.h5, 'a') as f:
        sensors = f.get('sensors')
        if sensors is None or 'robot' not in sensors:
            print('No robot sensor in', args.h5)
            return
        g = sensors['robot']
        if 'timestamps' not in g:
            print('robot has no timestamps in', args.h5)
            return
        ts = g['timestamps'][()]
        if 'timestamps_orig' not in g:
            g.create_dataset('timestamps_orig', data=ts, dtype='f8')
            print('Backed up original timestamps -> sensors/robot/timestamps_orig')
        corrected, shifts = fix_timestamps(ts, abs_thresh=args.abs_thresh, factor=args.factor)
        if not shifts:
            print('No significant gaps found; nothing changed for', args.h5)
            return
        # overwrite timestamps
        del g['timestamps']
        g.create_dataset('timestamps', data=corrected, dtype='f8')
        print(f'Applied {len(shifts)} shifts to sensors/robot/timestamps in {args.h5}')
        for s in shifts:
            print(' idx', s['index'], 'prev', s['prev_ts'], 'next', s['next_ts'], 'gap', s['gap_s'], 'removed', s['removed_s'])


if __name__ == '__main__':
    main()
