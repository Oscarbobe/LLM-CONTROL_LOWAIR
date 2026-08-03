"""Local site map support for named drone target areas."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_SITE_MAP_PATH = Path("data/maps/site_map.json")


@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float = 0.0


@dataclass(frozen=True)
class NamedArea:
    name: str
    center: Point3D
    radius_m: float = 0.5
    aliases: tuple[str, ...] = ()

    def matches(self, text: str) -> bool:
        names = (self.name, *self.aliases)
        return any(name and name in text for name in names)


@dataclass(frozen=True)
class NoFlyZone:
    name: str
    center: Point3D
    radius_m: float
    buffer_m: float = 0.0

    @property
    def protected_radius_m(self) -> float:
        return self.radius_m + self.buffer_m


@dataclass(frozen=True)
class FlightSettings:
    safe_height_m: float = 1.5
    default_hover_s: float = 2.0
    takeoff_duration_s: float = 5.0
    land_duration_s: float = 5.0
    default_speed: float = 20.0
    meters_per_second: float = 1.0


@dataclass(frozen=True)
class MapLimits:
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float = 0.0
    max_z: float = 3.0

    def contains(self, point: Point3D) -> bool:
        return (
            self.min_x <= point.x <= self.max_x
            and self.min_y <= point.y <= self.max_y
            and self.min_z <= point.z <= self.max_z
        )


@dataclass(frozen=True)
class SiteMap:
    name: str
    coordinate_system: str
    origin: Point3D
    flight: FlightSettings
    limits: MapLimits
    areas: tuple[NamedArea, ...] = ()
    no_fly_zones: tuple[NoFlyZone, ...] = ()
    landing_points: tuple[Point3D, ...] = field(default_factory=tuple)

    def find_area(self, text: str) -> NamedArea | None:
        for area in self.areas:
            if area.matches(text):
                return area
        return None

    def containing_no_fly_zone(self, point: Point3D) -> NoFlyZone | None:
        for zone in self.no_fly_zones:
            if distance_2d(point, zone.center) <= zone.protected_radius_m:
                return zone
        return None


def load_site_map(path: str | Path = DEFAULT_SITE_MAP_PATH) -> SiteMap:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_site_map(payload)


def parse_site_map(payload: dict[str, Any]) -> SiteMap:
    flight = payload.get("flight", {})
    limits = payload.get("limits", {})
    return SiteMap(
        name=str(payload.get("name", "site_map")),
        coordinate_system=str(payload.get("coordinate_system", "local_meters")),
        origin=_point(payload.get("origin", {})),
        flight=FlightSettings(
            safe_height_m=float(flight.get("safe_height_m", 1.5)),
            default_hover_s=float(flight.get("default_hover_s", 2)),
            takeoff_duration_s=float(flight.get("takeoff_duration_s", 5)),
            land_duration_s=float(flight.get("land_duration_s", 5)),
            default_speed=float(flight.get("default_speed", 20)),
            meters_per_second=float(flight.get("meters_per_second", 1)),
        ),
        limits=MapLimits(
            min_x=float(limits.get("min_x", -5)),
            max_x=float(limits.get("max_x", 5)),
            min_y=float(limits.get("min_y", -5)),
            max_y=float(limits.get("max_y", 5)),
            min_z=float(limits.get("min_z", 0)),
            max_z=float(limits.get("max_z", 3)),
        ),
        areas=tuple(_area(item) for item in payload.get("areas", [])),
        no_fly_zones=tuple(_zone(item) for item in payload.get("no_fly_zones", [])),
        landing_points=tuple(_point(item) for item in payload.get("landing_points", [])),
    )


def distance_2d(a: Point3D, b: Point3D) -> float:
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def _point(payload: dict[str, Any]) -> Point3D:
    return Point3D(
        x=float(payload.get("x", 0)),
        y=float(payload.get("y", 0)),
        z=float(payload.get("z", 0)),
    )


def _area(payload: dict[str, Any]) -> NamedArea:
    return NamedArea(
        name=str(payload["name"]),
        center=_point(payload.get("center", {})),
        radius_m=float(payload.get("radius_m", 0.5)),
        aliases=tuple(str(alias) for alias in payload.get("aliases", [])),
    )


def _zone(payload: dict[str, Any]) -> NoFlyZone:
    return NoFlyZone(
        name=str(payload["name"]),
        center=_point(payload.get("center", {})),
        radius_m=float(payload.get("radius_m", 0.5)),
        buffer_m=float(payload.get("buffer_m", 0.0)),
    )
