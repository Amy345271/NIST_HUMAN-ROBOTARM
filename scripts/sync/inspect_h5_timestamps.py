import sys
import h5py
from pprint import pprint

if len(sys.argv) < 2:
    print('Usage: python inspect_h5_timestamps.py <h5_file>')
    raise SystemExit(1)

p = sys.argv[1]
with h5py.File(p, 'r') as f:
    def walk(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(f'DATASET: {name} shape={obj.shape} dtype={obj.dtype}')
        else:
            print(f'GROUP: {name}')

    f.visititems(walk)

    # Try to find common timestamp arrays
    candidates = []
    for root, group in f.items():
        # look for datasets named 'timestamps' or containing 'timestamp'
        def find_ts(g, path=''):
            for k, v in g.items():
                full = f"{path}/{k}" if path else k
                if isinstance(v, h5py.Dataset):
                    if 'time' in k.lower() or 'stamp' in k.lower() or 'ts' == k.lower() or 'timestamps' in k.lower():
                        candidates.append(full)
                else:
                    find_ts(v, full)
        if isinstance(group, h5py.Group):
            find_ts(group, root)

    print('\nPossible timestamp datasets:')
    pprint(candidates)
