"""Generate Swing action routes from named map targets with A* path planning."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from swing_control.mapping.site_map import (
    DEFAULT_SITE_MAP_PATH,
    NamedArea,
    NoFlyZone,
    Point3D,
    SiteMap,
    load_site_map,
)
from swing_control.planning.path_planner import plan_astar_path
from swing_control.planning.trajectory_smoother import smooth_waypoints
from swing_control.planning.wind_model import WindField, apply_wind_to_waypoints


@dataclass
class RoutePlanResult:
    ok: bool
    actions: list[dict] = field(default_factory=list)
    target_area: str | None = None
    waypoints: list[Point3D] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def plan_route_from_instruction(
    instruction: str,
    *,
    map_path: str | Path = DEFAULT_SITE_MAP_PATH,
    use_astar: bool = True,
    return_to_home: bool = False,
    wind: WindField | None = None,
) -> RoutePlanResult:
    site_map = load_site_map(map_path)
    area = site_map.find_area(instruction)
    if area is None:
        return RoutePlanResult(False, errors=["指令中没有匹配到地图区域"])

    return plan_route_to_area(
        site_map,
        area,
        hover_s=_extract_hover_seconds(instruction) or site_map.flight.default_hover_s,
        use_astar=use_astar,
        return_to_home=return_to_home,
        wind=wind,
    )


def plan_route_to_area(
    site_map: SiteMap,
    area: NamedArea,
    *,
    hover_s: float | None = None,
    use_astar: bool = True,
    return_to_home: bool = False,
    wind: WindField | None = None,
) -> RoutePlanResult:
    target = Point3D(
        x=area.center.x,
        y=area.center.y,
        z=max(area.center.z, site_map.flight.safe_height_m),
    )
    hover_duration = _clamp(float(hover_s if hover_s is not None else site_map.flight.default_hover_s), 0.2, 5.0)
    errors: list[str] = []
    warnings: list[str] = []

    if not site_map.limits.contains(target):
        errors.append(f"目标区域 {area.name} 超出地图飞行边界")

    zone = site_map.containing_no_fly_zone(target)
    if zone:
        errors.append(f"目标区域 {area.name} 位于禁飞区 {zone.name} 内")

    if errors:
        return RoutePlanResult(False, target_area=area.name, errors=errors)

    waypoints = _build_waypoints(site_map, target, warnings, use_astar=use_astar, return_to_home=return_to_home)

    if wind is not None and (wind.vx != 0 or wind.vy != 0 or wind.gust_std != 0):
        waypoints = apply_wind_to_waypoints(waypoints, wind)
        warnings.append(f"已应用风扰动: vx={wind.vx}m/s, vy={wind.vy}m/s, gust={wind.gust_std}m/s")

    actions = _waypoints_to_actions(site_map, waypoints, hover_duration)
    return RoutePlanResult(True, actions=actions, target_area=area.name, waypoints=waypoints, warnings=warnings)


def _build_waypoints(
    site_map: SiteMap,
    target: Point3D,
    warnings: list[str],
    *,
    use_astar: bool = True,
    return_to_home: bool = False,
) -> list[Point3D]:
    origin = Point3D(site_map.origin.x, site_map.origin.y, max(site_map.origin.z, site_map.flight.safe_height_m))

    # Try A* first if enabled and multiple no-fly zones exist
    if use_astar and len(site_map.no_fly_zones) >= 1:
        astar_path = plan_astar_path(site_map, origin, target)
        if astar_path and len(astar_path) >= 2:
            smoothed = smooth_waypoints(astar_path, site_map)
            warnings.append(f"A* 路径规划成功，{len(smoothed)} 个航点（已平滑）")
            if return_to_home:
                smoothed.append(_find_landing_point(site_map, smoothed[-1]))
                warnings.append("已添加返航点")
            return smoothed

    # Fallback: original axis-aligned detour logic
    waypoints = [origin]

    for zone in site_map.no_fly_zones:
        if _axis_path_intersects_zone(origin, target, zone):
            detour = _detour_waypoints(site_map, origin, zone, target)
            if detour:
                waypoints.extend(detour)
                warnings.append(f"直线路径经过禁飞区 {zone.name}，已加入绕行航点")
            else:
                warnings.append(f"直线路径接近禁飞区 {zone.name}，但未找到可用绕行点")

    waypoints.append(target)

    if return_to_home:
        waypoints.append(_find_landing_point(site_map, waypoints[-1]))
        warnings.append("已添加返航点")

    return waypoints


def _find_landing_point(site_map: SiteMap, current: Point3D) -> Point3D:
    if site_map.landing_points:
        return site_map.landing_points[0]
    return Point3D(site_map.origin.x, site_map.origin.y, max(site_map.origin.z, site_map.flight.safe_height_m))


def _waypoints_to_actions(site_map: SiteMap, waypoints: list[Point3D], hover_s: float) -> list[dict]:
    actions: list[dict] = [
        {"tool": "pre_flight_check", "parameters": {}},
        {"tool": "takeoff", "parameters": {"duration_s": site_map.flight.takeoff_duration_s}},
    ]

    current = waypoints[0]
    for waypoint in waypoints[1:]:
        actions.extend(_segment_actions(site_map, current, waypoint))
        current = waypoint

    actions.append({"tool": "hover", "parameters": {"duration_s": hover_s}})
    actions.append({"tool": "land", "parameters": {"duration_s": site_map.flight.land_duration_s}})
    return _merge_consecutive_actions(actions)


def _merge_consecutive_actions(actions: list[dict]) -> list[dict]:
    if len(actions) <= 1:
        return actions

    merged: list[dict] = [actions[0]]
    for action in actions[1:]:
        prev = merged[-1]
        if (
            action["tool"] == prev["tool"]
            and action["tool"] in {"fly_forward", "fly_backward", "fly_left", "fly_right"}
            and action["parameters"].get("speed") == prev["parameters"].get("speed")
        ):
            prev["parameters"]["duration_s"] = round(
                prev["parameters"]["duration_s"] + action["parameters"]["duration_s"], 2
            )
        else:
            merged.append(action)

    return merged


def _segment_actions(site_map: SiteMap, start: Point3D, end: Point3D) -> list[dict]:
    actions: list[dict] = []
    dx = end.x - start.x
    dy = end.y - start.y

    if abs(dx) >= 0.05:
        tool = "fly_forward" if dx > 0 else "fly_backward"
        actions.extend(_motion_chunks(tool, abs(dx), site_map))

    if abs(dy) >= 0.05:
        tool = "fly_right" if dy > 0 else "fly_left"
        actions.extend(_motion_chunks(tool, abs(dy), site_map))

    return actions


def _motion_chunks(tool: str, distance_m: float, site_map: SiteMap) -> list[dict]:
    mps = max(0.2, site_map.flight.meters_per_second)
    remaining = distance_m / mps
    chunks: list[dict] = []
    while remaining > 0.05:
        duration = _clamp(min(remaining, 5.0), 0.2, 5.0)
        chunks.append(
            {
                "tool": tool,
                "parameters": {
                    "duration_s": round(duration, 2),
                    "speed": site_map.flight.default_speed,
                },
            }
        )
        remaining -= duration
    return chunks


def _segment_intersects_zone(start: Point3D, end: Point3D, zone: NoFlyZone) -> bool:
    sx, sy = start.x, start.y
    ex, ey = end.x, end.y
    cx, cy = zone.center.x, zone.center.y
    dx = ex - sx
    dy = ey - sy
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return ((sx - cx) ** 2 + (sy - cy) ** 2) ** 0.5 <= zone.protected_radius_m

    t = ((cx - sx) * dx + (cy - sy) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    closest = Point3D(sx + t * dx, sy + t * dy, start.z)
    distance = ((closest.x - cx) ** 2 + (closest.y - cy) ** 2) ** 0.5
    return distance <= zone.protected_radius_m


def _axis_path_intersects_zone(start: Point3D, end: Point3D, zone: NoFlyZone) -> bool:
    corner = Point3D(end.x, start.y, start.z)
    return _segment_intersects_zone(start, corner, zone) or _segment_intersects_zone(corner, end, zone)


def _axis_path_intersects_any_zone(site_map: SiteMap, start: Point3D, end: Point3D) -> bool:
    return any(_axis_path_intersects_zone(start, end, zone) for zone in site_map.no_fly_zones)


def _detour_waypoints(site_map: SiteMap, origin: Point3D, zone: NoFlyZone, target: Point3D) -> list[Point3D]:
    offset = zone.protected_radius_m + 0.6
    candidate_paths = [
        [
            Point3D(origin.x, zone.center.y + offset, site_map.flight.safe_height_m),
            Point3D(target.x, zone.center.y + offset, site_map.flight.safe_height_m),
        ],
        [
            Point3D(origin.x, zone.center.y - offset, site_map.flight.safe_height_m),
            Point3D(target.x, zone.center.y - offset, site_map.flight.safe_height_m),
        ],
        [
            Point3D(zone.center.x + offset, origin.y, site_map.flight.safe_height_m),
            Point3D(zone.center.x + offset, target.y, site_map.flight.safe_height_m),
        ],
        [
            Point3D(zone.center.x - offset, origin.y, site_map.flight.safe_height_m),
            Point3D(zone.center.x - offset, target.y, site_map.flight.safe_height_m),
        ],
    ]
    for candidates in candidate_paths:
        if any(not site_map.limits.contains(candidate) for candidate in candidates):
            continue
        if any(site_map.containing_no_fly_zone(candidate) for candidate in candidates):
            continue
        full_path = [origin, *candidates, target]
        if any(
            _axis_path_intersects_any_zone(site_map, start, end)
            for start, end in zip(full_path, full_path[1:])
        ):
            continue
        return candidates
    return []


def _extract_hover_seconds(text: str) -> float | None:
    pattern = r"(?:悬停|停留|等待)[^0-9一二两三四五六七八九十半]*([0-9]+(?:\.[0-9]+)?|半|一|二|两|三|四|五|六|七|八|九|十)\s*秒"
    match = re.search(pattern, text)
    if not match:
        return None
    return _clamp(_chinese_number_to_float(match.group(1)), 0.2, 5.0)


def _chinese_number_to_float(value: str) -> float:
    mapping = {
        "半": 0.5,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    if value in mapping:
        return float(mapping[value])
    return float(value)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
