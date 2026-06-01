#!/usr/bin/env python3
"""Debug tool: for a given data/<basename>.h5 and segment index, print counts and
first/last timestamps for each sensor and show which indices would be selected.
"""
from __future__ import annotations
import sys
import h5py
import numpy as np

if len(sys.argv) < 3:
    print('Usage: debug_segment_checks.py <h5_path> <segment_index>')
    sys.exit(2)

h5_path = sys.argv[1]
seg_idx = sys.argv[2]

with h5py.File(h5_path,'r') as f:
    si = f.get('segments_info')
    if si is None or seg_idx not in si:
        print('Segment not found:', seg_idx)
        sys.exit(1)
    seg = si[seg_idx]
    start = float(seg.attrs.get('start_time', seg.get('start')[()])) if ('start_time' in seg.attrs or 'start' in seg) else None
    end = float(seg.attrs.get('end_time', seg.get('end')[()])) if ('end_time' in seg.attrs or 'end' in seg) else None
    print(f'Segment {seg_idx}: start={start} end={end}')

    sensors = f['sensors']
    for s in sorted(sensors.keys()):
        g = sensors[s]
        print('\nSensor', s)
        if 'timestamps' in g:
            ts = g['timestamps'][()]
            print('  timestamps len=%d min=%.6f max=%.6f' % (len(ts), float(ts.min()), float(ts.max())))
            # find indices between start and end (inclusive)
            idxs = np.where((ts >= start) & (ts <= end))[0]
            print('  matched count', len(idxs))
            if len(idxs)>0:
                print('   first', idxs[0], 't', ts[idxs[0]])
                print('   last', idxs[-1], 't', ts[idxs[-1]])
        else:
            print('  no timestamps; attrs:', dict(g.attrs))
