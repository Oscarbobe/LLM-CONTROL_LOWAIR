"""Execute a validated Swing action JSON sequence on a real drone."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from swing_control.app.dry_run_actions import print_steps
from swing_control.flight.swing_action_executor import SwingActionExecutor
from swing_control.logging_utils import JsonlRunLogger
from swing_control.planning.action_planner import plan_actions
from swing_control.safety.action_validator import validate_action_sequence
from swing_control.safety.manual_confirmation import request_manual_confirmation


def load_actions(args: argparse.Namespace) -> Any:
    if args.file:
        return json.loads(Path(args.file).read_text(encoding="utf-8"))
    if args.json:
        return json.loads(args.json)
    raise SystemExit("请使用 --json 或 --file 提供动作序列")


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute validated Swing actions with pyparrot.")
    parser.add_argument("--addr", required=True, help="Parrot Swing BLE address.")
    parser.add_argument("--json", help="Action sequence JSON string.")
    parser.add_argument("--file", help="Path to an action sequence JSON file.")
    parser.add_argument("--retries", type=int, default=3, help="Connection retry count.")
    parser.add_argument("--log-dir", default="data/logs", help="Directory for JSONL run logs.")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL run logging.")
    args = parser.parse_args()

    logger = None if args.no_log else JsonlRunLogger(args.log_dir, run_type="execute")
    actions = load_actions(args)
    if logger:
        logger.log("actions_loaded", actions=actions, source_file=args.file, source_json=bool(args.json))

    validation = validate_action_sequence(actions)
    if logger:
        logger.log("validation_result", result=validation)

    print("校验结果：", "通过" if validation.ok else "失败")
    if validation.errors:
        for error in validation.errors:
            print(f"- {error}")
        if logger:
            logger.finish(1, status="validation_failed", errors=validation.errors)
            print("日志文件：", logger.path)
        return 1

    steps = plan_actions(actions)
    if logger:
        logger.log("planned_steps", steps=steps)
    print_steps(steps)

    if validation.require_manual_confirm:
        confirmation = request_manual_confirmation(step.description for step in steps)
        if logger:
            logger.log("manual_confirmation", result=confirmation)
        print("确认结果：", confirmation.message)
        if not confirmation.confirmed:
            if logger:
                logger.finish(2, status="manual_confirmation_rejected")
                print("日志文件：", logger.path)
            return 2

    executor = SwingActionExecutor(args.addr, retries=args.retries, logger=logger)
    result = executor.execute(actions, validate=False)
    print("执行结果：", "成功" if result.ok else "失败")
    if result.executed_tools:
        print("已执行工具：", ", ".join(result.executed_tools))
    if result.errors:
        for error in result.errors:
            print(f"- {error}")
    if result.log_path:
        if logger:
            logger.finish(0 if result.ok else 3, status="execution_done" if result.ok else "execution_failed", result=result)
        print("日志文件：", result.log_path)
    return 0 if result.ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
