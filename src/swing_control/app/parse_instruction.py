"""CLI entry point for parsing Chinese instructions into Swing action JSON."""

from __future__ import annotations

import argparse
import json

from swing_control.app.dry_run_actions import print_steps
from swing_control.logging_utils import JsonlRunLogger
from swing_control.nlp.instruction_parser import DEFAULT_MODEL, parse_instruction
from swing_control.planning.action_planner import plan_actions
from swing_control.safety.action_validator import validate_action_sequence


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse a Chinese instruction into Swing action JSON.")
    parser.add_argument("instruction", help="Chinese flight instruction.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print pyparrot preview.")
    parser.add_argument("--log-dir", default="data/logs", help="Directory for JSONL run logs.")
    parser.add_argument("--no-log", action="store_true", help="Disable JSONL run logging.")
    args = parser.parse_args()

    logger = None if args.no_log else JsonlRunLogger(args.log_dir, run_type="parse_instruction")
    if logger:
        logger.log("instruction_received", instruction=args.instruction, model=args.model)

    parsed = parse_instruction(args.instruction, model=args.model)
    if logger:
        logger.log("instruction_parsed", result=parsed)

    print("模型原始输出：")
    print(parsed.raw_output)

    if not parsed.ok:
        print("解析失败：", parsed.error)
        if logger:
            logger.finish(1, status="parse_failed", error=parsed.error)
            print("日志文件：", logger.path)
        return 1

    print("\n动作 JSON：")
    print(json.dumps(parsed.actions, indent=2, ensure_ascii=False))

    if args.dry_run:
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

    if logger:
        logger.finish(0, status="parse_done")
        print("日志文件：", logger.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

