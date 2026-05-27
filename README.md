# NIST_HUMAN-ROBOTARM

This repository is the working directory for building a multimodal dataset and synchronization pipeline inspired by REASSEMBLE.

## Current scope

- ELAN-based annotation conversion into HDF5 `segments_info`
- Sensor synchronization templates for multi-camera, wearable, robot, audio, eye-tracking, and force data
- Local iteration and versioning of scripts and notes

## Expected local layout

- `annotation/eaf/` - ELAN annotation files (`.eaf`)
- `data/` - raw or processed data files, including HDF5 recordings
- `scripts/labeling/` - annotation conversion utilities
- `scripts/sync/` - synchronization helpers and templates

## Multimodal data schema

This project expects each recording to use the same basename across annotation and sensor files. For example, `1.eaf` should pair with `data/1.h5` and the same `<basename>` should be reused across sensor files.

### Video data

Directory:

```text
data/videos/
```

Expected file names:

- Panoramic camera: `<basename>_cam1.mp4`
- Close-up camera: `<basename>_cam2.mp4`
- Wrist camera: `<basename>_cam3.mp4`

### Audio data

- Human voice microphone: `data/audio_people/<basename>.wav`
- Environment microphone: `data/audio_environment/<basename>.wav`

### Wrist sensor data (SCL / skin conductance)

- File path: `data/wrist/<basename>_wrist.csv`
- Expected fields:
	- 相对时间_秒
	- 原始日志时间戳
	- GSR电压(V)
	- 心率(bpm)
	- 血氧(%)
	- 加速度X(g)
	- 加速度Y(g)
	- 加速度Z(g)
	- 陀螺仪X(°/s)
	- 陀螺仪Y(°/s)
	- 陀螺仪Z(°/s)
	- 校验正确

### RTDE robot data

- File path: `data/robot/<basename>_rtde.csv`
- Expected fields:
	- `robot_timestamp`
	- `pc_timestamp`
	- `q0` - `q5`
	- `curr0` - `curr5`
	- `x`, `y`, `z`
	- `rx`, `ry`, `rz`
	- `fx`, `fy`, `fz`
	- `mx`, `my`, `mz`
	- `gripper_command`

### Eye-tracking data

- File path: `data/eye/<basename>_eyetracker.csv`
- Expected fields:
	- `session_time_s`
	- `system_timestamp_us`
	- `raw_timestamp_us`
	- `x_norm`
	- `y_norm`
	- `validity`

### Force sensor data

- File path: `data/force/<basename>_force.csv`
- Expected fields:
	- `time_ms`
	- `raw_value`
	- `voltage_V`
	- `force_N`

### How this schema is used

- ELAN annotations are converted into `segments_info` inside `data/<basename>.h5`.
- Sensor import scripts should write timestamps into `/sensors/<sensor>/timestamps` whenever possible.
- Sensor values should be written into `/sensors/<sensor>/values` or sensor-specific datasets when the structure is not a simple table.
- The synchronization scripts align these timestamps against each segment in `segments_info`.

## Quick start

### Python environment

Create a local virtual environment on Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install h5py numpy pandas pympi-ling
```

If you want to remove the environment later:

```powershell
deactivate
Remove-Item -Recurse -Force .venv
```

Optional Conda workflow:

```powershell
conda create -n nist_human_robotarm python=3.10
conda activate nist_human_robotarm
pip install h5py numpy pandas pympi-ling
```

Remove the Conda environment with:

```powershell
conda deactivate
conda env remove -n nist_human_robotarm
```

Convert one ELAN file into `segments_info`:

```powershell
python scripts\labeling\eaf_to_h5.py --eaf annotation\eaf\1.eaf --h5 data\1.h5 --high-tier HL --low-tier LL --overwrite
```

Batch convert all `annotation/eaf/*.eaf` files when matching `.h5` files already exist:

```powershell
python scripts\labeling\batch_eaf_to_h5.py --eaf-dir annotation\eaf --h5-dir data --high-tier HL --low-tier LL --overwrite
```

批量转换说明（示例）：

- 如果你的 ELAN 高层是 `voice`（本仓库示例），使用下面的命令：

```powershell
python scripts\labeling\batch_eaf_to_h5.py --eaf-dir annotation\eaf --h5-dir data --high-tier voice --low-tier LL --overwrite
```

- 批量脚本会匹配 `annotation/eaf/<basename>.eaf` 到 `data/<basename>.h5`；请确保两者基名一致。
- 若有多个低层 tier，可重复使用 `--low-tier` 参数，例如 `--low-tier LL1 --low-tier LL2`。


## Notes

- ELAN timestamps are stored in milliseconds; the scripts convert them to seconds for HDF5.
- Keep tier names consistent with your ELAN tiers.
- Avoid committing large raw sensor files unless needed; prefer storing them outside Git or using LFS.

## 文档

- [Git 使用入门指南](GIT_GUIDE.md)

**进展**

- **已完成**: 添加 [GIT_GUIDE.md](GIT_GUIDE.md)（Git 使用入门指南）
- **已完成**: 增强 `scripts/labeling/eaf_to_h5.py` 的容错与提示（当指定 tier 不存在时列出可用 tiers）
- **已完成**: 将 `annotation/eaf/1.eaf` 转换为 `data/1.h5`（单文件转换已执行）
- **已完成**: 添加同步检查脚本 `scripts/sync/inspect_h5_timestamps.py`，用于列出 HDF5 中可用的时间戳数据集
- **已完成**: 在 `scripts/labeling/` 和 `scripts/sync/` 中补充了若干模板与示例脚本

**下一步（待完成）**

- **验证**: 检查 `data/1.h5` 中的 `segments_info` 与时间戳是否一致（脚本位于 `scripts/sync/`）
- **批量转换**: 使用 `scripts/labeling/batch_eaf_to_h5.py` 批量处理 `annotation/eaf/*.eaf`
- **对齐同步**: 选择参考时间线（例如某个 camera 的 `timestamps`）并运行同步脚本对齐各传感器
- **发布**: 网络可用时把本地提交 `git push` 到远程仓库
