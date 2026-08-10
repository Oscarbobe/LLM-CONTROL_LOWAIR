"""A* grid-based path planner for multi-no-fly-zone avoidance."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

from swing_control.mapping.site_map import MapLimits, NoFlyZone, Point3D, SiteMap


@dataclass(order=True)
class _AStarNode:
    f: float
    g: float = field(compare=False)
    x: int = field(compare=False)
    y: int = field(compare=False)
    parent: _AStarNode | None = field(compare=False, default=None)


def plan_astar_path(
    site_map: SiteMap,
    start: Point3D,
    goal: Point3D,
    *,
    grid_resolution: float = 0.5,
    safety_margin: float = 0.3,
) -> list[Point3D]:
    """Find shortest collision-free path using A* on a 2D grid.

    Returns list of waypoints from start to goal at safe_height_m.
    Returns empty list if no path exists.
    """
    safe_z = site_map.flight.safe_height_m
    limits = site_map.limits

    min_x = limits.min_x + grid_resolution
    max_x = limits.max_x - grid_resolution
    min_y = limits.min_y + grid_resolution
    max_y = limits.max_y - grid_resolution

    cols = int((max_x - min_x) / grid_resolution) + 1
    rows = int((max_y - min_y) / grid_resolution) + 1

    if cols < 2 or rows < 2:
        return []

    # Mark blocked cells
    blocked = [[False] * rows for _ in range(cols)]
    for zone in site_map.no_fly_zones:
        protected_r = zone.protected_radius_m + safety_margin
        cx, cy = zone.center.x, zone.center.y
        ci0 = int((cx - protected_r - min_x) / grid_resolution)
        ci1 = int((cx + protected_r - min_x) / grid_resolution) + 1
        cj0 = int((cy - protected_r - min_y) / grid_resolution)
        cj1 = int((cy + protected_r - min_y) / grid_resolution) + 1
        for ci in range(max(0, ci0), min(cols, ci1)):
            for cj in range(max(0, cj0), min(rows, cj1)):
                wx = min_x + ci * grid_resolution
                wy = min_y + cj * grid_resolution
                if ((wx - cx) ** 2 + (wy - cy) ** 2) ** 0.5 <= protected_r:
                    blocked[ci][cj] = True

    def _to_grid(p: Point3D) -> tuple[int, int]:
        return (
            int((p.x - min_x) / grid_resolution),
            int((p.y - min_y) / grid_resolution),
        )

    def _to_world(ci: int, cj: int) -> Point3D:
        return Point3D(
            min_x + ci * grid_resolution,
            min_y + cj * grid_resolution,
            safe_z,
        )

    sx, sy = _to_grid(start)
    gx, gy = _to_grid(goal)

    if not (0 <= sx < cols and 0 <= sy < rows):
        return []
    if not (0 <= gx < cols and 0 <= gy < rows):
        return []
    if blocked[sx][sy] or blocked[gx][gy]:
        return []

    def _heuristic(ci: int, cj: int) -> float:
        return ((ci - gx) ** 2 + (cj - gy) ** 2) ** 0.5

    open_set: list[_AStarNode] = []
    closed: dict[tuple[int, int], float] = {}

    start_node = _AStarNode(f=_heuristic(sx, sy), g=0, x=sx, y=sy)
    heapq.heappush(open_set, start_node)

    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

    while open_set:
        current = heapq.heappop(open_set)

        if current.x == gx and current.y == gy:
            path: list[Point3D] = []
            node: _AStarNode | None = current
            while node is not None:
                path.append(_to_world(node.x, node.y))
                node = node.parent
            path.reverse()
            return _simplify_path(path, site_map, safety_margin)

        key = (current.x, current.y)
        if key in closed and closed[key] <= current.g:
            continue
        closed[key] = current.g

        for dx, dy in neighbors:
            nx, ny = current.x + dx, current.y + dy
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            if blocked[nx][ny]:
                continue

            move_cost = math.sqrt(dx * dx + dy * dy)
            ng = current.g + move_cost

            nkey = (nx, ny)
            if nkey in closed and closed[nkey] <= ng:
                continue

            neighbor = _AStarNode(
                f=ng + _heuristic(nx, ny),
                g=ng,
                x=nx,
                y=ny,
                parent=current,
            )
            heapq.heappush(open_set, neighbor)

    return []


def _simplify_path(
    path: list[Point3D],
    site_map: SiteMap,
    safety_margin: float,
) -> list[Point3D]:
    if len(path) <= 2:
        return path

    result = [path[0]]
    anchor = 0
    for i in range(1, len(path) - 1):
        if _segment_collides(path[anchor], path[i + 1], site_map, safety_margin):
            result.append(path[i])
            anchor = i
    result.append(path[-1])

    # Merge collinear segments: remove intermediate waypoints
    # that lie on the same line between two non-colliding waypoints
    merged = [result[0]]
    anchor = 0
    for i in range(1, len(result) - 1):
        if _segment_collides(result[anchor], result[i + 1], site_map, safety_margin):
            merged.append(result[i])
            anchor = i
    merged.append(result[-1])

    return merged


def _segment_collides(
    a: Point3D,
    b: Point3D,
    site_map: SiteMap,
    safety_margin: float,
    samples: int = 20,
) -> bool:
    for zone in site_map.no_fly_zones:
        protected_r = zone.protected_radius_m + safety_margin
        cx, cy = zone.center.x, zone.center.y
        for t in range(samples + 1):
            alpha = t / samples
            px = a.x + alpha * (b.x - a.x)
            py = a.y + alpha * (b.y - a.y)
            if ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 <= protected_r:
                return True
    return False