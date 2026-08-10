function actionsToVelocityCmd(actionFile, mapFile)
%ACTIONSTOVELOCITYCMD Convert Swing action JSON to velocity command time series.
%
% Usage:
%   actionsToVelocityCmd('data/processed/instructions/map_last_actions.json', ...
%                        'data/maps/site_map.json')
%
% Returns velocity command matrix in base workspace as 'velCmd':
%   velCmd = [t, vx, vy, vz]  (meters/second)
%
% This is the input signal for the Simulink model swing_language_control_sim.

if nargin < 1
    actionFile = 'data/processed/instructions/map_last_actions.json';
end
if nargin < 2
    mapFile = 'data/maps/site_map.json';
end

scriptDir = fileparts(mfilename('fullpath'));
projectRoot = fileparts(scriptDir);
actionPath = fullfile(projectRoot, actionFile);
mapPath = fullfile(projectRoot, mapFile);

if ~isfile(actionPath)
    error('Action file not found: %s', actionPath);
end
if ~isfile(mapPath)
    error('Map file not found: %s', mapPath);
end

actions = jsondecode(fileread(actionPath));
siteMap = jsondecode(fileread(mapPath));

dt = 0.1;
mps = siteMap.flight.meters_per_second;

state.pose = [siteMap.origin.x, siteMap.origin.y, siteMap.origin.z];
state.headingDeg = 0;
state.airborne = false;
state.time = 0;

velCmd = [0, 0, 0, 0];  % [t, vx, vy, vz]

for idx = 1:numel(actions)
    action = actions(idx);
    tool = string(action.tool);
    params = action.parameters;

    switch tool
        case {'pre_flight_check', 'get_status', 'error'}
            velCmd(end+1, :) = [state.time, 0, 0, 0]; %#ok<AGROW>

        case 'takeoff'
            duration = getParam(params, 'duration_s', siteMap.flight.takeoff_duration_s);
            vz = siteMap.flight.safe_height_m / duration;
            steps = max(1, ceil(duration / dt));
            for i = 1:steps
                state.time = state.time + dt;
                velCmd(end+1, :) = [state.time, 0, 0, vz]; %#ok<AGROW>
            end
            state.airborne = true;
            state.pose(3) = siteMap.flight.safe_height_m;

        case 'land'
            duration = getParam(params, 'duration_s', siteMap.flight.land_duration_s);
            vz = -siteMap.flight.safe_height_m / duration;
            steps = max(1, ceil(duration / dt));
            for i = 1:steps
                state.time = state.time + dt;
                velCmd(end+1, :) = [state.time, 0, 0, vz]; %#ok<AGROW>
            end
            state.airborne = false;
            state.pose(3) = 0;

        case 'hover'
            duration = getParam(params, 'duration_s', siteMap.flight.default_hover_s);
            steps = max(1, ceil(duration / dt));
            for i = 1:steps
                state.time = state.time + dt;
                velCmd(end+1, :) = [state.time, 0, 0, 0]; %#ok<AGROW>
            end

        case {'fly_forward', 'fly_backward', 'fly_left', 'fly_right', 'fly_up', 'fly_down'}
            duration = getParam(params, 'duration_s', 1);
            delta = actionDelta(tool, duration * mps) / duration;
            steps = max(1, ceil(duration / dt));
            for i = 1:steps
                state.time = state.time + dt;
                velCmd(end+1, :) = [state.time, delta(1), delta(2), delta(3)]; %#ok<AGROW>
            end

        case {'turn_left', 'turn_right', 'switch_plane_forward', 'switch_quadricopter'}
            duration = getParam(params, 'duration_s', 1);
            steps = max(1, ceil(duration / dt));
            for i = 1:steps
                state.time = state.time + dt;
                velCmd(end+1, :) = [state.time, 0, 0, 0]; %#ok<AGROW>
            end

        otherwise
            velCmd(end+1, :) = [state.time, 0, 0, 0]; %#ok<AGROW>
    end
end

assignin('base', 'velCmd', velCmd);
assignin('base', 'siteMap', siteMap);
assignin('base', 'simDuration', state.time);

fprintf('Velocity command generated: %d samples, %.2fs duration\n', size(velCmd, 1), state.time);
fprintf('Workspace variables ready: velCmd, siteMap, simDuration\n');
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
    case 'fly_forward'
        delta(1) = distance;
    case 'fly_backward'
        delta(1) = -distance;
    case 'fly_right'
        delta(2) = distance;
    case 'fly_left'
        delta(2) = -distance;
    case 'fly_up'
        delta(3) = distance;
    case 'fly_down'
        delta(3) = -distance;
end
end
