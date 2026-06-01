import h5py, os, sys
try:
    import cv2
except Exception as e:
    cv2 = None

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
h5_path = os.path.join(base_dir, 'data', '1.h5')
if not os.path.exists(h5_path):
    print('HDF5 missing:', h5_path)
    sys.exit(0)

with h5py.File(h5_path,'r') as f:
    sensors = f.get('sensors', None)
    if sensors is None:
        print('No sensors group in', h5_path)
        sys.exit(0)
    print('Sensors groups:', list(sensors.keys()))
    for cam in ['cam1','cam2','cam3']:
        if cam in sensors:
            g = sensors[cam]
            print('\n==', cam, '==')
            for k,v in g.attrs.items():
                print(' attr', k, type(v), v)
            path = None
            for cand in ('video_path','source_path','path'):
                if cand in g.attrs:
                    path = g.attrs[cand]
                    break
            if path is not None:
                try:
                    path = path.decode() if isinstance(path, (bytes,bytearray)) else str(path)
                except:
                    path = str(path)
                print(' video_path attr ->', path)
                exists = os.path.exists(path)
                print(' exists:', exists)
                if exists:
                    if cv2 is not None:
                        cap = cv2.VideoCapture(path)
                        if not cap.isOpened():
                            print(' cv2 cannot open video')
                        else:
                            fc = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                            fps = cap.get(cv2.CAP_PROP_FPS)
                            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            print(' cv2 frame_count', fc, 'fps', fps, 'w', w, 'h', h)
                            if fps>0 and fc>0:
                                print(' cv2 duration_s', fc / fps)
                            cap.release()
                    else:
                        print(' cv2 not available; skipping video probe')
                else:
                    print(' video file not found on disk')
            else:
                print(' no video_path attr found')
# end
