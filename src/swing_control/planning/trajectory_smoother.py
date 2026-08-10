"""Trajectory smoothing for waypoint sequences."""

from __future__ import annotations

import math

from swing_control.mapping.site_map import Point3D, SiteMap


def smooth_waypoints(
    waypoints: list[Point3D],
    site_map: SiteMap,
    *,
    window_size: int = 3,
    safety_margin: float = 0.3,
) -> list[Point3D]:
    """Apply moving-average smoothing to waypoints.

    Keeps start and end points fixed. Skips smoothing if it would
    push a waypoint into a no-fly zone.
    """
    if len(waypoints) <= 2:
        return waypoints

    half = window_size // 2
    result = [waypoints[0]]

    for i in range(1, len(waypoints) - 1):
        start = max(0, i - half)
        end = min(len(waypoints), i + half + 1)
        window = waypoints[start:end]

        sx = sum(w.x for w in window) / len(window)
        sy = sum(w.y for w in window) / len(window)
        smoothed = Point3D(sx, sy, waypoints[i].z)

        if _is_safe(smoothed, site_map, safety_margin):
            result.append(smoothed)
        else:
            result.append(waypoints[i])

    result.append(waypoints[-1])
    return result


def _is_safe(point: Point3D, site_map: SiteMap, safety_margin: float) -> bool:
    if not site_map.limits.contains(point):
        return False
    for zone in site_map.no_fly_zones:
        protected_r = zone.protected_radius_m + safety_margin
        dist = math.hypot(point.x - zone.center.x, point.y - zone.center.y)
        if dist <= protected_r:
            return False
    return True