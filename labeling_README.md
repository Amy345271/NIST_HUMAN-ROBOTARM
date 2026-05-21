# Labeling and conversion utilities

Use `scripts/labeling/eaf_to_h5.py` to convert a single ELAN `.eaf` annotation file into HDF5 `segments_info`.

Use `scripts/labeling/batch_eaf_to_h5.py` to convert all `.eaf` files in `annotation/eaf/` when matching `.h5` files exist in a data directory.

Example:

```powershell
python scripts\labeling\eaf_to_h5.py --eaf annotation\eaf\1.eaf --h5 data\1.h5 --high-tier HL --low-tier LL --overwrite
```

Batch example:

```powershell
python scripts\labeling\batch_eaf_to_h5.py --eaf-dir annotation\eaf --h5-dir data --high-tier HL --low-tier LL --overwrite
```

Notes:

- ELAN times are in milliseconds; the scripts convert them to seconds for HDF5.
- Ensure tier names exactly match your ELAN tiers.
- After conversion, use `scripts/sync/sync_sensors_template.py` as a starting point to align sensor data per segment.
Labeling and conversion utilities

Use `scripts/labeling/eaf_to_h5.py` to convert ELAN .eaf annotations into HDF5 `segments_info`.

Example:

python scripts/labeling/eaf_to_h5.py --eaf annotations.eaf --h5 recordings/2025-01-01-12-00-00.h5 --high-tier HL --low-tier LL --overwrite

Notes:
- ELAN times are in milliseconds; the script converts to seconds for HDF5.
- Ensure tier names exactly match your ELAN tiers.
- After conversion, use `scripts/sync/sync_sensors_template.py` as a starting point to align sensor data per segment.
