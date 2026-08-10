"""CLI for testing map target resolution and route planning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from swing_control.app.dry_run_actions import print_steps
from swing_control.planning.action_planner import plan_actions
from swing_control.planning.route_planner import plan_route_from_instruction
from swing_control.safety.action_validator import validate_action_sequence


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan Swing actions from a named map target.")
    parser.add_argument("instruction", help="Chinese instruction containing a map area name.")
    parser.add_argument("--map", default="data/maps/site_map.json", help="Path to site map JSON.")
    parser.add_argument("--save-actions", default=None, help="Save the generated action JSON to a file.")
    args = parser.parse_args()

    result = plan_route_from_instruction(args.instruction, map_path=args.map)
    print("地图路径规划：", "成功" if result.ok else "失败")
    if result.target_area:
        print("目标区域：", result.target_area)
    if result.warnings:
        for warning in result.warnings:
            print("警告：", warning)
    if result.errors:
        for error in result.errors:
            print(f"- {error}")
        return 1

    action_json = json.dumps(result.actions, indent=2, ensure_ascii=False)
    print("\n动作 JSON：")
    print(action_json)

    if args.save_actions:
        save_path = Path(args.save_actions)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(action_json, encoding="utf-8")
        print(f"\n动作已保存到: {save_path}")

    validation = validate_action_sequence(result.actions)
    print("\n校验结果：", "通过" if validation.ok else "失败")
    if validation.errors:
        for error in validation.errors:
            print(f"- {error}")
        return 2

    print_steps(plan_actions(result.actions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
