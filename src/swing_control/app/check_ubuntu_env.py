"""Check the Ubuntu-side runtime environment for project delivery."""

from __future__ import annotations

import argparse
import importlib.util
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODEL = "qwen3.5:4b"


@dataclass(frozen=True)
class CheckItem:
    name: str
    ok: bool
    detail: str
    required: bool = True


def _module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _run_command(command: list[str], timeout_s: float = 4.0) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)

    output = (completed.stdout or completed.stderr or "").strip()
    return completed.returncode == 0, output


def _ollama_model_available(model: str) -> CheckItem:
    if not _command_exists("ollama"):
        return CheckItem("ollama model", False, "ollama 命令不可用", required=False)

    ok, output = _run_command(["ollama", "list"], timeout_s=6.0)
    if not ok:
        return CheckItem("ollama model", False, output or "ollama list 执行失败", required=False)

    available = any(line.split(maxsplit=1)[0] == model for line in output.splitlines()[1:])
    if available:
        return CheckItem("ollama model", True, f"已安装 {model}", required=False)
    return CheckItem("ollama model", False, f"未在 ollama list 中看到 {model}", required=False)


def collect_checks(model: str = DEFAULT_MODEL) -> list[CheckItem]:
    py_ok = sys.version_info >= (3, 10)
    checks = [
        CheckItem("python", py_ok, f"{platform.python_version()} ({sys.executable})"),
        CheckItem("project root", (PROJECT_ROOT / "src/swing_control").exists(), str(PROJECT_ROOT)),
        CheckItem("site map", (PROJECT_ROOT / "data/maps/site_map.json").exists(), "data/maps/site_map.json"),
        CheckItem("pytest", _module_exists("pytest"), "Python 测试框架"),
        CheckItem("yaml", _module_exists("yaml"), "PyYAML 配置读取"),
        CheckItem("numpy", _module_exists("numpy"), "路径规划/仿真数据辅助"),
        CheckItem("pandas", _module_exists("pandas"), "仿真结果表格处理", required=False),
        CheckItem("scipy", _module_exists("scipy"), "数值仿真辅助", required=False),
        CheckItem("streamlit", _module_exists("streamlit"), "功能展示 Web 面板", required=False),
        CheckItem("ollama python", _module_exists("ollama"), "本地 LLM Python 客户端", required=False),
        CheckItem("ollama cli", _command_exists("ollama"), "本地 LLM 服务命令", required=False),
        _ollama_model_available(model),
        CheckItem("whisper python", _module_exists("whisper"), "openai-whisper 语音识别", required=False),
        CheckItem("whisper cli", _command_exists("whisper"), "whisper 命令行后端", required=False),
        CheckItem("arecord", _command_exists("arecord"), "ALSA 麦克风录音", required=False),
        CheckItem("ffmpeg", _command_exists("ffmpeg"), "音频转码/备用录音", required=False),
        CheckItem("bluepy", _module_exists("bluepy"), "BLE 真机连接", required=False),
        CheckItem("bluetoothctl", _command_exists("bluetoothctl"), "蓝牙控制器管理", required=False),
    ]
    return checks


def print_checks(checks: list[CheckItem]) -> None:
    print("Ubuntu 环境检查：")
    for item in checks:
        marker = "OK" if item.ok else ("MISS" if item.required else "OPTIONAL")
        print(f"- [{marker}] {item.name}: {item.detail}")

    missing_required = [item.name for item in checks if item.required and not item.ok]
    missing_optional = [item.name for item in checks if not item.required and not item.ok]
    print("\n结论：")
    if missing_required:
        print("基础链路不可交付，缺少必需项：", ", ".join(missing_required))
    else:
        print("基础链路可运行：文本解析、地图规划、安全校验和报告生成具备 Ubuntu 运行条件。")

    if missing_optional:
        print("可选能力缺口：", ", ".join(missing_optional))


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Ubuntu-side project dependencies.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Expected Ollama model name.")
    args = parser.parse_args()

    checks = collect_checks(args.model)
    print_checks(checks)
    return 1 if any(item.required and not item.ok for item in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
