function [state, samples, description] = applySwingAction(state, action, siteMap)
%APPLYSWINGACTION Convert one Swing action into simulated pose samples.

tool = string(action.tool);
params = action.parameters;
dt = 0.1;
samples = [];
description = tool;

switch tool
    case "pre_flight_check"
        description = "pre_flight_check: no pose change";

    case "get_status"
        description = "get_status: no pose change";

    case "takeoff"
        duration = getParam(params, "duration_s", siteMap.flight.takeoff_duration_s);
        startPose = state.pose;
        endPose = [state.pose(1), state.pose(2), siteMap.flight.safe_height_m];
        state.airborne = true;
        [state, samples] = moveLinear(state, startPose, endPose, duration, dt);
        description = sprintf("takeoff %.2fs to z=%.2fm", duration, endPose(3));

    case "land"
        duration = getParam(params, "duration_s", siteMap.flight.land_duration_s);
        startPose = state.pose;
        endPose = [state.pose(1), state.pose(2), siteMap.origin.z];
        [state, samples] = moveLinear(state, startPose, endPose, duration, dt);
        state.airborne = false;
        description = sprintf("land %.2fs to z=%.2fm", duration, endPose(3));

    case "hover"
        duration = getParam(params, "duration_s", siteMap.flight.default_hover_s);
        [state, samples] = holdPose(state, duration, dt);
        description = sprintf("hover %.2fs", duration);

    case {"fly_forward", "fly_backward", "fly_left", "fly_right", "fly_up", "fly_down"}
        duration = getParam(params, "duration_s", 1);
        mps = siteMap.flight.meters_per_second;
        delta = actionDelta(tool, duration * mps);
        startPose = state.pose;
        endPose = state.pose + delta;
        [state, samples] = moveLinear(state, startPose, endPose, duration, dt);
        description = sprintf("%s %.2fs, distance %.2fm", tool, duration, norm(delta));

    case "turn_left"
        duration = getParam(params, "duration_s", 1);
        yaw = getParam(params, "yaw", 20);
        state.headingDeg = state.headingDeg - duration * yaw;
        [state, samples] = holdPose(state, duration, dt);
        description = sprintf("turn_left %.2fs, yaw %.2f", duration, yaw);

    case "turn_right"
        duration = getParam(params, "duration_s", 1);
        yaw = getParam(params, "yaw", 20);
        state.headingDeg = state.headingDeg + duration * yaw;
        [state, samples] = holdPose(state, duration, dt);
        description = sprintf("turn_right %.2fs, yaw %.2f", duration, yaw);

    case {"switch_plane_forward", "switch_quadricopter"}
        description = sprintf("%s: mode switch only in simulation", tool);

    case "error"
        message = "";
        if isfield(params, "message")
            message = string(params.message);
        end
        description = sprintf("error action: %s", message);

    otherwise
        description = sprintf("unsupported action ignored: %s", tool);
end
end

function value = getParam(params, name, defaultValue)
if isfield(params, name)
    value = double(params.(name));
else
    value = double(defaultValue);
end
end

function delta = actionDelta(tool, distance)
delta = [0, 0, 0];
switch tool
    case "fly_forward"
        delta(1) = distance;
    case "fly_backward"
        delta(1) = -distance;
    case "fly_right"
        delta(2) = distance;
    case "fly_left"
        delta(2) = -distance;
    case "fly_up"
        delta(3) = distance;
    case "fly_down"
        delta(3) = -distance;
end
end

function [state, samples] = moveLinear(state, startPose, endPose, duration, dt)
if duration <= 0
    state.pose = endPose;
    samples = [state.time, state.pose, state.headingDeg];
    return;
end

steps = max(1, ceil(duration / dt));
samples = zeros(steps, 5);
for i = 1:steps
    alpha = i / steps;
    state.time = state.time + duration / steps;
    state.pose = startPose + alpha * (endPose - startPose);
    samples(i, :) = [state.time, state.pose, state.headingDeg];
end
end

function [state, samples] = holdPose(state, duration, dt)
steps = max(1, ceil(duration / dt));
samples = zeros(steps, 5);
for i = 1:steps
    state.time = state.time + duration / steps;
    samples(i, :) = [state.time, state.pose, state.headingDeg];
end
end
