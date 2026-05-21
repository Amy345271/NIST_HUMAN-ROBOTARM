#!/usr/bin/env python3
"""
Convert ELAN .eaf annotation files to HDF5 segments_info structure used by REASSEMBLE.

Usage:
  python eaf_to_h5.py --eaf path/to/file.eaf --h5 path/to/file.h5 --high-tier HighLevel --low-tier LowLevel1 --low-tier LowLevel2

The script writes/overwrites the `segments_info` group in the target HDF5 file. Times in .eaf are milliseconds; we convert them to seconds.

Requires: pympi-ling (pip install pympi-ling), h5py
"""
import argparse
import os
import sys
import h5py
from typing import List, Tuple

try:
    import pympi
except Exception as e:
    print('Missing dependency: pympi. Install with `pip install pympi-ling`')
    raise


def parse_args():
    p = argparse.ArgumentParser(description='Convert ELAN .eaf to HDF5 segments_info')
    p.add_argument('--eaf', required=True, help='Path to .eaf file')
    p.add_argument('--h5', required=True, help='Target HDF5 file to write segments_info into')
    p.add_argument('--high-tier', required=True, help='Tier name to use as high-level segments (exact match)')
    p.add_argument('--low-tier', action='append', default=[], help='Tier name(s) to use as low-level annotations (can repeat)')
    p.add_argument('--overwrite', action='store_true', help='Remove existing segments_info in HDF5 before writing')
    p.add_argument('--success-labels', nargs='*', default=None,
                   help='Optional list of labels that count as success; if omitted all segments set success=1')
    return p.parse_args()


def ms_to_s(ms: float) -> float:
    return float(ms) / 1000.0


def collect_annotations(eaf_path: str, tier: str) -> List[Tuple[float, float, str]]:
    eaf = pympi.Elan.Eaf(eaf_path)
    if tier not in eaf.get_tier_names():
        return []
    ann = eaf.get_annotation_data_for_tier(tier)
    # ann: list of (start, end, value) in ms
    return [(float(a[0]), float(a[1]), a[2]) for a in ann]


def write_segments_info(h5_path: str, high_ann: List[Tuple[float, float, str]], low_ann_map: dict,
                        overwrite: bool = False, success_labels: List[str] = None):
    # high_ann: list of (start_ms, end_ms, label)
    # low_ann_map: tier_name -> list of (start_ms, end_ms, label)

    if not os.path.exists(h5_path):
        # create empty h5
        with h5py.File(h5_path, 'w'):
            pass

    with h5py.File(h5_path, 'a') as f:
        if 'segments_info' in f:
            if overwrite:
                del f['segments_info']
            else:
                print('segments_info already exists in', h5_path, 'use --overwrite to replace')
                raise SystemExit(1)

        segs = f.create_group('segments_info')

        # sort high level by start
        high_sorted = sorted(high_ann, key=lambda x: x[0])

        for idx, (hs, he, hlabel) in enumerate(high_sorted):
            grp = segs.create_group(str(idx))
            grp.create_dataset('index', data=idx)
            grp.create_dataset('start', data=ms_to_s(hs))
            grp.create_dataset('end', data=ms_to_s(he))
            success = 1
            if success_labels is not None:
                success = 1 if hlabel in success_labels else 0
            grp.create_dataset('success', data=success)
            grp.create_dataset('text', data=str(hlabel).encode('utf-8'))

            # collect low-level annotations falling inside this high-level segment
            sub_ann = []
            for tier, anns in low_ann_map.items():
                for (ls, le, llabel) in anns:
                    # include if low segment lies within high segment (allow touching boundaries)
                    if ls >= hs and le <= he:
                        sub_ann.append((ls, le, llabel))

            # sort by start time and write as ordered low_level child groups
            sub_ann_sorted = sorted(sub_ann, key=lambda x: x[0])
            low_grp = grp.create_group('low_level') if sub_ann_sorted else None
            for sub_idx, (ls, le, llabel) in enumerate(sub_ann_sorted):
                sg = low_grp.create_group(str(sub_idx))
                sg.create_dataset('start', data=ms_to_s(ls))
                sg.create_dataset('end', data=ms_to_s(le))
                sg.create_dataset('success', data=1)
                sg.create_dataset('text', data=str(llabel).encode('utf-8'))

    print(f'Wrote {len(high_sorted)} high-level segments to {h5_path}')


def main():
    args = parse_args()
    if not os.path.exists(args.eaf):
        print('EAF file not found:', args.eaf)
        sys.exit(1)

    print('Collecting high-level annotations from tier:', args.high_tier)
    high_ann = collect_annotations(args.eaf, args.high_tier)
    if not high_ann:
        print('No annotations found in high tier', args.high_tier)
        sys.exit(1)

    low_map = {}
    for lt in args.low_tier:
        print('Collecting low-level annotations from tier:', lt)
        low_map[lt] = collect_annotations(args.eaf, lt)

    write_segments_info(args.h5, high_ann, low_map, overwrite=args.overwrite, success_labels=args.success_labels)


if __name__ == '__main__':
    main()
