"""Microphone voice-control loop for Parrot Swing."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

from swing_control.app.interactive_control import (
    DEFAULT_ADDR,
    EXIT_WORDS,
    handle_instruction,
    print_help,
)
from swing_control.asr.microphone import make_audio_path, record_microphone
from swing_control.asr.transcriber import transcribe_audio
from swing_control.logging_utils import JsonlRunLogger
from swing_control.nlp.instruction_parser import DEFAULT_MODEL


SPOKEN_REPLACEMENTS = {
    "，": " ",
    ",": " ",
    "。": " ",
    "、": " ",
    "起飛": "起飞",
    "飛": "飞",
    "兩": "两",
    "後": "后",
    "轉": "转",
    "著陸": "着陆",
    "玄廳": "悬停",
    "玄停": "悬停",
    "悬厅": "悬停",
    "懸停": "悬停",
    "懸廳": "悬停",
    "停兩秒": "停两秒",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Voice control Parrot Swing through microphone speech.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name for command parsing.")
    parser.add_argument("--execute", action="store_true", help="Execute each confirmed voice instruction on a real Swing.")
    parser.add_argument("--addr", default=DEFAULT_ADDR, help="Parrot Swing BLE address. Used only with --execute.")
    parser.add_argument("--retries", type=int, default=3, help="Connection retry count for each execution.")
    parser.add_argument("--record-seconds", type=float, default=4.0, help="Microphone recording duration per command.")
    parser.add_argument("--audio-dir", default="data/raw/audio", help="Directory for recorded wav files.")
    parser.add_argument("--audio-device", default=os.environ.get("SWING_AUDIO_DEVICE", "default"), help="arecord/ffmpeg audio device.")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Recording sample rate.")
    parser.add_argument("--asr-backend", default="auto", choices=("auto", "whisper", "whisper-cli"), help="Speech-to-text backend.")
    parser.add_argument("--asr-model", default=os.environ.get("SWING_ASR_MODEL", "base"), help="Whisper model name.")
    parser.add_argument("--asr-language", default="zh", help="ASR language code.")
    parser.add_argument("--save-actions", default="data/processed/instructions/voice_last_actions.json", help="Where to save latest action JSON.")
    parser.add_argument("--log-dir", default="data/logs", help="Directory for JSONL session logs.")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL session logging.")
    parser.add_argument("--check-env", action="store_true", help="Check microphone, Whisper, Ollama, and command availability, then exit.")
    args = parser.parse_args()

    if args.check_env:
        return check_voice_environment(args)

    logger = None if args.no_log else JsonlRunLogger(args.log_dir, run_type="voice_control")
    if logger:
        logger.log("voice_session_started", args=vars(args))

    print("Swing 麦克风语音控制")
    print("按 Enter 开始录音；输入 help 查看示例；输入 q 或 退出 结束。")
    print(f"录音时长：{args.record_seconds:g} 秒；ASR：{args.asr_backend}/{args.asr_model}")
    if args.execute:
        print("当前模式：真机执行。每条语音指令预览后仍需输入“确认执行”。")
    else:
        print("当前模式：dry-run。不会连接无人机。")

    exit_code = 0
    turn_index = 0

    try:
        while True:
            command = input("\n按 Enter 录音> ").strip()
            lowered = command.lower()
            if lowered in EXIT_WORDS or command in EXIT_WORDS:
                break
            if lowered in {"help", "?"} or command == "帮助":
                print_help()
                continue
            if command:
                print("未识别的控制输入；按 Enter 开始录音，输入 q 退出。")
                continue

            turn_index += 1
            audio_path = make_audio_path(args.audio_dir)
            print(f"开始录音 {args.record_seconds:g} 秒...")
            recording = record_microphone(
                audio_path,
                seconds=args.record_seconds,
                device=args.audio_device,
                sample_rate=args.sample_rate,
            )
            if logger:
                logger.log("voice_audio_recorded", turn_index=turn_index, result=recording)

            if not recording.ok or recording.path is None:
                print("录音失败：", recording.error)
                exit_code = 1
                continue

            print("音频文件：", recording.path)
            transcription = transcribe_audio(
                recording.path,
                backend=args.asr_backend,
                model=args.asr_model,
                language=args.asr_language,
            )
            if logger:
                logger.log("voice_transcription_result", turn_index=turn_index, result=transcription, audio_path=recording.path)

            if not transcription.ok:
                print("语音识别失败：", transcription.error)
                print("提示：安装 openai-whisper 后再试：python -m pip install openai-whisper")
                exit_code = 1
                continue

            instruction = transcription.text.strip()
            print("识别文本：", instruction)
            if not instruction:
                print("识别文本为空，本轮跳过。")
                continue

            normalized_instruction = normalize_spoken_instruction(instruction)
            if normalized_instruction != instruction:
                print("归一化文本：", normalized_instruction)

            if logger:
                logger.log(
                    "voice_instruction_normalized",
                    turn_index=turn_index,
                    original=instruction,
                    normalized=normalized_instruction,
                )

            ok = handle_instruction(normalized_instruction, args, logger, turn_index)
            if not ok:
                exit_code = 1

    finally:
        if logger:
            logger.finish(exit_code, status="voice_session_done")
            print("日志文件：", logger.path)

    return exit_code


def normalize_spoken_instruction(text: str) -> str:
    """Normalize common Whisper variants before command parsing."""
    normalized = text.strip()
    for old, new in SPOKEN_REPLACEMENTS.items():
        normalized = normalized.replace(old, new)
    return " ".join(normalized.split())


def check_voice_environment(args: argparse.Namespace) -> int:
    print("语音控制环境检查")
    ok = True

    checks = [
        ("arecord", shutil.which("arecord")),
        ("ffmpeg", shutil.which("ffmpeg")),
        ("ollama", shutil.which("ollama")),
        ("whisper 命令", shutil.which("whisper")),
    ]
    for name, path in checks:
        if path:
            print(f"[OK] {name}: {path}")
        else:
            print(f"[缺少] {name}")
            if name in {"ollama"}:
                ok = False

    try:
        import whisper  # type: ignore[import-not-found]

        version = getattr(whisper, "__version__", "unknown")
        print(f"[OK] Python whisper: {version}")
    except Exception as exc:
        print(f"[缺少] Python whisper: {exc}")
        ok = False

    try:
        import torch  # type: ignore[import-not-found]

        cuda = torch.cuda.is_available()
        print(f"[OK] torch: {getattr(torch, '__version__', 'unknown')} cuda={cuda}")
    except Exception as exc:
        print(f"[提示] torch 检查失败: {exc}")

    audio_dir = Path(args.audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] 音频目录: {audio_dir}")
    print(f"[INFO] 录音设备参数: {args.audio_device}")
    print(f"[INFO] Whisper 模型: {args.asr_model}")

    if shutil.which("arecord"):
        completed = subprocess.run(["arecord", "-l"], text=True, capture_output=True, check=False)
        listing = (completed.stdout or completed.stderr or "").strip()
        if listing:
            print("\narecord 设备：")
            print(listing)

    if shutil.which("pactl"):
        completed = subprocess.run(["pactl", "list", "short", "sources"], text=True, capture_output=True, check=False)
        listing = (completed.stdout or completed.stderr or "").strip()
        if listing:
            print("\nPulseAudio/PipeWire sources：")
            print(listing)

    if ok:
        print("\n环境检查通过：可以运行 ./model/run_swing_voice.sh")
        return 0

    print("\n环境检查未通过：请先补齐缺少项。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
