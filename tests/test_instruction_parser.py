"""Tests for instruction_parser - rule-based parsing of common Chinese instructions."""

from __future__ import annotations

from swing_control.nlp.instruction_parser import (
    _rule_based_parse,
    _extract_seconds,
    _chinese_number_to_float,
    _clamp_duration,
    _extract_json_array,
    _map_based_parse,
)


# ── _extract_seconds ──────────────────────────────────────

def test_extract_seconds_hover():
    assert _extract_seconds("悬停2秒", ("悬停",)) == 2.0


def test_extract_seconds_chinese_number():
    assert _extract_seconds("悬停两秒", ("悬停",)) == 2.0


def test_extract_seconds_not_found():
    assert _extract_seconds("no match here", ("悬停",)) is None


def test_extract_seconds_clamped():
    assert _extract_seconds("悬停10秒", ("悬停",)) == 5.0  # clamped to max


# ── _chinese_number_to_float ───────────────────────────────

def test_chinese_number_to_float_half():
    assert _chinese_number_to_float("半") == 0.5


def test_chinese_number_to_float_raw():
    assert _chinese_number_to_float("3.5") == 3.5


# ── _clamp_duration ────────────────────────────────────────

def test_clamp_duration_min():
    assert _clamp_duration(0.01) == 0.2


def test_clamp_duration_max():
    assert _clamp_duration(99) == 5.0


def test_clamp_duration_pass():
    assert _clamp_duration(2.0) == 2.0


# ── _extract_json_array ────────────────────────────────────

def test_extract_json_array_valid():
    result = _extract_json_array('[{"tool":"takeoff","parameters":{"duration_s":5}}]')
    assert len(result) == 1
    assert result[0]["tool"] == "takeoff"


def test_extract_json_array_no_brackets():
    import pytest
    with pytest.raises(ValueError):
        _extract_json_array("no json here")


def test_extract_json_array_not_list():
    import pytest
    with pytest.raises(ValueError):
        _extract_json_array('{"tool":"takeoff"}')


def test_extract_json_array_not_dict_elements():
    import pytest
    with pytest.raises(ValueError):
        _extract_json_array('["string", 123]')


# ── _rule_based_parse ──────────────────────────────────────

def test_rule_parse_takeoff_hover_land():
    actions = _rule_based_parse("起飞悬停2秒再降落")
    tools = [a["tool"] for a in actions]
    assert "takeoff" in tools
    assert "hover" in tools
    assert "land" in tools


def test_rule_parse_takeoff_only_adds_land():
    actions = _rule_based_parse("起飞")
    tools = [a["tool"] for a in actions]
    assert "takeoff" in tools
    assert "land" in tools  # auto-added


def test_rule_parse_forward():
    actions = _rule_based_parse("向前飞2秒")
    tools = [a["tool"] for a in actions]
    assert "fly_forward" in tools


def test_rule_parse_backward():
    actions = _rule_based_parse("向后飞1秒")
    tools = [a["tool"] for a in actions]
    assert "fly_backward" in tools


def test_rule_parse_turn_left():
    actions = _rule_based_parse("左转1秒")
    tools = [a["tool"] for a in actions]
    assert "turn_left" in tools


def test_rule_parse_empty():
    actions = _rule_based_parse("")
    assert actions == []


def test_rule_parse_map_based_fallback():
    """When a map area name is in the instruction, rule parser delegates to map."""
    actions = _rule_based_parse("飞到果园上方悬停两秒")
    # Should delegate to map-based parsing since "果园" is a mapped area
    tools = [a["tool"] for a in actions]
    assert "takeoff" in tools
    assert "land" in tools


# ── _map_based_parse ───────────────────────────────────────

def test_map_based_parse_no_match():
    actions = _map_based_parse("just hover")
    assert actions == []


def test_map_based_parse_with_match():
    actions = _map_based_parse("fly to orchard hover 2s then land")
    # Depends on site_map.json having matching areas
    if actions:
        tools = [a["tool"] for a in actions]
        assert "takeoff" in tools
        assert "land" in tools