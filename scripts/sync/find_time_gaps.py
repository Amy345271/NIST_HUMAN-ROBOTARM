#!/usr/bin/env python3
"""Scan all data/*.h5 and report large timestamp gaps per sensor.

Criteria: a gap is reported if diff > max(absolute_thresh, factor * median_dt)
Defaults: absolute_thresh=1.0 (s), factor=5

Usage: python find_time_gaps.py [--data-root data] [--abs 1.0] [--factor 5]
"""
from __future__ import annotations
import argparse
import glob
import json
import os
from pathlib import Path

import h5py
import numpy as np


def scan_h5(path: str, abs_thresh: float, factor: float):
    out = {}
    with h5py.File(path, 'r') as f:
        sensors = f.get('sensors', {})
        for s in sorted(sensors.keys()):
            g = sensors[s]
            if 'timestamps' not in g:
                continue
            ts = g['timestamps'][()]
            if len(ts) < 2:
                continue
            diffs = np.diff(ts)
            # ignore non-positive diffs for median calculation
            positive = diffs[diffs > 0]
            if len(positive) == 0:
                median = 0.0
            else:
                median = float(np.median(positive))
            thresh = max(abs_thresh, factor * median)
            gap_indices = np.where(diffs > thresh)[0]
            if len(gap_indices) > 0:
                gaps = []
                for idx in gap_indices:
                    gaps.append({
                        'index': int(idx),
                        'prev_ts': float(ts[idx]),
                        'next_ts': float(ts[idx+1]),
                        'gap_s': float(diffs[idx]),
                        'median_dt': median,
                        'thresh': thresh,
                    })
                out[s] = gaps
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data-root', default='data')
    p.add_argument('--abs', type=float, default=1.0, dest='abs_thresh')
    p.add_argument('--factor', type=float, default=5.0)
    p.add_argument('--out', default=None)
    args = p.parse_args()

    data_root = Path(args.data_root)
    h5_paths = sorted(glob.glob(str(data_root / '*.h5')))
    summary = {}
    for h5 in h5_paths:
        basename = os.path.splitext(os.path.basename(h5))[0]
        try:
            gaps = scan_h5(h5, args.abs_thresh, args.factor)
            if gaps:
                summary[basename] = gaps
        except Exception as e:
            summary[basename] = {'error': str(e)}

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, indent=2, ensure_ascii=False)
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
