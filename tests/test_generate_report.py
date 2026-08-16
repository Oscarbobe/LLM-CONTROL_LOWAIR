from __future__ import annotations

import json
from pathlib import Path

from swing_control.app.generate_report import build_report


def test_build_report_includes_actions_and_validation(tmp_path: Path) -> None:
    actions = [
        {"tool": "pre_flight_check", "parameters": {}},
        {"tool": "takeoff", "parameters": {"duration_s": 5}},
        {"tool": "hover", "parameters": {"duration_s": 2}},
        {"tool": "land", "parameters": {"duration_s": 5}},
    ]
    actions_path = tmp_path / "actions.json"
    actions_path.write_text(json.dumps(actions, ensure_ascii=False), encoding="utf-8")

    sim_path = tmp_path / "latest_result.json"
    sim_path.write_text(
        json.dumps({"ok": True, "finalPose": [0, 0, 0], "totalTime": 12}, ensure_ascii=False),
        encoding="utf-8",
    )

    report = build_report(
        instruction="起飞后悬停两秒再降落",
        actions_path=actions_path,
        map_path=Path("data/maps/site_map.json"),
        sim_result_path=sim_path,
    )

    assert "起飞后悬停两秒再降落" in report
    assert "校验结果：通过" in report
    assert "`hover`" in report
    assert "仿真结论：`PASS`" in report
