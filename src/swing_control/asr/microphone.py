"""Microphone recording helpers for voice control."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RecordingResult:
    ok: bool
    path: Path | None = None
    backend: str | None = None
    error: str | None = None


def make_audio_path(audio_dir: str | Path = "data/raw/audio", *, prefix: str = "voice_command") -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = Path(audio_dir) / f"{prefix}_{stamp}.wav"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def record_microphone(
    output_path: str | Path,
    *,
    seconds: float = 4.0,
    device: str = "default",
    sample_rate: int = 16000,
) -> RecordingResult:
    """Record microphone audio to a mono 16 kHz wav file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    if shutil.which("arecord"):
        result = _record_with_arecord(path, seconds=seconds, device=device, sample_rate=sample_rate)
        if result.ok:
            return result
        if result.error:
            errors.append(result.error)

    if shutil.which("ffmpeg"):
        result = _record_with_ffmpeg(path, seconds=seconds, device=device, sample_rate=sample_rate)
        if result.ok:
            return result
        if result.error:
            errors.append(result.error)

    if not errors:
        errors.append("未找到 arecord 或 ffmpeg，无法录音")
    return RecordingResult(False, path=path, error="; ".join(errors))


def _record_with_arecord(
    path: Path,
    *,
    seconds: float,
    device: str,
    sample_rate: int,
) -> RecordingResult:
    cmd = [
        "arecord",
        "-D",
        device,
        "-f",
        "S16_LE",
        "-r",
        str(sample_rate),
        "-c",
        "1",
        "-d",
        str(max(1, int(round(seconds)))),
        str(path),
    ]
    return _run_record_command(cmd, path, "arecord")


def _record_with_ffmpeg(
    path: Path,
    *,
    seconds: float,
    device: str,
    sample_rate: int,
) -> RecordingResult:
    pulse_device = "default" if device == "default" else device
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "pulse",
        "-i",
        pulse_device,
        "-t",
        f"{seconds:g}",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        str(path),
    ]
    return _run_record_command(cmd, path, "ffmpeg")


def _run_record_command(cmd: list[str], path: Path, backend: str) -> RecordingResult:
    try:
        completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    except OSError as exc:
        return RecordingResult(False, path=path, backend=backend, error=f"{backend} 启动失败: {exc}")

    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()
        return RecordingResult(False, path=path, backend=backend, error=f"{backend} 录音失败: {message}")

    if not path.exists() or path.stat().st_size == 0:
        return RecordingResult(False, path=path, backend=backend, error=f"{backend} 未生成有效音频文件")

    return RecordingResult(True, path=path, backend=backend)
