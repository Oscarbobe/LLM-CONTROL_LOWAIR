"""Dry-run a Swing action JSON sequence without connecting to the drone."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swing_control.logging_utils import JsonlRunLogger
from swing_control.planning.action_planner import PlannedStep, plan_actions
from swing_control.safety.manual_confirmation import request_manual_confirmation
from swing_control.safety.action_validator import validate_action_sequence


DEMO_ACTIONS = [
    {"tool": "pre_flight_check", "parameters": {}},
    {"tool": "takeoff", "parameters": {"duration_s": 5}},
    {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}},
    {"tool": "land", "parameters": {"duration_s": 5}},
]


def load_actions(args: argparse.Namespace) -> Any:
    if args.demo:
        return DEMO_ACTIONS

    if args.file:
        return json.loads(Path(args.file).read_text(encoding="utf-8"))

    if args.json:
        return json.loads(args.json)

    raise SystemExit("请使用 --demo、--json 或 --file 提供动作序列")


def print_steps(steps: list[PlannedStep]) -> None:
    print("\nDry-run 动作序列：")
    for step in steps:
        print(f"{step.index}. {step.description}")
        print(f"   tool: {step.tool}")
        print(f"   pyparrot: {step.pyparrot_preview}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run validated Swing actions.")
    parser.add_argument("--demo", action="store_true", help="Run a built-in demo action sequence.")
    parser.add_argument("--json", help="Action sequence JSON string.")
    parser.add_argument("--file", help="Path to an action sequence JSON file.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Ask for manual confirmation after dry-run output. This still does not execute the drone.",
    )
    parser.add_argument("--log-dir", default="data/logs", help="Directory for JSONL run logs.")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL run logging.")
    args = parser.parse_args()

    logger = None if args.no_log else JsonlRunLogger(args.log_dir, run_type="dry_run")
    actions = load_actions(args)
    if logger:
        logger.log(
            "actions_loaded",
            actions=actions,
            source_demo=args.demo,
            source_file=args.file,
            source_json=bool(args.json),
        )

    result = validate_action_sequence(actions)
    if logger:
        logger.log("validation_result", result=result)

    print("校验结果：", "通过" if result.ok else "失败")
    if result.errors:
        print("\n错误：")
        for error in result.errors:
            print(f"- {error}")

    if result.warnings:
        print("\n警告：")
        for warning in result.warnings:
            print(f"- {warning}")

    print("需要人工确认：", "是" if result.require_manual_confirm else "否")

    if not result.ok:
        if logger:
            logger.finish(1, status="validation_failed", errors=result.errors)
            print("日志文件：", logger.path)
        return 1

    steps = plan_actions(actions)
    if logger:
        logger.log("planned_steps", steps=steps)
    print_steps(steps)

    if args.confirm and result.require_manual_confirm:
        confirmation = request_manual_confirmation(step.description for step in steps)
        if logger:
            logger.log("manual_confirmation", result=confirmation)
        print("确认结果：", confirmation.message)
        if not confirmation.confirmed:
            if logger:
                logger.finish(2, status="manual_confirmation_rejected")
                print("日志文件：", logger.path)
            return 2

    if logger:
        logger.finish(0, status="dry_run_done")
        print("日志文件：", logger.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
