Labeling and conversion utilities

Use `scripts/labeling/eaf_to_h5.py` to convert ELAN .eaf annotations into HDF5 `segments_info`.

Example:

python scripts/labeling/eaf_to_h5.py --eaf annotations.eaf --h5 recordings/2025-01-01-12-00-00.h5 --high-tier HL --low-tier LL --overwrite

Notes:
- ELAN times are in milliseconds; the script converts to seconds for HDF5.
- Ensure tier names exactly match your ELAN tiers.
- After conversion, use `scripts/sync/sync_sensors_template.py` as a starting point to align sensor data per segment.
