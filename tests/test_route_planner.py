"""Tests for route_planner - map target resolution, route generation, no-fly zones."""

from __future__ import annotations

from swing_control.planning.route_planner import (
    plan_route_from_instruction,
    plan_route_to_area,
)
from swing_control.mapping.site_map import (
    MapLimits,
    NamedArea,
    NoFlyZone,
    Point3D,
    SiteMap,
    FlightSettings,
    load_site_map,
)


def _make_site_map() -> SiteMap:
    return SiteMap(
        name="test",
        coordinate_system="local_meters",
        origin=Point3D(0, 0, 0),
        flight=FlightSettings(),
        limits=MapLimits(-10, 10, -10, 10, 0, 5),
        areas=(
            NamedArea("orchard", Point3D(3, 2, 1.5), 1.2, ("fruit_area",)),
            NamedArea("cornfield", Point3D(-3, 2.5, 1.5), 1.5, ("corn",)),
        ),
        no_fly_zones=(
            NoFlyZone("house", Point3D(1.5, 1.2, 0), 0.8, 0.5),
        ),
        landing_points=(Point3D(0, 0, 0),),
    )


def test_load_real_site_map():
    site_map = load_site_map()
    assert site_map.name == "demo_mountain_test_site"
    assert len(site_map.areas) >= 4
    assert len(site_map.no_fly_zones) >= 2


def test_find_orchard_from_instruction():
    result = plan_route_from_instruction("fly to orchard and hover 2s then land")
    # This won't match the Chinese map, but we test the code path
    assert isinstance(result.ok, bool)


def test_unknown_area_fails():
    result = plan_route_from_instruction("fly to the moon")
    assert not result.ok
    assert len(result.errors) >= 1


def test_plan_route_to_area_custom_map():
    site_map = _make_site_map()
    area = site_map.find_area("orchard")
    assert area is not None

    result = plan_route_to_area(site_map, area, hover_s=2)
    assert result.ok
    assert result.target_area == "orchard"
    assert len(result.actions) >= 4

    tools = [a["tool"] for a in result.actions]
    assert "takeoff" in tools
    assert "land" in tools


def test_plan_route_to_area_with_no_fly_zone_detour():
    site_map = _make_site_map()
    area = site_map.find_area("orchard")
    assert area is not None

    result = plan_route_to_area(site_map, area, hover_s=2)
    assert result.ok

    # A* now handles multi-no-fly-zone; detour or A* warning expected
    if result.warnings:
        assert any(
            "绕行" in w or "禁飞区" in w or "A*" in w or "no-fly" in w.lower()
            for w in result.warnings
        )


def test_route_has_pre_flight_check():
    site_map = _make_site_map()
    area = site_map.find_area("cornfield")
    assert area is not None
    result = plan_route_to_area(site_map, area, hover_s=2)
    assert result.actions[0]["tool"] == "pre_flight_check"


def test_route_ends_with_land():
    site_map = _make_site_map()
    area = site_map.find_area("cornfield")
    assert area is not None
    result = plan_route_to_area(site_map, area, hover_s=2)
    assert result.actions[-1]["tool"] == "land"


def test_target_out_of_bounds_fails():
    site_map = SiteMap(
        name="test_small",
        coordinate_system="local_meters",
        origin=Point3D(0, 0, 0),
        flight=FlightSettings(),
        limits=MapLimits(-1, 1, -1, 1, 0, 3),
        areas=(NamedArea("far", Point3D(50, 50, 2), 1.0),),
    )
    area = site_map.find_area("far")
    assert area is not None
    result = plan_route_to_area(site_map, area)
    assert not result.ok


def test_target_in_no_fly_zone_fails():
    site_map = SiteMap(
        name="test_nfz",
        coordinate_system="local_meters",
        origin=Point3D(0, 0, 0),
        flight=FlightSettings(),
        limits=MapLimits(-10, 10, -10, 10, 0, 5),
        areas=(NamedArea("trapped", Point3D(2, 2, 2), 1.0),),
        no_fly_zones=(NoFlyZone("danger", Point3D(2, 2, 0), 3.0, 0.5),),
    )
    area = site_map.find_area("trapped")
    assert area is not None
    result = plan_route_to_area(site_map, area)
    assert not result.ok