#!/usr/bin/env python3
"""Import audio files using the current directory naming convention.

Expected layout:
- `data/audio_people/<basename>.wav`
- `data/audio_environment/<basename>.wav`

The importer stores data under `/sensors/<sensor>/` and can optionally write
sample-level timestamps for alignment.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import h5py
import numpy as np

try:
    import soundfile as sf
except Exception:
    sf = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import audio into HDF5")
    parser.add_argument("--h5", required=True, help="Target HDF5 file")
    parser.add_argument("--audio", default=None, help="Explicit WAV path; overrides basename/kind resolution")
    parser.add_argument("--basename", default=None, help="Recording basename used with --kind")
    parser.add_argument(
        "--kind",
        choices=("people", "environment"),
        default="people",
        help="Which audio folder to use when --audio is not provided",
    )
    parser.add_argument(
        "--audio-root",
        default="data",
        help="Root folder containing audio_people/ and audio_environment/",
    )
    parser.add_argument(
        "--sensor",
        default=None,
        help="Sensor group name under /sensors/ (defaults to audio_people or audio_environment)",
    )
    parser.add_argument(
        "--timestamps",
        action="store_true",
        help="Write sample-level timestamps for alignment",
    )
    return parser.parse_args()


def resolve_audio_path(args: argparse.Namespace) -> tuple[str, str]:
    if args.audio:
        path = args.audio
        sensor_name = args.sensor or ("audio_people" if "people" in Path(path).parts else "audio_environment")
        return path, sensor_name

    if not args.basename:
        raise SystemExit("Provide either --audio or --basename")

    sensor_name = args.sensor or f"audio_{args.kind}"
    path = os.path.join(args.audio_root, sensor_name, f"{args.basename}.wav")
    return path, sensor_name


def read_audio_info(audio_path: str) -> tuple[int, int]:
    if sf is None:
        import wave

        with wave.open(audio_path, "rb") as wf:
            sample_rate = wf.getframerate()
            num_frames = wf.getnframes()
    else:
        info = sf.info(audio_path)
        sample_rate = int(info.samplerate)
        num_frames = int(info.frames)
    return sample_rate, num_frames


def main() -> None:
    args = parse_args()
    audio_path, sensor_name = resolve_audio_path(args)

    if not os.path.exists(audio_path):
        raise SystemExit(f"Audio file not found: {audio_path}")

    sample_rate, num_frames = read_audio_info(audio_path)

    with h5py.File(args.h5, "a") as h5_file:
        sensors_group = h5_file.require_group("sensors")
        sensor_group = sensors_group.require_group(sensor_name)

        sensor_group.attrs["sample_rate"] = sample_rate
        sensor_group.attrs["num_samples"] = num_frames
        sensor_group.attrs["source_path"] = os.path.abspath(audio_path)

        if "audio_path" in sensor_group:
            del sensor_group["audio_path"]
        sensor_group.create_dataset(
            "audio_path",
            data=os.path.abspath(audio_path),
            dtype=h5py.string_dtype(encoding="utf-8"),
        )

        if args.timestamps:
            timestamps = np.arange(num_frames, dtype=np.float64) / float(sample_rate)
            if "timestamps" in sensor_group:
                del sensor_group["timestamps"]
            sensor_group.create_dataset("timestamps", data=timestamps, dtype="f8")

    print(
        f"Imported {sensor_name}: sample_rate={sample_rate}, frames={num_frames}, path={audio_path}"
    )


if __name__ == '__main__':
    main()
