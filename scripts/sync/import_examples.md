# 传感器导入示例

本目录包含一组用于把传感器原始文件导入到 HDF5 的脚本示例：

- `import_sensor_csv.py`：按传感器预设字段名导入 CSV，支持 `wrist`、`robot`、`eye`、`force`。
- `import_audio.py`：按 `data/audio_people/<basename>.wav` 或 `data/audio_environment/<basename>.wav` 自动定位音频文件，并写入 `sample_rate`、`num_samples`、`timestamps`（可选）。
- `import_video.py`：按 `data/videos/<basename>_cam1.mp4`、`<basename>_cam2.mp4`、`<basename>_cam3.mp4` 自动定位视频文件，并可写入帧级 `timestamps`。
- `align_segments.py`：对 `segments_info` 中的每个 segment，使用可用的 `timestamps` 数组对传感器进行对齐；如果是音频或视频且只有采样率/帧率元数据，也会自动构建时间轴，并将索引写回 `segments_info/<i>/aligned/<sensor>/indices`。

快速示例：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install h5py numpy pandas soundfile

# 导入腕带 CSV（字段名按当前约定自动读取）
python import_sensor_csv.py --csv data/wrist/1_wrist.csv --h5 data/1.h5 --sensor wrist

# 导入机器人 RTDE CSV
python import_sensor_csv.py --csv data/robot/1_rtde.csv --h5 data/1.h5 --sensor robot

# 导入眼动 CSV
python import_sensor_csv.py --csv data/eye/1_eyetracker.csv --h5 data/1.h5 --sensor eye

# 导入力传感器 CSV
python import_sensor_csv.py --csv data/force/1_force.csv --h5 data/1.h5 --sensor force

# 导入人声麦克风音频（按 basename 自动找 `data/audio_people/<basename>.wav`）
python import_audio.py --basename 1 --kind people --h5 data/1.h5 --timestamps

# 导入环境麦克风音频
python import_audio.py --basename 1 --kind environment --h5 data/1.h5 --timestamps

# 注册视频并写入帧时间戳
python import_video.py --basename 1 --camera cam1 --h5 data/1.h5 --frame-rate 30.0 --num-frames 1200 --timestamps

# 也可以直接给显式视频路径
python import_video.py --video data/videos/1_cam2.mp4 --h5 data/1.h5 --frame-rate 30.0 --num-frames 1200 --timestamps

# 对齐并写回 indices
python align_segments.py data/1.h5
```

说明：脚本尽量保持通用，你可以根据实际 CSV 列名通过 `--time-col` 和 `--value-cols` 调整。对视频帧的严格对齐需要先用 `ffprobe` 或其他工具获取 `num_frames` 和 `frame_rate`，并通过 `import_video.py` 写入 HDF5。
