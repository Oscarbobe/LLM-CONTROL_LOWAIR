"""Speech-to-text backends for recorded voice commands."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TranscriptionResult:
    ok: bool
    text: str = ""
    backend: str | None = None
    error: str | None = None


def transcribe_audio(
    audio_path: str | Path,
    *,
    backend: str = "auto",
    model: str = "base",
    language: str = "zh",
) -> TranscriptionResult:
    """Transcribe a wav file to text."""
    path = Path(audio_path)
    if not path.exists():
        return TranscriptionResult(False, backend=backend, error=f"音频文件不存在: {path}")

    errors: list[str] = []
    if backend in {"auto", "whisper"}:
        result = _transcribe_with_python_whisper(path, model=model, language=language)
        if result.ok or backend == "whisper":
            return result
        if result.error:
            errors.append(f"Python whisper: {result.error}")

    if backend in {"auto", "whisper-cli"}:
        result = _transcribe_with_whisper_cli(path, model=model, language=language)
        if result.ok or backend == "whisper-cli":
            return result
        if result.error:
            errors.append(f"whisper 命令: {result.error}")

    if errors and all("未识别到有效文本" in error for error in errors):
        return TranscriptionResult(
            False,
            backend=backend,
            error="ASR 已可用，但本段录音没有识别到有效文本。请靠近麦克风、提高音量，或增加 --record-seconds。",
        )

    return TranscriptionResult(
        False,
        backend=backend,
        error="没有可用 ASR 后端或 ASR 执行失败：" + "; ".join(errors),
    )


def _transcribe_with_python_whisper(path: Path, *, model: str, language: str) -> TranscriptionResult:
    try:
        import whisper  # type: ignore[import-not-found]
    except Exception as exc:
        return TranscriptionResult(False, backend="whisper", error=f"Python whisper 不可用: {exc}")

    try:
        loaded = whisper.load_model(model)
        result = loaded.transcribe(str(path), language=language, fp16=False)
    except Exception as exc:
        return TranscriptionResult(False, backend="whisper", error=f"Whisper 转写失败: {exc}")

    text = str(result.get("text", "")).strip()
    if not text:
        return TranscriptionResult(False, backend="whisper", error="Whisper 未识别到有效文本")
    return TranscriptionResult(True, text=text, backend="whisper")


def _transcribe_with_whisper_cli(path: Path, *, model: str, language: str) -> TranscriptionResult:
    if not shutil.which("whisper"):
        return TranscriptionResult(False, backend="whisper-cli", error="未找到 whisper 命令")

    cmd = [
        "whisper",
        str(path),
        "--model",
        model,
        "--language",
        language,
        "--fp16",
        "False",
        "--output_format",
        "txt",
        "--output_dir",
        str(path.parent),
    ]
    completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "").strip()
        return TranscriptionResult(False, backend="whisper-cli", error=f"whisper 命令失败: {message}")

    text_path = path.with_suffix(".txt")
    if not text_path.exists():
        return TranscriptionResult(False, backend="whisper-cli", error=f"未找到 whisper 输出: {text_path}")

    text = text_path.read_text(encoding="utf-8").strip()
    if not text:
        return TranscriptionResult(False, backend="whisper-cli", error="whisper 命令未识别到有效文本")
    return TranscriptionResult(True, text=text, backend="whisper-cli")
