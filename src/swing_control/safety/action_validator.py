"""Validate Swing action sequences before they reach the flight executor."""

from __future__ import annotations

from dataclasses import dataclass, field
from numbers import Real
from typing import Any


@dataclass(frozen=True)
class ParamRule:
    expected_type: type
    min_value: float | None = None
    max_value: float | None = None


@dataclass(frozen=True)
class ToolRule:
    required_params: tuple[str, ...] = ()
    optional_params: tuple[str, ...] = ()
    param_rules: dict[str, ParamRule] = field(default_factory=dict)
    requires_airborne: bool = False
    is_motion: bool = False
    requires_manual_confirm: bool = False


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    require_manual_confirm: bool = False


DURATION = ParamRule(Real, 0.2, 5.0)
SPEED = ParamRule(Real, 1.0, 30.0)
YAW = ParamRule(Real, 1.0, 30.0)
VERTICAL = ParamRule(Real, 1.0, 30.0)
MESSAGE = ParamRule(str)


TOOL_RULES: dict[str, ToolRule] = {
    "pre_flight_check": ToolRule(),
    "get_status": ToolRule(),
    "takeoff": ToolRule(
        required_params=("duration_s",),
        param_rules={"duration_s": DURATION},
        requires_manual_confirm=True,
    ),
    "land": ToolRule(
        required_params=("duration_s",),
        param_rules={"duration_s": DURATION},
        requires_airborne=True,
    ),
    "hover": ToolRule(
        required_params=("duration_s",),
        param_rules={"duration_s": DURATION},
        requires_airborne=True,
        is_motion=True,
    ),
    "fly_forward": ToolRule(
        required_params=("duration_s", "speed"),
        param_rules={"duration_s": DURATION, "speed": SPEED},
        requires_airborne=True,
        is_motion=True,
        requires_manual_confirm=True,
    ),
    "fly_backward": ToolRule(
        required_params=("duration_s", "speed"),
        param_rules={"duration_s": DURATION, "speed": SPEED},
        requires_airborne=True,
        is_motion=True,
        requires_manual_confirm=True,
    ),
    "fly_left": ToolRule(
        required_params=("duration_s", "speed"),
        param_rules={"duration_s": DURATION, "speed": SPEED},
        requires_airborne=True,
        is_motion=True,
        requires_manual_confirm=True,
    ),
    "fly_right": ToolRule(
        required_params=("duration_s", "speed"),
        param_rules={"duration_s": DURATION, "speed": SPEED},
        requires_airborne=True,
        is_motion=True,
        requires_manual_confirm=True,
    ),
    "turn_left": ToolRule(
        required_params=("duration_s", "yaw"),
        param_rules={"duration_s": DURATION, "yaw": YAW},
        requires_airborne=True,
        is_motion=True,
        requires_manual_confirm=True,
    ),
    "turn_right": ToolRule(
        required_params=("duration_s", "yaw"),
        param_rules={"duration_s": DURATION, "yaw": YAW},
        requires_airborne=True,
        is_motion=True,
        requires_manual_confirm=True,
    ),
    "fly_up": ToolRule(
        required_params=("duration_s", "vertical_movement"),
        param_rules={"duration_s": DURATION, "vertical_movement": VERTICAL},
        requires_airborne=True,
        is_motion=True,
        requires_manual_confirm=True,
    ),
    "fly_down": ToolRule(
        required_params=("duration_s", "vertical_movement"),
        param_rules={"duration_s": DURATION, "vertical_movement": VERTICAL},
        requires_airborne=True,
        is_motion=True,
        requires_manual_confirm=True,
    ),
    "switch_plane_forward": ToolRule(
        requires_airborne=True,
        requires_manual_confirm=True,
    ),
    "switch_quadricopter": ToolRule(
        requires_airborne=True,
        requires_manual_confirm=True,
    ),
    "error": ToolRule(
        required_params=("message",),
        param_rules={"message": MESSAGE},
    ),
}


def validate_action(action: Any, index: int) -> list[str]:
    """Validate one action object and return error messages."""
    prefix = f"第{index + 1}步"
    errors: list[str] = []

    if not isinstance(action, dict):
        return [f"{prefix}不是对象"]

    tool = action.get("tool")
    if not isinstance(tool, str) or not tool:
        return [f"{prefix}缺少有效 tool 字段"]

    rule = TOOL_RULES.get(tool)
    if rule is None:
        return [f"{prefix}使用了未知工具: {tool}"]

    params = action.get("parameters", {})
    if not isinstance(params, dict):
        return [f"{prefix}的 parameters 必须是对象"]

    for name in rule.required_params:
        if name not in params:
            errors.append(f"{prefix}工具 {tool} 缺少必填参数: {name}")

    allowed_params = set(rule.required_params) | set(rule.optional_params)
    for name in params:
        if name not in allowed_params:
            errors.append(f"{prefix}工具 {tool} 包含未知参数: {name}")

    for name, param_rule in rule.param_rules.items():
        if name not in params:
            continue

        value = params[name]
        if not isinstance(value, param_rule.expected_type):
            errors.append(
                f"{prefix}参数 {name} 类型错误，预期 {param_rule.expected_type.__name__}"
            )
            continue

        if isinstance(value, bool):
            errors.append(f"{prefix}参数 {name} 不能是布尔值")
            continue

        if param_rule.min_value is not None and value < param_rule.min_value:
            errors.append(
                f"{prefix}参数 {name}={value} 低于最小值 {param_rule.min_value}"
            )

        if param_rule.max_value is not None and value > param_rule.max_value:
            errors.append(
                f"{prefix}参数 {name}={value} 超过最大值 {param_rule.max_value}"
            )

    return errors


def validate_action_sequence(
    actions: Any,
    *,
    max_actions: int = 12,
    max_motion_duration_s: float = 20.0,
) -> ValidationResult:
    """Validate a full action sequence."""
    result = ValidationResult(ok=False)

    if not isinstance(actions, list):
        result.errors.append("动作序列必须是 JSON 数组")
        return result

    if not actions:
        result.errors.append("动作序列不能为空")
        return result

    if len(actions) > max_actions:
        result.errors.append(f"动作数量 {len(actions)} 超过上限 {max_actions}")

    for index, action in enumerate(actions):
        result.errors.extend(validate_action(action, index))

    if result.errors:
        return result

    tools = [action["tool"] for action in actions]
    if "error" in tools and len(actions) > 1:
        result.errors.append("error 工具只能单独出现，不能和飞行动作混用")
        return result

    airborne = False
    landed = False
    has_takeoff = False
    has_land = False
    has_motion = False
    total_motion_duration = 0.0

    for index, action in enumerate(actions):
        tool = action["tool"]
        params = action.get("parameters", {})
        rule = TOOL_RULES[tool]
        prefix = f"第{index + 1}步"

        if landed and tool not in {"get_status", "error"}:
            result.errors.append(f"{prefix}发生在降落之后，不允许继续执行 {tool}")

        if rule.requires_airborne and not airborne:
            result.errors.append(f"{prefix}工具 {tool} 需要先起飞")

        if tool == "takeoff":
            if airborne:
                result.errors.append(f"{prefix}重复起飞")
            has_takeoff = True
            airborne = True

        if tool == "land":
            has_land = True
            airborne = False
            landed = True

        if rule.is_motion:
            has_motion = True
            total_motion_duration += float(params.get("duration_s", 0.0))

        if rule.requires_manual_confirm:
            result.require_manual_confirm = True

    if has_motion and not has_takeoff:
        result.errors.append("包含运动动作时，序列必须包含 takeoff")

    if has_takeoff and not has_land:
        result.errors.append("包含 takeoff 时，序列必须包含 land")

    if total_motion_duration > max_motion_duration_s:
        result.errors.append(
            f"累计运动时间 {total_motion_duration:.1f}s 超过上限 {max_motion_duration_s:.1f}s"
        )

    if result.require_manual_confirm:
        result.warnings.append("动作序列包含起飞、运动或模式切换，真机执行前必须人工确认")

    result.ok = not result.errors
    return result


def _demo() -> None:
    examples = [
        [
            {"tool": "pre_flight_check", "parameters": {}},
            {"tool": "takeoff", "parameters": {"duration_s": 5}},
            {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}},
            {"tool": "land", "parameters": {"duration_s": 5}},
        ],
        [
            {"tool": "takeoff", "parameters": {"duration_s": 5}},
            {"tool": "fly_forward", "parameters": {"duration_s": 20, "speed": 80}},
            {"tool": "land", "parameters": {"duration_s": 5}},
        ],
    ]

    for actions in examples:
        result = validate_action_sequence(actions)
        print("actions:", actions)
        print("ok:", result.ok)
        print("errors:", result.errors)
        print("warnings:", result.warnings)
        print("require_manual_confirm:", result.require_manual_confirm)
        print("-" * 60)


if __name__ == "__main__":
    _demo()
