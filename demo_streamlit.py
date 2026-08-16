"""Streamlit demo dashboard for LLM-CONTROL_LOWAIR."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from swing_control.app.check_ubuntu_env import collect_checks
from swing_control.app.generate_report import (
    DEFAULT_ACTIONS,
    DEFAULT_MAP,
    DEFAULT_OUTPUT,
    DEFAULT_SIM_RESULT,
    build_report,
)
from swing_control.mapping.site_map import Point3D, load_site_map
from swing_control.nlp.instruction_parser import DEFAULT_MODEL, parse_instruction
from swing_control.planning.action_planner import PlannedStep, plan_actions
from swing_control.planning.route_planner import RoutePlanResult, plan_route_from_instruction
from swing_control.safety.action_validator import ValidationResult, validate_action_sequence


DEFAULT_TEXT_INSTRUCTION = "起飞后悬停2秒再降落"
DEFAULT_MAP_INSTRUCTION = "飞到果园上方悬停两秒再降落"


st.set_page_config(
    page_title="LLM-CONTROL_LOWAIR 功能展示",
    page_icon="A",
    layout="wide",
)


def _write_actions(actions: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(actions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _render_validation(validation: ValidationResult) -> None:
    col_ok, col_confirm, col_errors = st.columns(3)
    col_ok.metric("安全校验", "通过" if validation.ok else "失败")
    col_confirm.metric("需要人工确认", "是" if validation.require_manual_confirm else "否")
    col_errors.metric("错误数量", len(validation.errors))

    if validation.errors:
        st.error("校验错误：\n" + "\n".join(f"- {item}" for item in validation.errors))
    if validation.warnings:
        st.warning("校验警告：\n" + "\n".join(f"- {item}" for item in validation.warnings))


def _steps_dataframe(steps: list[PlannedStep]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "步骤": step.index,
                "动作": step.tool,
                "说明": step.description,
                "pyparrot 预览": step.pyparrot_preview,
            }
            for step in steps
        ]
    )


def _render_actions(actions: list[dict[str, Any]]) -> None:
    validation = validate_action_sequence(actions)
    _render_validation(validation)

    with st.expander("动作 JSON", expanded=True):
        st.json(actions)

    if validation.ok:
        steps = plan_actions(actions)
        st.subheader("Dry-run 动作序列")
        st.dataframe(_steps_dataframe(steps), width="stretch", hide_index=True)


def _map_dataframe() -> pd.DataFrame:
    site_map = load_site_map(DEFAULT_MAP)
    rows: list[dict[str, Any]] = []
    for area in site_map.areas:
        rows.append(
            {
                "类型": "目标区域",
                "名称": area.name,
                "x": area.center.x,
                "y": area.center.y,
                "z": area.center.z,
                "半径": area.radius_m,
                "显示尺寸": max(area.radius_m * 80, 40),
            }
        )
    for zone in site_map.no_fly_zones:
        rows.append(
            {
                "类型": "禁飞区",
                "名称": zone.name,
                "x": zone.center.x,
                "y": zone.center.y,
                "z": zone.center.z,
                "半径": zone.protected_radius_m,
                "显示尺寸": max(zone.protected_radius_m * 90, 50),
            }
        )
    rows.append(
        {
            "类型": "起飞点",
            "名称": site_map.origin.name if hasattr(site_map.origin, "name") else "起飞点",
            "x": site_map.origin.x,
            "y": site_map.origin.y,
            "z": site_map.origin.z,
            "半径": 0.3,
            "显示尺寸": 80,
        }
    )
    return pd.DataFrame(rows)


def _waypoints_dataframe(waypoints: list[Point3D]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"航点": index, "x": point.x, "y": point.y, "z": point.z}
            for index, point in enumerate(waypoints, start=1)
        ]
    )


def _render_map_overview() -> None:
    df = _map_dataframe()
    col_chart, col_table = st.columns([3, 2])
    with col_chart:
        st.scatter_chart(df, x="x", y="y", color="类型", size="显示尺寸", height=360)
    with col_table:
        st.dataframe(df[["类型", "名称", "x", "y", "z", "半径"]], width="stretch", hide_index=True)


def _render_route_result(result: RoutePlanResult, save_path: Path | None = DEFAULT_ACTIONS) -> None:
    if not result.ok:
        st.error("地图规划失败：\n" + "\n".join(f"- {item}" for item in result.errors))
        return

    metric_cols = st.columns(4)
    metric_cols[0].metric("规划状态", "成功")
    metric_cols[1].metric("目标区域", result.target_area or "-")
    metric_cols[2].metric("航点数量", len(result.waypoints))
    metric_cols[3].metric("动作数量", len(result.actions))

    if result.warnings:
        st.info("规划提示：\n" + "\n".join(f"- {item}" for item in result.warnings))

    waypoints_df = _waypoints_dataframe(result.waypoints)
    if not waypoints_df.empty:
        st.subheader("航点预览")
        st.line_chart(waypoints_df, x="航点", y=["x", "y", "z"], height=260)
        st.dataframe(waypoints_df, width="stretch", hide_index=True)

    if save_path is not None:
        _write_actions(result.actions, save_path)
        st.success(f"动作 JSON 已保存：{save_path}")

    _render_actions(result.actions)


def _overview_tab() -> None:
    st.header("项目功能展示")
    st.write("自然语言/语音输入转换为结构化动作，经地图规划和安全校验后，用于 MATLAB/Simulink 仿真或可选真机验证。")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("文本控制", "已接入")
    col2.metric("地图规划", "A* 绕行")
    col3.metric("安全校验", "72 tests")
    col4.metric("真机执行", "可选")

    st.subheader("本地示范地图")
    _render_map_overview()

    st.subheader("推荐演示顺序")
    st.code(
        "\n".join(
            [
                "1. 在“文本控制”输入中文指令，查看动作 JSON 和 dry-run。",
                "2. 在“地图规划”输入目标区域指令，查看航点和禁飞区绕行。",
                "3. 在“交付报告”生成 Markdown 报告。",
                "4. 在“环境检查”确认 Ubuntu 演示环境。真机执行只作为可选验证。",
            ]
        ),
        language="text",
    )


def _text_tab() -> None:
    st.header("文本指令 → 动作 JSON")
    instruction = st.text_input("中文飞行指令", DEFAULT_TEXT_INSTRUCTION)
    model = st.text_input("Ollama 模型", DEFAULT_MODEL)
    save_path = Path(st.text_input("动作保存路径", "data/processed/instructions/last_actions.json"))
    save_actions = st.checkbox("解析成功后保存动作 JSON", value=True)

    if st.button("解析并 dry-run", type="primary"):
        with st.spinner("正在调用本地 LLM / 规则兜底解析..."):
            parsed = parse_instruction(instruction, model=model)

        st.subheader("模型原始输出")
        st.code(parsed.raw_output or parsed.error or "", language="json")

        if not parsed.ok:
            st.error(parsed.error or "解析失败")
            return

        if save_actions:
            _write_actions(parsed.actions, save_path)
            st.success(f"动作 JSON 已保存：{save_path}")

        _render_actions(parsed.actions)


def _map_tab() -> None:
    st.header("地图目标 → 路径规划 → 动作 JSON")
    instruction = st.text_input("地图目标指令", DEFAULT_MAP_INSTRUCTION)
    col_opts = st.columns(3)
    use_astar = col_opts[0].checkbox("启用 A* 绕行", value=True)
    return_to_home = col_opts[1].checkbox("添加返航点", value=False)
    save_path = Path(col_opts[2].text_input("保存路径", str(DEFAULT_ACTIONS)))

    st.subheader("地图区域")
    _render_map_overview()

    if st.button("规划路线并 dry-run", type="primary"):
        with st.spinner("正在进行地图目标识别和路径规划..."):
            result = plan_route_from_instruction(
                instruction,
                map_path=DEFAULT_MAP,
                use_astar=use_astar,
                return_to_home=return_to_home,
            )
        _render_route_result(result, save_path)


def _report_tab() -> None:
    st.header("交付报告")
    instruction = st.text_input("报告输入指令", DEFAULT_MAP_INSTRUCTION)
    actions_path = Path(st.text_input("动作 JSON", str(DEFAULT_ACTIONS)))
    output_path = Path(st.text_input("报告输出路径", str(DEFAULT_OUTPUT)))

    if st.button("生成 / 刷新报告", type="primary"):
        try:
            report = build_report(
                instruction=instruction,
                actions_path=actions_path,
                map_path=DEFAULT_MAP,
                sim_result_path=DEFAULT_SIM_RESULT,
            )
        except FileNotFoundError as exc:
            st.error(f"缺少文件：{exc}")
            return
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        st.success(f"报告已生成：{output_path}")

    if output_path.exists():
        st.download_button(
            "下载 Markdown 报告",
            data=output_path.read_text(encoding="utf-8"),
            file_name=output_path.name,
            mime="text/markdown",
        )
        st.markdown(output_path.read_text(encoding="utf-8"))
    else:
        st.info("还没有生成报告。请先完成地图规划并点击生成报告。")


def _env_tab() -> None:
    st.header("Ubuntu 环境检查")
    if st.button("重新检查环境", type="primary"):
        st.session_state["env_checks"] = collect_checks()

    checks = st.session_state.get("env_checks") or collect_checks()
    df = pd.DataFrame(
        [
            {
                "项目": item.name,
                "状态": "OK" if item.ok else ("必需缺失" if item.required else "可选缺失"),
                "说明": item.detail,
                "必需": "是" if item.required else "否",
            }
            for item in checks
        ]
    )
    st.dataframe(df, width="stretch", hide_index=True)

    missing_required = [item.name for item in checks if item.required and not item.ok]
    if missing_required:
        st.error("基础链路不可交付，缺少：" + "、".join(missing_required))
    else:
        st.success("基础链路可运行。")


def main() -> None:
    st.title("LLM-CONTROL_LOWAIR 功能展示")
    st.caption("文本/语音无人机控制原型：指令解析、地图规划、安全校验、dry-run 和交付报告。")

    tabs = st.tabs(["总览", "文本控制", "地图规划", "交付报告", "环境检查"])
    with tabs[0]:
        _overview_tab()
    with tabs[1]:
        _text_tab()
    with tabs[2]:
        _map_tab()
    with tabs[3]:
        _report_tab()
    with tabs[4]:
        _env_tab()


if __name__ == "__main__":
    main()
