# NIST_HUMAN-ROBOTARM

本仓库是一个工作目录，用于构建受 REASSEMBLE 启发的多模态数据集和同步流水线。

## 当前范围

- 将 ELAN 标注转换为 HDF5 中的 `segments_info`
- 为多相机、穿戴设备、机器人、音频、眼动和力数据提供同步模板
- 对脚本和说明文档进行本地迭代与版本管理

## 期望的本地目录结构

- `annotation/eaf/` - ELAN 标注文件（`.eaf`）
- `data/` - 原始或处理后的数据文件，包括 HDF5 记录
- `scripts/labeling/` - 标注转换工具
- `scripts/sync/` - 同步辅助脚本和模板

## 多模态数据结构

本项目要求同一条录制在标注文件和传感器文件中使用相同的基名。例如，`1.eaf` 应该对应 `data/1.h5`，并且所有传感器文件都应复用同一个 `<basename>`。

### 视频数据
**进展**

- **已完成**: 添加 [GIT_GUIDE.md](GIT_GUIDE.md)（Git 使用入门指南）
- **已完成**: 增强 `scripts/labeling/eaf_to_h5.py` 的容错与提示（当指定 tier 不存在时列出可用 tiers）
- **已完成**: 添加同步检查脚本 `scripts/sync/inspect_h5_timestamps.py`，用于列出 HDF5 中可用的时间戳数据集
- **已完成**: 添加 `scripts/sync/run_multisensor_pipeline.py`，实现单条记录的自动导入 + 对齐
- **已完成**: 添加 `scripts/sync/run_multisensor_batch.py`，实现批量处理 `1`、`2` 及后续更多 basename
- **已完成**: `force` 文件支持 `.csv` 和 `.xlsx`，并兼容 `openpyxl`
- **已完成**: 实际跑通 `1` 和 `2` 两条记录，`data/1.h5` 与 `data/2.h5` 均已生成对齐结果

**近期已完成（重要更新）**

- **视频自动探测与修复**：`scripts/sync/import_video.py` 在使用 `--timestamps` 时会 probe MP4 文件以读取真实 `frame_rate`/`num_frames`，并优先采用探测值；若用户显式传入的值与探测值差异显著，脚本会打印警告并使用探测值，避免在 HDF5 中写入错误持续时长。
- **批量修正视频元数据**：新增 `scripts/sync/batch_fix_videos.py`，用于对仓库中所有 `data/*.h5` 执行视频元数据重写（已对 `1`、`2` 运行并更新 `num_frames`/`frame_rate`）。
- **CSV/Excel 导入增强**：`scripts/sync/import_sensor_csv.py` 增加编码回退（`utf-8-sig`, `utf-8`, `gbk`, `gb18030`）、Excel (`.xlsx`) 支持及头行自动提升逻辑，提高对中文/非标准导出文件的兼容性。
- **机器人时间轴归一化**：导入 `robot` 时优先使用 `pc_timestamp` 并减去首样本，保证 `robot` 时间与 `segments_info` 同一零点；原始 `robot_timestamp` 字段仍保留在记录里供溯源。
- **时间同步归档改进**：`scripts/sync/build_timesync_h5.py` 已更新以复用统一的时间戳提取逻辑并写入根级 streams + `/timestamps`（文件属性 `layout="time_sync_archive"` 标记此格式）。
- **诊断与检测工具**：新增 `scripts/sync/probe_videos.py`（探测 HDF5 中 video 路径并用 cv2 probe 原文件）、`scripts/sync/debug_segment_checks.py`（检查某个 segment 各传感器样本匹配）、`scripts/sync/find_time_gaps.py`（批量扫描 `data/*.h5` 中显著时间跳跃并输出汇总）。
- **已发现的问题说明**：在 `data/1.h5` 与 `data/2.h5` 的 `robot` 时间轴检测到若干大跳跃（gap），例如 21s→42s 等，导致部分中间段 align 时 `robot` 显示 0 samples；这是原始日志数据的问题（记录器/传输中断或时间基准切换），仓库中已加入检测脚本以便定位并决定後續修复策略（修复原 CSV / 插值 / 标注缺失）。

这些更新已在本地运行验证，相关脚本位于 `scripts/sync/`，可直接复现与审查。

**当前成果**

- **标注转换**: `annotation/eaf/<basename>.eaf` → `data/<basename>.h5` 的 `segments_info`
- **多模态导入**: `wrist`、`robot`、`eye`、`force`、`audio_people`、`audio_environment` 已接入同一条流水线
- **同步对齐**: `align_segments.py` 会把每个 segment 对应的传感器索引寫回 HDF5
- **批量处理**: `run_multisensor_batch.py` 会自动发现 `annotation/eaf/*.eaf` 并逐个执行转换 + 导入 + 对齐

**推荐执行顺序**

1. 确认依赖已安装：`pympi-ling`、`openpyxl`、`h5py`、`numpy`、`pandas`
2. 先处理单条记录验证流程，例如 `basename=2`
3. 再执行批处理，统一跑完 `1`、`2` 和後續新增记录
4. 如需视频同步，再補充 `--video-frame-rate` 和 `--video-num-frames`

**已验证命令**

- `python scripts\sync\run_multisensor_batch.py --basenames 2 --high-tier voice --low-tier LL --skip-videos`
- `python scripts\sync\run_multisensor_batch.py --high-tier voice --low-tier LL --skip-videos`
	- 加速度Y(g)
	- 加速度Z(g)
	- 陀螺仪X(°/s)
	- 陀螺仪Y(°/s)
	- 陀螺仪Z(°/s)
	- 校验正确

### RTDE 机器人数据


- 文件路径：`data/robot/<basename>_rtde.csv`
- 预期字段：
	- `robot_timestamp`
	- `pc_timestamp`
	- `q0` - `q5`
	- `curr0` - `curr5`
	- `x`, `y`, `z`
	- `rx`, `ry`, `rz`
	- `fx`, `fy`, `fz`
	- `mx`, `my`, `mz`
	- `gripper_command`

	说明：导入脚本会优先使用 `pc_timestamp` 作为统一时间轴，并在写入 HDF5 时减去首个时间点，使机器人数据与 `segments_info` 共享同一个零点基准；`robot_timestamp` 会作为原始字段保留在记录里。

### 眼动数据

- 文件路径：`data/eye/<basename>_eyetracker.csv`
- 预期字段：
	- `session_time_s`
	- `system_timestamp_us`
	- `raw_timestamp_us`
	- `x_norm`
	- `y_norm`
	- `validity`

### 力传感器数据

- 文件路径：`data/force/<basename>_force.csv` 或 `data/force/<basename>_force.xlsx`
- 预期字段：
	- `time_ms`
	- `raw_value`
	- `voltage_V`
	- `force_N`

### 该结构的使用方式

- ELAN 标注会被转换为 `data/<basename>.h5` 中的 `segments_info`。
- 传感器导入脚本应尽可能把时间戳写入 `/sensors/<sensor>/timestamps`。
- 如果结构不是简单表格，传感器值应写入 `/sensors/<sensor>/values` 或该传感器专属的数据集。
- 同步脚本会将这些时间戳与 `segments_info` 中的每个片段对齐。
- CSV 导入器会自动尝试 `utf-8-sig`、`utf-8`、`gbk` 和 `gb18030` 等常见编码，这对导出的中文传感器日志很有用。
- 如果你的 `force` 文件是 `.xlsx`，请在同一环境中安装 `openpyxl`，这样 pandas 才能读取。

## 快速开始

### Python 环境

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

批量转换所有 `annotation/eaf/*.eaf` 文件（前提是对应的 `.h5` 文件已经存在）：

```powershell
python scripts\labeling\batch_eaf_to_h5.py --eaf-dir annotation\eaf --h5-dir data --high-tier HL --low-tier LL --overwrite
```

批量转换说明（示例）：

- 如果你的 ELAN 高层 tier 是 `voice`（本仓库示例），使用下面的命令：

```powershell
python scripts\labeling\batch_eaf_to_h5.py --eaf-dir annotation\eaf --h5-dir data --high-tier voice --low-tier LL --overwrite
```

- 批量脚本会匹配 `annotation/eaf/<basename>.eaf` 到 `data/<basename>.h5`；请确保两者基名一致。
- 若有多个低层 tier，可重复使用 `--low-tier` 参数，例如 `--low-tier LL1 --low-tier LL2`。

### 传感器导入示例

使用下面这些命令，可以按当前命名规则把多模态传感器文件导入到 `data/<basename>.h5` 中：

```powershell
# 手环 CSV
python scripts\sync\import_sensor_csv.py --csv data\wrist\1_wrist.csv --h5 data\1.h5 --sensor wrist

# RTDE 机器人 CSV
python scripts\sync\import_sensor_csv.py --csv data\robot\1_rtde.csv --h5 data\1.h5 --sensor robot

# 眼动 CSV
python scripts\sync\import_sensor_csv.py --csv data\eye\1_eyetracker.csv --h5 data\1.h5 --sensor eye

# 力传感器 CSV
python scripts\sync\import_sensor_csv.py --csv data\force\1_force.csv --h5 data\1.h5 --sensor force

# 音频（人声 / 环境）
python scripts\sync\import_audio.py --basename 1 --kind people --h5 data\1.h5 --timestamps
python scripts\sync\import_audio.py --basename 1 --kind environment --h5 data\1.h5 --timestamps

# 视频（cam1 / cam2 / cam3）
# 推荐只使用 `--timestamps` 让脚本自动探测帧率与帧数，避免手工填写错误值：
python scripts\sync\import_video.py --basename 1 --camera cam1 --h5 data\1.h5 --timestamps
python scripts\sync\import_video.py --basename 1 --camera cam2 --h5 data\1.h5 --timestamps
python scripts\sync\import_video.py --basename 1 --camera cam3 --h5 data\1.h5 --timestamps
```

如果你不想手动填写视频帧率和帧数，也可以只加 `--timestamps`，脚本会尝试从 MP4 文件本身自动读取这些元数据。若某些较晚的片段里视频样本数为 0，通常表示该相机的视频时长本来就没有覆盖到这些片段，例如 30 FPS、1200 帧的视频只有约 40 秒。

### 一键导入 + 同步

如果某条录制的文件已经遵循当前命名规则，就可以用一条命令跑完整流程：

```powershell
python scripts\sync\run_multisensor_pipeline.py --basename 1 --h5 data\1.h5

注意：不要为 `--video-frame-rate`/`--video-num-frames` 传入错误的常量值。优先让 `import_video.py` 使用 `--timestamps` 自动探测（脚本会在探测到的视频文件上读取真实的帧率和帧数，并优先使用探测值以避免写入不正确的持续时长）。如果确实需要手工覆盖，请在确认来源可靠时再使用这些选项。
```

这条命令会做什么：

- 如果存在 wrist、robot、eye、force 的 CSV 文件，就会自动导入
- 如果存在 `data/audio_people/<basename>.wav` 和 `data/audio_environment/<basename>.wav`，就会自动导入
- 当你提供视频元数据时，会导入 `data/videos/<basename>_cam1.mp4`、`<basename>_cam2.mp4` 和 `<basename>_cam3.mp4`
- 最后会自动运行 `align_segments.py`

如果你只想导入已有数据并跳过视频，可以省略视频元数据参数，或者直接添加 `--skip-videos`。

### 批量导入 + 同步

如果你想一次处理 `annotation/eaf/` 下的所有录制，可以使用批量运行脚本。它会自动发现像 `1`、`2` 这样的基名，以及未来新增的 `.eaf` 文件，先把每个标注转换为 HDF5，再运行多模态流水线。

```powershell
python scripts\sync\run_multisensor_batch.py --high-tier HL --low-tier LL --skip-videos
```

如果你的 ELAN tier 命名和示例不同，请把 `--high-tier` 和 `--low-tier` 改成与你文件匹配的名称：

```powershell
python scripts\sync\run_multisensor_batch.py --high-tier voice --low-tier LL --skip-videos
```

常用选项：

- `--basenames 1 2`：只处理指定的录制
- `--continue-on-error`：某个基名失败时继续处理后面的任务
- 去掉 `--skip-videos`，并提供 `--video-frame-rate` / `--video-num-frames`，即可同时导入视频

### 时间同步归档（图片里那种格式）

如果你更希望使用一个单独的 HDF5 文件来保存原始流和各流时间戳（也就是参考图片中的格式），可以使用新的 `build_timesync_h5.py` 脚本。它会生成类似 `data/<basename>_timesync.h5` 的文件，根级分组包含 `/wrist`、`/robot_state`、`/eye`、`/force`、`/audio_people`、`/cam1` 等，另外还有一个 `/timestamps` 组用于记录每条流的时间轴。

示例：

```powershell
python scripts\sync\build_timesync_h5.py --basename 2 --video-frame-rate 30 --video-num-frames 1200
```

说明：

- 该归档会为每条流保存 `timestamps` 数据集，并在适用时保存原始 `records`。
- `robot_state` 的 `timestamps` 同样基于 `pc_timestamp` 归一化后写入，因此可以直接和片段时间对齐。
- 视频帧率和帧数同样会优先自动探测；如果后面片段的 `cam1` / `cam2` / `cam3` 样本数为 0，通常是因为视频文件本身的时长没有覆盖到那些片段。
- 它不会生成片段级的 `aligned` 索引；如果你需要基于标注的对齐，请使用 `run_multisensor_pipeline.py` + `align_segments.py`。
- 文件属性 `layout="time_sync_archive"` 用于标记这种格式。


## 说明

- ELAN 时间戳以毫秒存储；脚本会在写入 HDF5 时将其转换为秒。
- 请保持 tier 名称与 ELAN 文件中的命名一致。
- 尽量不要提交体积很大的原始传感器文件；更推荐存放在 Git 之外或使用 LFS。

## 文档

- [Git 使用入门指南](GIT_GUIDE.md)

**进展**

 - **已完成**: 添加 [GIT_GUIDE.md](GIT_GUIDE.md)（Git 使用入门指南）
 - **已完成**: 增强 `scripts/labeling/eaf_to_h5.py` 的容错与提示（当指定 tier 不存在时列出可用 tiers）
 - **已完成**: 添加同步检查脚本 `scripts/sync/inspect_h5_timestamps.py`，用于列出 HDF5 中可用的时间戳数据集
 - **已完成**: 添加 `scripts/sync/run_multisensor_pipeline.py`，实现单条记录的自动导入 + 对齐
 - **已完成**: 添加 `scripts/sync/run_multisensor_batch.py`，实现批量处理 `1`、`2` 及后续更多 basename
 - **已完成**: `force` 文件支持 `.csv` 和 `.xlsx`，并兼容 `openpyxl`
 - **已完成**: 实际跑通 `1` 和 `2` 两条记录，`data/1.h5` 与 `data/2.h5` 均已生成对齐结果

**当前成果**

 - **标注转换**: `annotation/eaf/<basename>.eaf` → `data/<basename>.h5` 的 `segments_info`
 - **多模态导入**: `wrist`、`robot`、`eye`、`force`、`audio_people`、`audio_environment` 已接入同一条流水线
 - **同步对齐**: `align_segments.py` 会把每个 segment 对应的传感器索引写回 HDF5
 - **批量处理**: `run_multisensor_batch.py` 会自动发现 `annotation/eaf/*.eaf` 并逐个执行转换 + 导入 + 对齐

**推荐执行顺序**

1. 确认依赖已安装：`pympi-ling`、`openpyxl`、`h5py`、`numpy`、`pandas`
2. 先处理单条记录验证流程，例如 `basename=2`
3. 再执行批处理，统一跑完 `1`、`2` 和后续新增记录
4. 如需视频同步，再补充 `--video-frame-rate` 和 `--video-num-frames`

**已验证命令**

 - `python scripts\sync\run_multisensor_batch.py --basenames 2 --high-tier voice --low-tier LL --skip-videos`
 - `python scripts\sync\run_multisensor_batch.py --high-tier voice --low-tier LL --skip-videos`
- **已完成**: 增强 `scripts/labeling/eaf_to_h5.py` 的容错与提示（当指定 tier 不存在时列出可用 tiers）
- **已完成**: 添加同步检查脚本 `scripts/sync/inspect_h5_timestamps.py`，用于列出 HDF5 中可用的时间戳数据集
- **已完成**: 添加 `scripts/sync/run_multisensor_pipeline.py`，实现单条记录的自动导入 + 对齐
- **已完成**: 添加 `scripts/sync/run_multisensor_batch.py`，实现批量处理 `1`、`2` 及后续更多 basename
- **已完成**: `force` 文件支持 `.csv` 和 `.xlsx`，并兼容 `openpyxl`
- **已完成**: 实际跑通 `1` 和 `2` 两条记录，`data/1.h5` 与 `data/2.h5` 均已生成对齐结果

**当前成果**

- **标注转换**: `annotation/eaf/<basename>.eaf` → `data/<basename>.h5` 的 `segments_info`
- **多模态导入**: `wrist`、`robot`、`eye`、`force`、`audio_people`、`audio_environment` 已接入同一条流水线
- **同步对齐**: `align_segments.py` 会把每个 segment 对应的传感器索引写回 HDF5
- **批量处理**: `run_multisensor_batch.py` 会自动发现 `annotation/eaf/*.eaf` 并逐个执行转换 + 导入 + 对齐

**推荐执行顺序**

1. 确认依赖已安装：`pympi-ling`、`openpyxl`、`h5py`、`numpy`、`pandas`
2. 先处理单条记录验证流程，例如 `basename=2`
3. 再执行批处理，统一跑完 `1`、`2` 和后续新增记录
4. 如需视频同步，再补充 `--video-frame-rate` 和 `--video-num-frames`

**已验证命令**

- `python scripts\sync\run_multisensor_batch.py --basenames 2 --high-tier voice --low-tier LL --skip-videos`
- `python scripts\sync\run_multisensor_batch.py --high-tier voice --low-tier LL --skip-videos`
