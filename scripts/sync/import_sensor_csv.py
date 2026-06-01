#!/usr/bin/env python3
"""Import sensor CSV files using the project's current field names.

Supported presets:
- wrist:  `data/wrist/<basename>_wrist.csv`
- robot:  `data/robot/<basename>_rtde.csv`
- eye:    `data/eye/<basename>_eyetracker.csv`
- force:  `data/force/<basename>_force.csv`

The importer reads the exact source column names from the CSV, stores the
timestamps as `/sensors/<sensor>/timestamps`, and writes the remaining fields
into a structured dataset `/sensors/<sensor>/records` while preserving the
original column names in attributes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import zipfile
from dataclasses import dataclass
from typing import Iterable

import h5py
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SensorSchema:
    time_col: str
    time_scale: float
    keep_cols: tuple[str, ...]


SENSOR_SCHEMAS: dict[str, SensorSchema] = {
    "wrist": SensorSchema(
        time_col="相对时间_秒",
        time_scale=1.0,
        keep_cols=(
            "原始日志时间戳",
            "GSR电压(V)",
            "心率(bpm)",
            "血氧(%)",
            "加速度X(g)",
            "加速度Y(g)",
            "加速度Z(g)",
            "陀螺仪X(°/s)",
            "陀螺仪Y(°/s)",
            "陀螺仪Z(°/s)",
            "校验正确",
        ),
    ),
    "robot": SensorSchema(
        time_col="robot_timestamp",
        time_scale=1.0,
        keep_cols=(
            "robot_timestamp",
            "pc_timestamp",
            "q0",
            "q1",
            "q2",
            "q3",
            "q4",
            "q5",
            "curr0",
            "curr1",
            "curr2",
            "curr3",
            "curr4",
            "curr5",
            "x",
            "y",
            "z",
            "rx",
            "ry",
            "rz",
            "fx",
            "fy",
            "fz",
            "mx",
            "my",
            "mz",
            "gripper_command",
        ),
    ),
    "eye": SensorSchema(
        time_col="session_time_s",
        time_scale=1.0,
        keep_cols=("system_timestamp_us", "raw_timestamp_us", "x_norm", "y_norm", "validity"),
    ),
    "force": SensorSchema(
        time_col="time_ms",
        time_scale=0.001,
        keep_cols=("raw_value", "voltage_V", "force_N"),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a sensor CSV into HDF5")
    parser.add_argument("--csv", required=True, help="Path to the CSV file")
    parser.add_argument("--h5", required=True, help="Target HDF5 file")
    parser.add_argument(
        "--sensor",
        required=True,
        choices=sorted(SENSOR_SCHEMAS.keys()),
        help="Sensor preset to use",
    )
    parser.add_argument(
        "--time-col",
        default=None,
        help="Override the preset time column if your CSV uses a different header",
    )
    parser.add_argument(
        "--drop-missing",
        action="store_true",
        help="Drop rows with missing values before writing to HDF5",
    )
    return parser.parse_args()


def sanitize_name(name: str) -> str:
    sanitized = re.sub(r"[^0-9A-Za-z_\u4e00-\u9fff]+", "_", name)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return sanitized or "field"


def unique_names(names: Iterable[str]) -> list[str]:
    used: set[str] = set()
    result: list[str] = []
    for name in names:
        base = sanitize_name(name)
        candidate = base
        suffix = 1
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        used.add(candidate)
        result.append(candidate)
    return result


def ensure_columns(df: pd.DataFrame, required: Iterable[str], csv_path: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns in {csv_path}: {missing}")


def promote_first_row_to_header_if_needed(df: pd.DataFrame, required: Iterable[str]) -> pd.DataFrame:
    if not len(df.columns):
        return df

    if not all(str(column).startswith("Unnamed") for column in df.columns):
        return df

    if df.empty:
        return df

    header_values = ["" if pd.isna(value) else str(value).strip() for value in df.iloc[0].tolist()]
    if not any(value for value in header_values):
        return df

    promoted = df.iloc[1:].reset_index(drop=True).copy()
    promoted.columns = header_values

    required_set = set(required)
    if required_set.intersection(promoted.columns):
        return promoted

    return df


def read_csv_with_fallback(csv_path: str) -> pd.DataFrame:
    encodings = ("utf-8-sig", "utf-8", "gbk", "gb18030")
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(csv_path, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
        except pd.errors.ParserError:
            last_error = None
            break
    if last_error is not None:
        if zipfile.is_zipfile(csv_path) or csv_path.lower().endswith((".xlsx", ".xlsm", ".xls")):
            return pd.read_excel(csv_path)
        raise last_error

    if zipfile.is_zipfile(csv_path) or csv_path.lower().endswith((".xlsx", ".xlsm", ".xls")):
        return pd.read_excel(csv_path)
    return pd.read_csv(csv_path)


def build_records_dataset(df: pd.DataFrame, columns: list[str]) -> tuple[np.ndarray, dict[str, str]]:
    dtype_fields: list[tuple[str, np.dtype]] = []
    safe_names = unique_names(columns)
    field_map: dict[str, str] = {}

    for original_name, safe_name in zip(columns, safe_names):
        series = df[original_name]
        if pd.api.types.is_bool_dtype(series):
            np_dtype = np.dtype("?")
        elif pd.api.types.is_integer_dtype(series):
            np_dtype = np.dtype("<i8")
        elif pd.api.types.is_float_dtype(series):
            np_dtype = np.dtype("<f8")
        else:
            # Strings or mixed content; keep as UTF-8 fixed-width object via vlen.
            np_dtype = h5py.string_dtype(encoding="utf-8")
        dtype_fields.append((safe_name, np_dtype))
        field_map[original_name] = safe_name

    records = np.empty(len(df), dtype=np.dtype(dtype_fields))
    for original_name, safe_name in field_map.items():
        series = df[original_name]
        if series.dtype == object or pd.api.types.is_string_dtype(series):
            records[safe_name] = series.fillna("").astype(str).to_numpy()
        else:
            # preserve numeric values and let pandas coerce missing cells when possible
            records[safe_name] = series.to_numpy()

    return records, field_map


def extract_timestamps(df: pd.DataFrame, sensor: str, time_col: str, time_scale: float) -> np.ndarray:
    if sensor == "robot":
        timestamps = pd.to_numeric(df["pc_timestamp"], errors="coerce").to_numpy(dtype=float)
        valid = timestamps[~np.isnan(timestamps)]
        if valid.size:
            timestamps = timestamps - valid[0]
        return timestamps

    return pd.to_numeric(df[time_col], errors="coerce").to_numpy(dtype=float) * time_scale


def main() -> None:
    args = parse_args()
    schema = SENSOR_SCHEMAS[args.sensor]

    df = read_csv_with_fallback(args.csv)
    time_col = args.time_col or schema.time_col
    df = promote_first_row_to_header_if_needed(df, [time_col, *schema.keep_cols])
    ensure_columns(df, [time_col, *schema.keep_cols], args.csv)

    if args.drop_missing:
        df = df.dropna(subset=[time_col, *schema.keep_cols]).reset_index(drop=True)

    timestamps = extract_timestamps(df, args.sensor, time_col, schema.time_scale)
    keep_columns = [column for column in schema.keep_cols if column in df.columns]
    records, field_map = build_records_dataset(df, keep_columns)

    with h5py.File(args.h5, "a") as h5_file:
        sensors_group = h5_file.require_group("sensors")
        sensor_group = sensors_group.require_group(args.sensor)

        if "timestamps" in sensor_group:
            del sensor_group["timestamps"]
        if "records" in sensor_group:
            del sensor_group["records"]

        sensor_group.create_dataset("timestamps", data=timestamps, dtype="f8")
        sensor_group.create_dataset("records", data=records)
        sensor_group.attrs["time_col"] = time_col
        sensor_group.attrs["time_scale"] = schema.time_scale
        sensor_group.attrs["source_csv"] = os.path.abspath(args.csv)
        sensor_group.attrs["original_columns"] = json.dumps([time_col, *keep_columns], ensure_ascii=False)
        sensor_group.attrs["field_map"] = json.dumps(field_map, ensure_ascii=False)

    print(f"Imported {len(df)} rows into /sensors/{args.sensor}/ from {args.csv}")


if __name__ == "__main__":
    main()
