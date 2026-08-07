function errors = checkMapSafety(pose, siteMap)
%CHECKMAPSAFETY Check map limits and circular no-fly zones.

errors = strings(0, 1);
x = pose(1);
y = pose(2);
z = pose(3);

if x < siteMap.limits.min_x || x > siteMap.limits.max_x
    errors(end + 1, 1) = sprintf("x out of bounds: %.2f", x);
end

if y < siteMap.limits.min_y || y > siteMap.limits.max_y
    errors(end + 1, 1) = sprintf("y out of bounds: %.2f", y);
end

if z < siteMap.limits.min_z || z > siteMap.limits.max_z
    errors(end + 1, 1) = sprintf("z out of bounds: %.2f", z);
end

if isfield(siteMap, "no_fly_zones")
    zones = siteMap.no_fly_zones;
    for i = 1:numel(zones)
        zone = zones(i);
        protectedRadius = double(zone.radius_m) + double(zone.buffer_m);
        distance = hypot(x - double(zone.center.x), y - double(zone.center.y));
        if distance <= protectedRadius
            errors(end + 1, 1) = sprintf( ...
                "inside no-fly zone %s: distance %.2fm <= %.2fm", ...
                string(zone.name), distance, protectedRadius);
        end
    end
end
end
