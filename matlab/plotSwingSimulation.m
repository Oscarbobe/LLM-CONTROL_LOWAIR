function plotSwingSimulation(siteMap, trajectory, actionLog)
%PLOTSWINGSIMULATION Plot map areas, no-fly zones, and simulated route.

figure("Name", "Swing MATLAB Simulation", "Color", "w");
hold on;
grid on;
axis equal;

xlabel("x / m");
ylabel("y / m");
zlabel("z / m");
title("Swing language-control map simulation");

xlim([siteMap.limits.min_x, siteMap.limits.max_x]);
ylim([siteMap.limits.min_y, siteMap.limits.max_y]);
zlim([siteMap.limits.min_z, siteMap.limits.max_z]);

plot3(trajectory(:, 2), trajectory(:, 3), trajectory(:, 4), ...
    "-o", "Color", [0.1, 0.35, 0.9], "MarkerSize", 4, "LineWidth", 2);

plot3(siteMap.origin.x, siteMap.origin.y, siteMap.origin.z, ...
    "ko", "MarkerFaceColor", "k", "MarkerSize", 7);
text(siteMap.origin.x, siteMap.origin.y, siteMap.origin.z, " origin");

if isfield(siteMap, "areas")
    areas = siteMap.areas;
    for i = 1:numel(areas)
        area = areas(i);
        plot3(area.center.x, area.center.y, area.center.z, ...
            "p", "Color", [0.0, 0.5, 0.15], "MarkerFaceColor", [0.2, 0.8, 0.3], "MarkerSize", 12);
        text(area.center.x, area.center.y, area.center.z, " " + string(area.name), ...
            "Color", [0.0, 0.35, 0.1]);
        drawCircle(area.center.x, area.center.y, area.center.z, area.radius_m, [0.2, 0.7, 0.25], "-");
    end
end

if isfield(siteMap, "no_fly_zones")
    zones = siteMap.no_fly_zones;
    for i = 1:numel(zones)
        zone = zones(i);
        protectedRadius = zone.radius_m + zone.buffer_m;
        drawCircle(zone.center.x, zone.center.y, 0, protectedRadius, [0.9, 0.1, 0.1], "--");
        fillNoFlyDisk(zone.center.x, zone.center.y, protectedRadius);
        text(zone.center.x, zone.center.y, 0, " no-fly: " + string(zone.name), ...
            "Color", [0.75, 0.0, 0.0]);
    end
end

legend(["trajectory", "origin"], "Location", "best");
view(35, 25);

annotationText = sprintf("Actions: %d | Total time: %.2fs", numel(actionLog), trajectory(end, 1));
annotation("textbox", [0.15, 0.01, 0.7, 0.05], ...
    "String", annotationText, "EdgeColor", "none", "HorizontalAlignment", "center");
end

function drawCircle(cx, cy, cz, r, color, style)
theta = linspace(0, 2 * pi, 160);
x = cx + r * cos(theta);
y = cy + r * sin(theta);
z = cz * ones(size(theta));
plot3(x, y, z, style, "Color", color, "LineWidth", 1.5);
end

function fillNoFlyDisk(cx, cy, r)
theta = linspace(0, 2 * pi, 160);
x = cx + r * cos(theta);
y = cy + r * sin(theta);
z = zeros(size(theta));
patch(x, y, z, [1.0, 0.2, 0.2], "FaceAlpha", 0.10, "EdgeColor", "none");
end
