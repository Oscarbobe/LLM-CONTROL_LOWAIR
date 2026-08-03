"""Convert validated Swing actions into dry-run execution steps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PlannedStep:
    index: int
    tool: str
    description: str
    pyparrot_preview: str
    parameters: dict[str, Any]


def _num(params: dict[str, Any], name: str, default: float = 0.0) -> float:
    return float(params.get(name, default))


def plan_action(action: dict[str, Any], index: int) -> PlannedStep:
    """Convert one validated action into a planned dry-run step."""
    tool = action["tool"]
    params = action.get("parameters", {})

    if tool == "pre_flight_check":
        return PlannedStep(index, tool, "执行起飞前安全检查", "# check bluetooth, battery, area, manual confirmation", params)

    if tool == "get_status":
        return PlannedStep(index, tool, "获取无人机状态", "swing.ask_for_state_update()", params)

    if tool == "takeoff":
        duration = _num(params, "duration_s")
        return PlannedStep(index, tool, f"安全起飞，等待 {duration:g} 秒", f"swing.safe_takeoff({duration:g})", params)

    if tool == "land":
        duration = _num(params, "duration_s")
        return PlannedStep(index, tool, f"安全降落，等待 {duration:g} 秒", f"swing.safe_land({duration:g})", params)

    if tool == "hover":
        duration = _num(params, "duration_s")
        return PlannedStep(index, tool, f"悬停 {duration:g} 秒", f"swing.smart_sleep({duration:g})", params)

    if tool in {"fly_forward", "fly_backward", "fly_left", "fly_right"}:
        duration = _num(params, "duration_s")
        speed = _num(params, "speed")
        roll = 0.0
        pitch = 0.0

        if tool == "fly_forward":
            pitch = speed
            text = "向前飞行"
        elif tool == "fly_backward":
            pitch = -speed
            text = "向后飞行"
        elif tool == "fly_left":
            roll = -speed
            text = "向左飞行"
        else:
            roll = speed
            text = "向右飞行"

        preview = (
            "swing.fly_direct("
            f"roll={roll:g}, pitch={pitch:g}, yaw=0, "
            f"vertical_movement=0, duration={duration:g})"
        )
        return PlannedStep(index, tool, f"{text} {duration:g} 秒，速度参数 {speed:g}", preview, params)

    if tool in {"turn_left", "turn_right"}:
        duration = _num(params, "duration_s")
        yaw = _num(params, "yaw")
        signed_yaw = -yaw if tool == "turn_left" else yaw
        text = "向左转向" if tool == "turn_left" else "向右转向"
        preview = (
            "swing.fly_direct("
            f"roll=0, pitch=0, yaw={signed_yaw:g}, "
            f"vertical_movement=0, duration={duration:g})"
        )
        return PlannedStep(index, tool, f"{text} {duration:g} 秒，yaw 参数 {yaw:g}", preview, params)

    if tool in {"fly_up", "fly_down"}:
        duration = _num(params, "duration_s")
        vertical = _num(params, "vertical_movement")
        signed_vertical = vertical if tool == "fly_up" else -vertical
        text = "上升" if tool == "fly_up" else "下降"
        preview = (
            "swing.fly_direct("
            f"roll=0, pitch=0, yaw=0, "
            f"vertical_movement={signed_vertical:g}, duration={duration:g})"
        )
        return PlannedStep(index, tool, f"{text} {duration:g} 秒，垂直参数 {vertical:g}", preview, params)

    if tool == "switch_plane_forward":
        return PlannedStep(index, tool, "切换到固定翼前飞模式", 'swing.set_flying_mode("plane_forward")', params)

    if tool == "switch_quadricopter":
        return PlannedStep(index, tool, "切换到四旋翼模式", 'swing.set_flying_mode("quadricopter")', params)

    if tool == "error":
        return PlannedStep(index, tool, f"指令错误：{params.get('message', '')}", "# no flight action", params)

    raise ValueError(f"unsupported action tool: {tool}")


def plan_actions(actions: list[dict[str, Any]]) -> list[PlannedStep]:
    """Convert a validated action sequence into dry-run steps."""
    return [plan_action(action, index) for index, action in enumerate(actions, start=1)]

