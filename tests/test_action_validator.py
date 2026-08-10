"""Tests for action_validator — safety rules, parameter bounds, sequence logic."""

from __future__ import annotations

import pytest

from swing_control.safety.action_validator import validate_action, validate_action_sequence


# ── 单个动作校验 ──────────────────────────────────────────

def test_valid_takeoff():
    errors = validate_action({"tool": "takeoff", "parameters": {"duration_s": 5}}, 0)
    assert errors == []


def test_valid_land():
    errors = validate_action({"tool": "land", "parameters": {"duration_s": 5}}, 0)
    assert errors == []


def test_valid_fly_forward():
    errors = validate_action(
        {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}}, 0
    )
    assert errors == []


def test_unknown_tool_fails():
    errors = validate_action({"tool": "do_backflip", "parameters": {}}, 0)
    assert len(errors) >= 1
    assert "未知工具" in errors[0]


def test_missing_required_param():
    errors = validate_action({"tool": "takeoff", "parameters": {}}, 0)
    assert len(errors) >= 1
    assert "duration_s" in errors[0]


def test_unknown_param_warns():
    errors = validate_action(
        {"tool": "takeoff", "parameters": {"duration_s": 5, "extra": 99}}, 0
    )
    assert len(errors) >= 1
    assert "未知参数" in errors[0]


def test_duration_below_min():
    errors = validate_action({"tool": "hover", "parameters": {"duration_s": 0.01}}, 0)
    assert len(errors) >= 1
    assert "0.01" in errors[0] or "最小值" in errors[0]


def test_duration_above_max():
    errors = validate_action({"tool": "hover", "parameters": {"duration_s": 99}}, 0)
    assert len(errors) >= 1
    assert "99" in errors[0] or "最大值" in errors[0]


def test_speed_out_of_range():
    errors = validate_action(
        {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 999}}, 0
    )
    assert len(errors) >= 1


def test_not_dict():
    errors = validate_action("not_a_dict", 0)
    assert len(errors) >= 1


def test_missing_tool():
    errors = validate_action({"parameters": {}}, 0)
    assert len(errors) >= 1


def test_params_not_dict():
    errors = validate_action({"tool": "takeoff", "parameters": [1, 2, 3]}, 0)
    assert len(errors) >= 1


# ── 序列校验 ──────────────────────────────────────────────

def test_full_valid_sequence():
    result = validate_action_sequence(
        [
            {"tool": "pre_flight_check", "parameters": {}},
            {"tool": "takeoff", "parameters": {"duration_s": 5}},
            {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}},
            {"tool": "land", "parameters": {"duration_s": 5}},
        ]
    )
    assert result.ok
    assert result.require_manual_confirm


def test_empty_sequence_fails():
    result = validate_action_sequence([])
    assert not result.ok


def test_not_list_fails():
    result = validate_action_sequence("not_a_list")
    assert not result.ok


def test_motion_without_takeoff_fails():
    result = validate_action_sequence(
        [
            {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}},
            {"tool": "land", "parameters": {"duration_s": 5}},
        ]
    )
    assert not result.ok
    assert any("先起飞" in e for e in result.errors)


def test_takeoff_without_land_fails():
    result = validate_action_sequence(
        [
            {"tool": "takeoff", "parameters": {"duration_s": 5}},
        ]
    )
    assert not result.ok
    assert any("land" in e for e in result.errors)


def test_action_after_land_fails():
    result = validate_action_sequence(
        [
            {"tool": "takeoff", "parameters": {"duration_s": 5}},
            {"tool": "land", "parameters": {"duration_s": 5}},
            {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}},
        ]
    )
    assert not result.ok
    assert any("降落之后" in e for e in result.errors)


def test_double_takeoff_fails():
    result = validate_action_sequence(
        [
            {"tool": "takeoff", "parameters": {"duration_s": 5}},
            {"tool": "takeoff", "parameters": {"duration_s": 5}},
            {"tool": "land", "parameters": {"duration_s": 5}},
        ]
    )
    assert not result.ok
    assert any("重复起飞" in e for e in result.errors)


def test_exceeds_max_actions():
    actions = [
        {"tool": "takeoff", "parameters": {"duration_s": 5}},
        *[{"tool": "hover", "parameters": {"duration_s": 0.2}} for _ in range(12)],
        {"tool": "land", "parameters": {"duration_s": 5}},
    ]
    result = validate_action_sequence(actions)
    assert not result.ok
    assert any("上限" in e for e in result.errors)


def test_exceeds_motion_duration():
    result = validate_action_sequence(
        [
            {"tool": "takeoff", "parameters": {"duration_s": 5}},
            {"tool": "fly_forward", "parameters": {"duration_s": 5, "speed": 20}},
            {"tool": "fly_forward", "parameters": {"duration_s": 5, "speed": 20}},
            {"tool": "fly_forward", "parameters": {"duration_s": 5, "speed": 20}},
            {"tool": "fly_forward", "parameters": {"duration_s": 5, "speed": 20}},
            {"tool": "fly_forward", "parameters": {"duration_s": 5, "speed": 20}},
            {"tool": "land", "parameters": {"duration_s": 5}},
        ]
    )
    assert not result.ok
    assert any("运动时间" in e for e in result.errors)


def test_error_tool_with_flight_actions_fails():
    result = validate_action_sequence(
        [
            {"tool": "error", "parameters": {"message": "stop"}},
            {"tool": "takeoff", "parameters": {"duration_s": 5}},
        ]
    )
    assert not result.ok
    assert any("单独出现" in e for e in result.errors)


def test_error_tool_alone_passes():
    result = validate_action_sequence(
        [{"tool": "error", "parameters": {"message": "无法识别"}}]
    )
    assert result.ok


def test_pre_flight_check_alone_passes():
    result = validate_action_sequence(
        [
            {"tool": "pre_flight_check", "parameters": {}},
            {"tool": "get_status", "parameters": {}},
        ]
    )
    assert result.ok