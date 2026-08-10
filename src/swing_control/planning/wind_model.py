"""Wind disturbance model for trajectory perturbation."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from swing_control.mapping.site_map import Point3D


@dataclass(frozen=True)
class WindField:
    """Constant wind vector with optional gust component."""

    vx: float = 0.0  # m/s, positive = eastward
    vy: float = 0.0  # m/s, positive = northward
    gust_std: float = 0.0  # standard deviation of gust (m/s)
    gust_direction_std: float = 0.0  # direction variation (radians)

    def perturb(self, position: Point3D, dt: float) -> Point3D:
        """Return position displacement due to wind over dt seconds."""
        dx = self.vx * dt
        dy = self.vy * dt

        if self.gust_std > 0:
            gust_mag = abs(random.gauss(0, self.gust_std))
            gust_angle = random.gauss(0, self.gust_direction_std) if self.gust_direction_std > 0 else 0
            dx += gust_mag * math.cos(gust_angle) * dt
            dy += gust_mag * math.sin(gust_angle) * dt

        return Point3D(dx, dy, 0.0)


# Predefined wind scenarios
WIND_CALM = WindField(0, 0, 0, 0)
WIND_LIGHT = WindField(0.5, 0.3, 0.1, 0.2)
WIND_MODERATE = WindField(1.5, 1.0, 0.3, 0.5)
WIND_STRONG = WindField(3.0, 2.0, 0.8, 0.8)


def apply_wind_to_waypoints(
    waypoints: list[Point3D],
    wind: WindField,
    dt: float = 0.1,
) -> list[Point3D]:
    """Apply wind disturbance to a sequence of waypoints.

    Simulates cumulative drift over time. Each waypoint represents
    a position at a time step, and wind is applied cumulatively.
    """
    if wind.vx == 0 and wind.vy == 0 and wind.gust_std == 0:
        return waypoints

    random.seed(42)  # deterministic for reproducibility
    result: list[Point3D] = []
    cumulative_dx = 0.0
    cumulative_dy = 0.0

    for i, wp in enumerate(waypoints):
        if i == 0:
            result.append(wp)
            continue

        # Compute wind displacement for this step
        displacement = wind.perturb(wp, dt)
        cumulative_dx += displacement.x
        cumulative_dy += displacement.y

        result.append(
            Point3D(
                wp.x + cumulative_dx,
                wp.y + cumulative_dy,
                wp.z,
            )
        )

    return result