function [disturbedTrajectory, windField] = applyWindDisturbance(trajectory, windField)
%APPLYWINDDISTURBANCE Apply wind disturbance to a trajectory matrix.
%
% Usage:
%   wind = struct('vx', 1.5, 'vy', 1.0, 'gust_std', 0.3, 'gust_dir_std', 0.5);
%   disturbed = applyWindDisturbance(trajectory, wind);
%
% trajectory: [time, x, y, z, heading] matrix
% windField: struct with vx, vy, gust_std, gust_dir_std
%
% Returns disturbed trajectory with wind drift applied cumulatively.

if nargin < 2
    windField = struct('vx', 0, 'vy', 0, 'gust_std', 0, 'gust_dir_std', 0);
end

if windField.vx == 0 && windField.vy == 0 && windField.gust_std == 0
    disturbedTrajectory = trajectory;
    return;
end

rng(42);  % deterministic for reproducibility

n = size(trajectory, 1);
disturbedTrajectory = trajectory;

cumulativeDx = 0;
cumulativeDy = 0;

for i = 2:n
    dt = trajectory(i, 1) - trajectory(i-1, 1);
    if dt <= 0
        dt = 0.1;
    end

    % Constant wind drift
    dx = windField.vx * dt;
    dy = windField.vy * dt;

    % Random gust
    if windField.gust_std > 0
        gustMag = abs(randn() * windField.gust_std);
        gustAngle = 0;
        if isfield(windField, 'gust_dir_std') && windField.gust_dir_std > 0
            gustAngle = randn() * windField.gust_dir_std;
        end
        dx = dx + gustMag * cos(gustAngle) * dt;
        dy = dy + gustMag * sin(gustAngle) * dt;
    end

    cumulativeDx = cumulativeDx + dx;
    cumulativeDy = cumulativeDy + dy;

    disturbedTrajectory(i, 2) = disturbedTrajectory(i, 2) + cumulativeDx;
    disturbedTrajectory(i, 3) = disturbedTrajectory(i, 3) + cumulativeDy;
end

fprintf('Wind disturbance applied: vx=%.2f, vy=%.2f, gust=%.2f\n', ...
    windField.vx, windField.vy, windField.gust_std);
fprintf('  Max drift: dx=%.2fm, dy=%.2fm\n', cumulativeDx, cumulativeDy);
end
