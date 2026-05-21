# Project sensors and recommended fields

Sensors:

- Cameras:
  - panoramic (dataset name: panoramic or hama1)
  - close (dataset name: close or hama2)
  - wrist (dataset name: wrist or hand)
  - Each camera: frames array and matching timestamps in HDF5 under `timestamps/<camera>`.

- Wristband (skin conductance): CSV with columns: `timestamp,value`
- Robot RTDE: CSV or HDF5 with timestamps and joint states: `timestamp,joint_positions(7),joint_velocities(7),gripper`
- Eye tracker: CSV with `timestamp,gaze_x,gaze_y` (or suitable fields)
- Microphones: audio files or arrays; prefer storing short-time feature arrays with timestamps or sample-level timestamps
  - human_voice_mic: annotations exist in ELAN (use `eaf_to_h5.py` to map)
  - headset_mic: raw audio
- Force / strain gauges: CSV/HDF5 with `timestamp,force_x,force_y,force_z` or strain channel values

Recommendations:

- Use seconds (float) for all timestamps in HDF5 to match REASSEMBLE conventions.
- Store per-sensor timestamps under `timestamps/<sensor>` as 1D arrays.
- Use `segments_info` HDF5 group to store high-level and low-level annotations.
Project sensors and recommended fields

Sensors:
- Cameras:
  - panoramic (dataset name: panoramic or hama1)
  - close (dataset name: close or hama2)
  - wrist (dataset name: wrist or hand)
  Each camera: frames array and matching timestamps in HDF5 under `timestamps/<camera>`.

- Wristband (skin conductance): CSV with columns: `timestamp,value`
- Robot RTDE: CSV or HDF5 with timestamps and joint states: `timestamp,joint_positions(7),joint_velocities(7),gripper`
- Eye tracker: CSV with `timestamp,gaze_x,gaze_y` (or suitable fields)
- Microphones: audio files or arrays; prefer storing short-time feature arrays with timestamps or sample-level timestamps
  - human_voice_mic: annotations exist in ELAN (use `eaf_to_h5.py` to map)
  - headset_mic: raw audio
- Force / strain gauges: CSV/HDF5 with `timestamp,force_x,force_y,force_z` or strain channel values

Recommendations:
- Use seconds (float) for all timestamps in HDF5 to match REASSEMBLE conventions.
- Store per-sensor timestamps under `timestamps/<sensor>` as 1D arrays.
- Use `segments_info` HDF5 group to store high-level and low-level annotations.
