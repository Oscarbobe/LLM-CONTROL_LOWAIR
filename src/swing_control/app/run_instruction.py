"""Full text-instruction pipeline: parse, validate, dry-run, and optionally execute."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from swing_control.app.dry_run_actions import print_steps
from swing_control.flight.swing_action_executor import SwingActionExecutor
from swing_control.logging_utils import JsonlRunLogger
from swing_control.nlp.instruction_parser import DEFAULT_MODEL, parse_instruction
from swing_control.planning.action_planner import plan_actions
from swing_control.safety.action_validator import validate_action_sequence
from swing_control.safety.manual_confirmation import request_manual_confirmation


DEFAULT_ADDR = os.environ.get("SWING_ADDR", "E0:14:89:09:3D:CB")
DEFAULT_ACTION_OUTPUT = Path("data/processed/instructions/last_actions.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the complete Swing text-control pipeline.")
    parser.add_argument("instruction", help="Chinese flight instruction.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name.")
    parser.add_argument("--execute", action="store_true", help="Execute on a real Swing after validation and confirmation.")
    parser.add_argument("--addr", default=DEFAULT_ADDR, help="Parrot Swing BLE address. Used only with --execute.")
    parser.add_argument("--retries", type=int, default=3, help="Connection retry count.")
    parser.add_argument("--save-actions", default=str(DEFAULT_ACTION_OUTPUT), help="Where to save parsed action JSON.")
    parser.add_argument("--log-dir", default="data/logs", help="Directory for JSONL run logs.")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL run logging.")
    args = parser.parse_args()

    logger = None if args.no_log else JsonlRunLogger(args.log_dir, run_type="instruction_pipeline")
    if logger:
        logger.log("instruction_received", instruction=args.instruction, model=args.model, execute=args.execute)

    parsed = parse_instruction(args.instruction, model=args.model)
    if logger:
        logger.log("instruction_parsed", result=parsed)

    print("模型：", args.model)
    print("模型原始输出：")
    print(parsed.raw_output)

    if not parsed.ok:
        print("解析失败：", parsed.error)
        if logger:
            logger.finish(1, status="parse_failed", error=parsed.error)
            print("日志文件：", logger.path)
        return 1

    output_path = Path(args.save_actions)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(parsed.actions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if logger:
        logger.log("actions_saved", path=output_path, actions=parsed.actions)

    print("\n动作 JSON：")
    print(json.dumps(parsed.actions, indent=2, ensure_ascii=False))
    print("动作文件：", output_path)

    validation = validate_action_sequence(parsed.actions)
    if logger:
        logger.log("validation_result", result=validation)

    print("\n校验结果：", "通过" if validation.ok else "失败")
    if validation.errors:
        for error in validation.errors:
            print(f"- {error}")
        if logger:
            logger.finish(2, status="validation_failed", errors=validation.errors)
            print("日志文件：", logger.path)
        return 2

    steps = plan_actions(parsed.actions)
    if logger:
        logger.log("planned_steps", steps=steps)
    print_steps(steps)

    if not args.execute:
        print("\n当前为 dry-run：未连接无人机，未执行飞行动作。")
        if logger:
            logger.finish(0, status="dry_run_done")
            print("日志文件：", logger.path)
        return 0

    if validation.require_manual_confirm:
        confirmation = request_manual_confirmation(step.description for step in steps)
        if logger:
            logger.log("manual_confirmation", result=confirmation)
        print("确认结果：", confirmation.message)
        if not confirmation.confirmed:
            if logger:
                logger.finish(3, status="manual_confirmation_rejected")
                print("日志文件：", logger.path)
            return 3

    executor = SwingActionExecutor(args.addr, retries=args.retries, logger=logger)
    result = executor.execute(parsed.actions, validate=False)
    print("执行结果：", "成功" if result.ok else "失败")
    if result.executed_tools:
        print("已执行工具：", ", ".join(result.executed_tools))
    if result.errors:
        for error in result.errors:
            print(f"- {error}")
    if logger:
        logger.finish(0 if result.ok else 4, status="execution_done" if result.ok else "execution_failed", result=result)
        print("日志文件：", logger.path)
    return 0 if result.ok else 4


if __name__ == "__main__":
    raise SystemExit(main())
