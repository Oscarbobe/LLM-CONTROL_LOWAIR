"""Generate a Markdown delivery report from current actions and simulation output."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from swing_control.mapping.site_map import load_site_map
from swing_control.planning.action_planner import plan_actions
from swing_control.safety.action_validator import validate_action_sequence


DEFAULT_ACTIONS = Path("data/processed/instructions/map_last_actions.json")
DEFAULT_MAP = Path("data/maps/site_map.json")
DEFAULT_SIM_RESULT = Path("data/simulation/latest_result.json")
DEFAULT_OUTPUT = Path("data/reports/latest_report.md")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _optional_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return _read_json(path)


def _format_action_rows(actions: list[dict[str, Any]]) -> str:
    rows = ["| 步骤 | 动作 | 参数 | dry-run / pyparrot 预览 |", "|---:|---|---|---|"]
    for step in plan_actions(actions):
        params = json.dumps(step.parameters, ensure_ascii=False)
        rows.append(
            f"| {step.index} | `{step.tool}` | `{params}` | `{step.pyparrot_preview}` |"
        )
    return "\n".join(rows)


def _format_simulation(sim_result: Any | None) -> str:
    if not isinstance(sim_result, dict):
        return "未读取到 `data/simulation/latest_result.json`，请先在 MATLAB/Simulink 中导出结果。"

    ok = "PASS" if sim_result.get("ok") else "FAIL"
    final_pose = sim_result.get("finalPose") or sim_result.get("final_pose")
    total_time = sim_result.get("totalTime") or sim_result.get("total_time_s")
    minimum_clearance = sim_result.get("minimumClearance") or sim_result.get("minimum_clearance_m")
    lines = [f"- 仿真结论：`{ok}`"]
    if total_time is not None:
        lines.append(f"- 总飞行时间：`{total_time}` 秒")
    if final_pose is not None:
        lines.append(f"- 末端位置：`{final_pose}`")
    if minimum_clearance is not None:
        lines.append(f"- 禁飞区最小距离：`{minimum_clearance}` 米")
    return "\n".join(lines)


def build_report(
    *,
    instruction: str,
    actions_path: Path = DEFAULT_ACTIONS,
    map_path: Path = DEFAULT_MAP,
    sim_result_path: Path = DEFAULT_SIM_RESULT,
) -> str:
    actions = _read_json(actions_path)
    validation = validate_action_sequence(actions)
    site_map = load_site_map(map_path)
    sim_result = _optional_json(sim_result_path)

    area_names = "、".join(area.name for area in site_map.areas) or "无"
    zone_names = "、".join(zone.name for zone in site_map.no_fly_zones) or "无"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    validation_text = "通过" if validation.ok else "失败"
    confirm_text = "是" if validation.require_manual_confirm else "否"
    errors = "\n".join(f"- {error}" for error in validation.errors) or "- 无"
    warnings = "\n".join(f"- {warning}" for warning in validation.warnings) or "- 无"

    return f"""# LLM-CONTROL_LOWAIR Ubuntu 交付报告

生成时间：{generated_at}

## 1. 输入指令

{instruction}

## 2. 地图与安全边界

- 地图文件：`{map_path}`
- 地图名称：`{site_map.name}`
- 坐标系：`{site_map.coordinate_system}`
- 可识别目标区域：{area_names}
- 禁飞区：{zone_names}
- 飞行边界：x=[{site_map.limits.min_x}, {site_map.limits.max_x}], y=[{site_map.limits.min_y}, {site_map.limits.max_y}], z=[{site_map.limits.min_z}, {site_map.limits.max_z}]

## 3. 动作校验

- 动作文件：`{actions_path}`
- 校验结果：{validation_text}
- 需要人工确认：{confirm_text}

错误：

{errors}

警告：

{warnings}

## 4. 动作序列与执行预览

{_format_action_rows(actions)}

## 5. MATLAB/Simulink 仿真结果

{_format_simulation(sim_result)}

## 6. Ubuntu 可交付结论

Ubuntu 侧可完成中文指令解析、地图路径规划、动作安全校验、dry-run 预览、语音入口环境检查、日志与报告生成。MATLAB/Simulink GUI 实测建议在 Windows MATLAB 中完成，真机飞行作为可选安全验证。
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Markdown project delivery report.")
    parser.add_argument("--instruction", default="飞到果园上方悬停两秒再降落", help="Instruction shown in the report.")
    parser.add_argument("--actions", default=str(DEFAULT_ACTIONS), help="Action JSON file.")
    parser.add_argument("--map", default=str(DEFAULT_MAP), help="Site map JSON file.")
    parser.add_argument("--sim-result", default=str(DEFAULT_SIM_RESULT), help="Simulation result JSON file.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Markdown output path.")
    args = parser.parse_args()

    output = Path(args.output)
    report = build_report(
        instruction=args.instruction,
        actions_path=Path(args.actions),
        map_path=Path(args.map),
        sim_result_path=Path(args.sim_result),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"交付报告已生成：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
