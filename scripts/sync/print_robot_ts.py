import h5py
import numpy as np
f='H:\\备份\\study\\school\\大三\\大三下\\机电系统设计开发\\项目\\NIST_HUMAN&ROBOTARM\\data\\1.h5'
with h5py.File(f,'r') as fh:
    ts=fh['sensors']['robot']['timestamps'][()]
    print('len', len(ts))
    print('min max', float(ts.min()), float(ts.max()))
    # find indices nearest to 28 and 33
    idx28 = np.searchsorted(ts, 28.0)
    print('idx28', idx28, 'ts[idx28-5:idx28+5]', ts[max(0,idx28-5):idx28+5])
    idx = np.where((ts>=28.0)&(ts<=33.349))[0]
    print('count in [28,33.349]', len(idx))
    if len(idx):
        print('first', idx[0], ts[idx[0]])
        print('last', idx[-1], ts[idx[-1]])
    # print a sample slice from start
    print('head 0:20', ts[:20])
    print('slice 1000:1020', ts[1000:1020])
