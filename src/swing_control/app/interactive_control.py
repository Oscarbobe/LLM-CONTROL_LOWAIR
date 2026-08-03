"""Interactive Chinese text-control loop for Parrot Swing."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from swing_control.app.dry_run_actions import print_steps
from swing_control.flight.swing_action_executor import SwingActionExecutor
from swing_control.logging_utils import JsonlRunLogger
from swing_control.nlp.instruction_parser import DEFAULT_MODEL, parse_instruction
from swing_control.planning.action_planner import plan_actions
from swing_control.planning.route_planner import plan_route_from_instruction
from swing_control.safety.action_validator import validate_action_sequence
from swing_control.safety.manual_confirmation import request_manual_confirmation


DEFAULT_ADDR = os.environ.get("SWING_ADDR", "E0:14:89:09:3D:CB")
DEFAULT_ACTION_OUTPUT = Path("data/processed/instructions/interactive_last_actions.json")
EXIT_WORDS = {"q", "quit", "exit", "退出", "结束"}
HELP_WORDS = {"help", "帮助", "?"}
AIRBORNE_COMMANDS = {
    "hover",
    "fly_forward",
    "fly_backward",
    "fly_left",
    "fly_right",
    "turn_left",
    "turn_right",
    "fly_up",
    "fly_down",
    "switch_plane_forward",
    "switch_quadricopter",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive Chinese text control for Parrot Swing.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name.")
    parser.add_argument("--execute", action="store_true", help="Execute each confirmed instruction on a real Swing.")
    parser.add_argument("--addr", default=DEFAULT_ADDR, help="Parrot Swing BLE address. Used only with --execute.")
    parser.add_argument("--retries", type=int, default=3, help="Connection retry count for each execution.")
    parser.add_argument("--save-actions", default=str(DEFAULT_ACTION_OUTPUT), help="Where to save the latest parsed action JSON.")
    parser.add_argument("--log-dir", default="data/logs", help="Directory for JSONL session logs.")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL session logging.")
    args = parser.parse_args()

    logger = None if args.no_log else JsonlRunLogger(args.log_dir, run_type="interactive_control")
    if logger:
        logger.log("interactive_session_started", model=args.model, execute=args.execute, addr=args.addr)

    print("Swing 中文交互控制")
    print("输入中文飞行指令；输入 help 查看示例；输入 q 或 退出 结束。")
    if args.execute:
        print("当前模式：真机执行。每条动作预览后仍需输入“确认执行”。")
    else:
        print("当前模式：dry-run。不会连接无人机。")

    exit_code = 0
    turn_index = 0

    try:
        while True:
            try:
                instruction = input("\n飞行指令> ").strip()
            except EOFError:
                print()
                break

            if not instruction:
                continue

            lowered = instruction.lower()
            if lowered in EXIT_WORDS or instruction in EXIT_WORDS:
                break

            if lowered in HELP_WORDS or instruction in HELP_WORDS:
                print_help()
                continue

            turn_index += 1
            ok = handle_instruction(instruction, args, logger, turn_index)
            if not ok:
                exit_code = 1

    finally:
        if logger:
            logger.finish(exit_code, status="interactive_session_done")
            print("日志文件：", logger.path)

    return exit_code


def handle_instruction(
    instruction: str,
    args: argparse.Namespace,
    logger: JsonlRunLogger | None,
    turn_index: int,
) -> bool:
    if logger:
        logger.log("interactive_instruction_received", turn_index=turn_index, instruction=instruction)

    parsed = parse_instruction(instruction, model=args.model)
    route_result = plan_route_from_instruction(instruction)
    if logger:
        logger.log("interactive_instruction_parsed", turn_index=turn_index, result=parsed)
        logger.log("interactive_route_planned", turn_index=turn_index, result=route_result)

    print("模型：", args.model)
    print("模型原始输出：")
    print(parsed.raw_output)

    if route_result.ok:
        print("地图目标：", route_result.target_area)
        for warning in route_result.warnings:
            print("地图警告：", warning)

    if not parsed.ok:
        print("解析失败：", parsed.error)
        if logger:
            logger.log("interactive_parse_failed", turn_index=turn_index, error=parsed.error)
        return False

    actions, notes = normalize_interactive_actions(parsed.actions)
    for note in notes:
        print("交互补全：", note)

    output_path = Path(args.save_actions)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(actions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if logger:
        logger.log("interactive_actions_saved", turn_index=turn_index, path=output_path, actions=actions, notes=notes)

    print("\n动作 JSON：")
    print(json.dumps(actions, indent=2, ensure_ascii=False))
    print("动作文件：", output_path)

    validation = validate_action_sequence(actions)
    if logger:
        logger.log("interactive_validation_result", turn_index=turn_index, result=validation)

    print("\n校验结果：", "通过" if validation.ok else "失败")
    if validation.errors:
        for error in validation.errors:
            print(f"- {error}")
        return False

    if validation.warnings:
        for warning in validation.warnings:
            print("警告：", warning)

    steps = plan_actions(actions)
    if logger:
        logger.log("interactive_planned_steps", turn_index=turn_index, steps=steps)
    print_steps(steps)

    if not args.execute:
        print("\n当前为 dry-run：未连接无人机，未执行飞行动作。")
        return True

    if validation.require_manual_confirm:
        confirmation = request_manual_confirmation(step.description for step in steps)
        if logger:
            logger.log("interactive_manual_confirmation", turn_index=turn_index, result=confirmation)
        print("确认结果：", confirmation.message)
        if not confirmation.confirmed:
            return False

    executor = SwingActionExecutor(args.addr, retries=args.retries, logger=logger)
    result = executor.execute(actions, validate=False)
    print("执行结果：", "成功" if result.ok else "失败")
    if result.executed_tools:
        print("已执行工具：", ", ".join(result.executed_tools))
    if result.errors:
        for error in result.errors:
            print(f"- {error}")
    if logger:
        logger.log("interactive_execution_result", turn_index=turn_index, result=result)
    return result.ok


def normalize_interactive_actions(actions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Make short interactive commands self-contained while keeping confirmation mandatory."""
    if any(action.get("tool") == "error" for action in actions):
        return actions, []

    tools = [action.get("tool") for action in actions]
    needs_airborne = any(tool in AIRBORNE_COMMANDS for tool in tools)
    has_takeoff = "takeoff" in tools
    has_land = "land" in tools
    normalized = [dict(action) for action in actions]
    notes: list[str] = []

    if needs_airborne and not has_takeoff:
        prefix = []
        if "pre_flight_check" not in tools:
            prefix.append({"tool": "pre_flight_check", "parameters": {}})
        prefix.append({"tool": "takeoff", "parameters": {"duration_s": 5}})
        normalized = prefix + normalized
        has_takeoff = True
        notes.append("检测到空中动作但未包含起飞，已补充起飞前检查和安全起飞。")

    if has_takeoff and not has_land:
        normalized.append({"tool": "land", "parameters": {"duration_s": 5}})
        notes.append("检测到动作序列未包含降落，已补充安全降落。")

    return normalized, notes


def print_help() -> None:
    print(
        """
示例：
  起飞后悬停2秒再降落
  起飞后向前飞1秒再降落
  向左飞1秒
  右转1秒
  上升1秒

说明：
  dry-run 模式只展示动作 JSON 和 pyparrot 预览。
  真机模式下，每条指令执行前都必须输入：确认执行
  输入 q 或 退出 结束交互。
""".strip()
    )


if __name__ == "__main__":
    raise SystemExit(main())
