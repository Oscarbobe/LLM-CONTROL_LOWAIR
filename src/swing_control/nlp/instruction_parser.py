"""Parse Chinese flight instructions into Swing action JSON with Ollama."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_MODEL = os.environ.get("SWING_LLM_MODEL", "qwen3.5:4b")

SYSTEM_PROMPT = """
你是 Parrot Swing 无人机自然语言控制规划器。
你的任务是把中文飞行指令转换为 JSON 工具调用序列。
只能使用工具列表中的工具，不允许编造工具。
必须严格输出 JSON 数组，不要输出解释文字。
如果指令危险、超出能力或无法理解，输出 error 工具。

可用工具：
pre_flight_check()
takeoff(duration_s)
land(duration_s)
fly_forward(duration_s, speed)
fly_backward(duration_s, speed)
fly_left(duration_s, speed)
fly_right(duration_s, speed)
turn_left(duration_s, yaw)
turn_right(duration_s, yaw)
fly_up(duration_s, vertical_movement)
fly_down(duration_s, vertical_movement)
hover(duration_s)
switch_plane_forward()
switch_quadricopter()
get_status()
error(message)

安全范围：
duration_s 必须在 0.2 到 5.0 之间。
speed、yaw、vertical_movement 必须在 1 到 30 之间。
包含飞行动作时必须先 takeoff，最后必须 land。
起飞前优先加入 pre_flight_check。

示例：
用户指令：起飞后悬停2秒再降落
输出：
[
  {"tool":"pre_flight_check","parameters":{}},
  {"tool":"takeoff","parameters":{"duration_s":5}},
  {"tool":"hover","parameters":{"duration_s":2}},
  {"tool":"land","parameters":{"duration_s":5}}
]
""".strip()


@dataclass
class ParseResult:
    ok: bool
    actions: list[dict[str, Any]]
    raw_output: str
    error: str | None = None


def parse_instruction(instruction: str, *, model: str = DEFAULT_MODEL) -> ParseResult:
    """Parse one instruction with Ollama and return an action sequence."""
    map_actions = _map_based_parse(instruction)
    if map_actions:
        return ParseResult(True, map_actions, "地图路径规划已启用。")

    prompt = f"{SYSTEM_PROMPT}\n\n用户指令：{instruction}\n输出："
    raw_output = _call_ollama_http(model, prompt)
    if raw_output is None:
        try:
            raw_output = _call_ollama_cli(model, prompt)
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            return ParseResult(False, [], "", f"Ollama 调用失败：{exc}")

    try:
        actions = _extract_json_array(raw_output)
    except ValueError as exc:
        fallback = _rule_based_parse(instruction)
        if fallback:
            return ParseResult(True, fallback, f"{raw_output}\n\n规则兜底解析已启用。")
        return ParseResult(False, [], raw_output, str(exc))

    return ParseResult(True, actions, raw_output)


def _call_ollama_http(model: str, prompt: str) -> str | None:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "think": False,
            "options": {"temperature": 0.1, "num_predict": 300},
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("error"):
                return None
            output = str(data.get("response", "")).strip()
            return output or None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def _call_ollama_cli(model: str, prompt: str) -> str:
    completed = subprocess.run(
        ["ollama", "run", model, prompt],
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end < start:
        raise ValueError("模型输出中没有 JSON 数组")

    payload = text[start : end + 1]
    parsed = json.loads(payload)
    if not isinstance(parsed, list):
        raise ValueError("模型输出不是 JSON 数组")
    if not all(isinstance(item, dict) for item in parsed):
        raise ValueError("JSON 数组元素必须是对象")
    return parsed


def _rule_based_parse(instruction: str) -> list[dict[str, Any]]:
    """Fallback parser for common demo instructions when the local model is weak."""
    text = instruction.strip()
    map_actions = _map_based_parse(text)
    if map_actions:
        return map_actions

    actions: list[dict[str, Any]] = []

    has_takeoff = "起飞" in text
    has_land = "降落" in text or "落地" in text or "着陆" in text

    if has_takeoff:
        actions.append({"tool": "pre_flight_check", "parameters": {}})
        actions.append({"tool": "takeoff", "parameters": {"duration_s": 5}})

    hover_seconds = _extract_seconds(text, ("悬停", "停留", "等待"))
    if hover_seconds is not None:
        actions.append({"tool": "hover", "parameters": {"duration_s": hover_seconds}})

    motion_patterns = [
        (("向前", "前进", "往前"), "fly_forward"),
        (("向后", "后退", "往后"), "fly_backward"),
        (("向左飞", "左移", "往左"), "fly_left"),
        (("向右飞", "右移", "往右"), "fly_right"),
    ]
    for keywords, tool in motion_patterns:
        if any(keyword in text for keyword in keywords):
            actions.append(
                {
                    "tool": tool,
                    "parameters": {"duration_s": _extract_seconds(text, keywords) or 1, "speed": 20},
                }
            )

    if "左转" in text or "向左转" in text:
        actions.append({"tool": "turn_left", "parameters": {"duration_s": _extract_seconds(text, ("左转", "向左转")) or 1, "yaw": 20}})

    if "右转" in text or "向右转" in text:
        actions.append({"tool": "turn_right", "parameters": {"duration_s": _extract_seconds(text, ("右转", "向右转")) or 1, "yaw": 20}})

    if "上升" in text:
        actions.append({"tool": "fly_up", "parameters": {"duration_s": _extract_seconds(text, ("上升",)) or 1, "vertical_movement": 20}})

    if "下降" in text:
        actions.append({"tool": "fly_down", "parameters": {"duration_s": _extract_seconds(text, ("下降",)) or 1, "vertical_movement": 20}})

    if has_land:
        actions.append({"tool": "land", "parameters": {"duration_s": 5}})

    if has_takeoff and not has_land:
        actions.append({"tool": "land", "parameters": {"duration_s": 5}})

    return actions


def _extract_seconds(text: str, keywords: tuple[str, ...]) -> float | None:
    for keyword in keywords:
        pattern = rf"{re.escape(keyword)}[^0-9一二两三四五六七八九十半]*([0-9]+(?:\.[0-9]+)?|半|一|二|两|三|四|五|六|七|八|九|十)\s*秒"
        match = re.search(pattern, text)
        if match:
            return _clamp_duration(_chinese_number_to_float(match.group(1)))
    return None


def _chinese_number_to_float(value: str) -> float:
    mapping = {
        "半": 0.5,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    if value in mapping:
        return float(mapping[value])
    return float(value)


def _clamp_duration(value: float) -> float:
    return max(0.2, min(5.0, value))


def _map_based_parse(instruction: str) -> list[dict[str, Any]]:
    try:
        from swing_control.planning.route_planner import plan_route_from_instruction
    except Exception:
        return []

    try:
        result = plan_route_from_instruction(instruction)
    except Exception:
        return []

    if not result.ok:
        return []
    return result.actions
