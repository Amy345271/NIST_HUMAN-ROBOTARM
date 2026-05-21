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

## Notes

- ELAN timestamps are stored in milliseconds; the scripts convert them to seconds for HDF5.
- Keep tier names consistent with your ELAN tiers.
- Avoid committing large raw sensor files unless needed; prefer storing them outside Git or using LFS.
