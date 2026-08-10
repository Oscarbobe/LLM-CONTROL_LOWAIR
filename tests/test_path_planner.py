"""Tests for path_planner, trajectory_smoother, and wind_model."""

from __future__ import annotations

import pytest

from swing_control.planning.path_planner import plan_astar_path
from swing_control.planning.trajectory_smoother import smooth_waypoints
from swing_control.planning.wind_model import (
    WindField,
    WIND_CALM,
    WIND_LIGHT,
    WIND_MODERATE,
    apply_wind_to_waypoints,
)
from swing_control.mapping.site_map import (
    MapLimits,
    NamedArea,
    NoFlyZone,
    Point3D,
    SiteMap,
    FlightSettings,
)


def _simple_map() -> SiteMap:
    return SiteMap(
        name="test",
        coordinate_system="local_meters",
        origin=Point3D(0, 0, 0),
        flight=FlightSettings(),
        limits=MapLimits(-10, 10, -10, 10, 0, 5),
        areas=(),
        no_fly_zones=(
            NoFlyZone("house", Point3D(2, 2, 0), 1.0, 0.5),
        ),
        landing_points=(Point3D(0, 0, 0),),
    )


def _dense_map() -> SiteMap:
    return SiteMap(
        name="dense",
        coordinate_system="local_meters",
        origin=Point3D(0, 0, 0),
        flight=FlightSettings(),
        limits=MapLimits(-10, 10, -10, 10, 0, 5),
        areas=(),
        no_fly_zones=(
            NoFlyZone("nfz1", Point3D(2, 1, 0), 1.0, 0.5),
            NoFlyZone("nfz2", Point3D(5, 3, 0), 1.0, 0.5),
            NoFlyZone("nfz3", Point3D(3, 5, 0), 1.0, 0.5),
        ),
        landing_points=(Point3D(0, 0, 0),),
    )


# ── A* Path Planner ────────────────────────────────────────

def test_astar_direct_path():
    site_map = _simple_map()
    start = Point3D(0, 0, 2)
    goal = Point3D(-3, -3, 2)
    path = plan_astar_path(site_map, start, goal)
    assert len(path) >= 2
    assert path[0].x == pytest.approx(start.x, abs=0.5)
    assert path[-1].x == pytest.approx(goal.x, abs=0.5)


def test_astar_avoids_no_fly_zone():
    site_map = _simple_map()
    start = Point3D(0, 0, 2)
    goal = Point3D(5, 5, 2)
    path = plan_astar_path(site_map, start, goal)
    assert len(path) >= 2

    # Verify no waypoint is inside the no-fly zone
    for wp in path:
        for zone in site_map.no_fly_zones:
            dist = ((wp.x - zone.center.x) ** 2 + (wp.y - zone.center.y) ** 2) ** 0.5
            assert dist > zone.protected_radius_m


def test_astar_goal_in_no_fly_zone():
    site_map = _simple_map()
    goal = Point3D(2, 2, 2)  # center of the no-fly zone
    path = plan_astar_path(site_map, Point3D(0, 0, 2), goal)
    assert path == []


def test_astar_multi_no_fly_zone():
    site_map = _dense_map()
    start = Point3D(0, 0, 2)
    goal = Point3D(8, 8, 2)
    path = plan_astar_path(site_map, start, goal)
    assert len(path) >= 2

    for wp in path:
        for zone in site_map.no_fly_zones:
            dist = ((wp.x - zone.center.x) ** 2 + (wp.y - zone.center.y) ** 2) ** 0.5
            assert dist > zone.protected_radius_m


def test_astar_start_equals_goal():
    site_map = _simple_map()
    p = Point3D(-3, -3, 2)  # safe point, far from no-fly zone
    path = plan_astar_path(site_map, p, p)
    assert len(path) >= 1


# ── Trajectory Smoother ────────────────────────────────────

def test_smooth_preserves_endpoints():
    site_map = _simple_map()
    waypoints = [
        Point3D(0, 0, 2),
        Point3D(1, 0, 2),
        Point3D(2, 1, 2),
        Point3D(3, 3, 2),
        Point3D(5, 5, 2),
    ]
    smoothed = smooth_waypoints(waypoints, site_map)
    assert smoothed[0] == waypoints[0]
    assert smoothed[-1] == waypoints[-1]


def test_smooth_short_path():
    site_map = _simple_map()
    waypoints = [Point3D(0, 0, 2), Point3D(5, 5, 2)]
    smoothed = smooth_waypoints(waypoints, site_map)
    assert len(smoothed) == 2


def test_smooth_does_not_enter_nfz():
    site_map = _simple_map()
    waypoints = [
        Point3D(0, 0, 2),
        Point3D(0.8, 0, 2),  # safe - far from no-fly zone at (2,2)
        Point3D(0, 1.5, 2),
        Point3D(5, 5, 2),
    ]
    smoothed = smooth_waypoints(waypoints, site_map)
    for wp in smoothed[1:-1]:
        for zone in site_map.no_fly_zones:
            dist = ((wp.x - zone.center.x) ** 2 + (wp.y - zone.center.y) ** 2) ** 0.5
            assert dist > zone.protected_radius_m


# ── Wind Model ─────────────────────────────────────────────

def test_wind_calm_does_nothing():
    waypoints = [
        Point3D(0, 0, 2),
        Point3D(1, 0, 2),
        Point3D(2, 0, 2),
    ]
    result = apply_wind_to_waypoints(waypoints, WIND_CALM)
    assert result == waypoints


def test_wind_light_perturbs():
    waypoints = [
        Point3D(0, 0, 2),
        Point3D(1, 0, 2),
        Point3D(2, 0, 2),
    ]
    result = apply_wind_to_waypoints(waypoints, WIND_LIGHT)
    assert len(result) == len(waypoints)
    # First point unchanged
    assert result[0] == waypoints[0]
    # Later points should be perturbed
    assert result[-1] != waypoints[-1]


def test_wind_strong_more_perturbation():
    from swing_control.planning.wind_model import WIND_STRONG
    waypoints = [Point3D(0, 0, 2), Point3D(5, 0, 2)]
    result_light = apply_wind_to_waypoints(waypoints, WIND_LIGHT)
    result_strong = apply_wind_to_waypoints(waypoints, WIND_STRONG)
    diff_light = abs(result_light[-1].x - waypoints[-1].x)
    diff_strong = abs(result_strong[-1].x - waypoints[-1].x)
    assert diff_strong > diff_light


def test_route_planner_with_wind():
    from swing_control.planning.route_planner import plan_route_to_area
    from swing_control.mapping.site_map import load_site_map

    site_map = load_site_map()
    area = site_map.find_area("果园")
    assert area is not None

    result = plan_route_to_area(site_map, area, hover_s=2, wind=WIND_LIGHT)
    assert result.ok
    assert any("风扰动" in w for w in result.warnings)


def test_route_planner_return_to_home():
    from swing_control.planning.route_planner import plan_route_to_area
    from swing_control.mapping.site_map import load_site_map

    site_map = load_site_map()
    area = site_map.find_area("果园")
    assert area is not None

    result = plan_route_to_area(site_map, area, hover_s=2, return_to_home=True)
    assert result.ok
    assert any("返航" in w for w in result.warnings)


def test_route_planner_astar_real_map():
    from swing_control.planning.route_planner import plan_route_from_instruction

    result = plan_route_from_instruction("飞到果园上方悬停两秒再降落", use_astar=True)
    assert result.ok
    assert result.target_area == "果园"
    assert any("A*" in w for w in result.warnings)


# ── WindField dataclass ────────────────────────────────────

def test_wind_field_immutable():
    w = WindField(vx=1.0, vy=2.0)
    try:
        w.vx = 3.0  # type: ignore[misc]
    except Exception:
        pass  # expected - frozen dataclass
    assert w.vx == 1.0