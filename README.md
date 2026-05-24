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
