function result = simulate_swing_actions(actionFile)
%SIMULATE_SWING_ACTIONS Simulate Swing action JSON without real hardware.
%
% Usage in MATLAB:
%   cd('/home/abc/桌面/LLM-CONTROL_LOWAIR/matlab')
%   simulate_swing_actions
%
% Optional:
%   simulate_swing_actions('../data/processed/instructions/voice_last_actions.json')

if nargin < 1 || strlength(string(actionFile)) == 0
    actionFile = "../data/processed/instructions/interactive_last_actions.json";
end

scriptDir = fileparts(mfilename("fullpath"));
projectRoot = fileparts(scriptDir);
actionPath = normalizePath(projectRoot, actionFile);
mapPath = fullfile(projectRoot, "data", "maps", "site_map.json");

if ~isfile(actionPath)
    error("Action file not found: %s\nRun ./model/run_swing_interactive.sh --no-log first.", actionPath);
end

if ~isfile(mapPath)
    error("Map file not found: %s", mapPath);
end

actions = jsondecode(fileread(actionPath));
siteMap = jsondecode(fileread(mapPath));

state.pose = [siteMap.origin.x, siteMap.origin.y, siteMap.origin.z];
state.headingDeg = 0;
state.airborne = false;
state.time = 0;

trajectory = [state.time, state.pose, state.headingDeg];
safetyErrors = strings(0, 1);
actionLog = strings(0, 1);

fprintf("Swing MATLAB simulation\n");
fprintf("Action file: %s\n", actionPath);
fprintf("Map file:    %s\n\n", mapPath);

for index = 1:numel(actions)
    action = actions(index);
    [state, samples, description] = applySwingAction(state, action, siteMap);
    actionLog(end + 1, 1) = sprintf("%02d. %s", index, description); %#ok<AGROW>

    if ~isempty(samples)
        trajectory = [trajectory; samples]; %#ok<AGROW>
    else
        trajectory = [trajectory; state.time, state.pose, state.headingDeg]; %#ok<AGROW>
    end

    for row = 1:size(samples, 1)
        errors = checkMapSafety(samples(row, 2:4), siteMap);
        if ~isempty(errors)
            for e = 1:numel(errors)
                safetyErrors(end + 1, 1) = sprintf("t=%.2fs %s", samples(row, 1), errors(e)); %#ok<AGROW>
            end
        end
    end
end

finalErrors = checkMapSafety(state.pose, siteMap);
if ~isempty(finalErrors)
    for e = 1:numel(finalErrors)
        safetyErrors(end + 1, 1) = sprintf("final %s", finalErrors(e)); %#ok<AGROW>
    end
end

plotSwingSimulation(siteMap, trajectory, actionLog);

result.actionFile = actionPath;
result.mapFile = mapPath;
result.actions = actions;
result.trajectory = trajectory;
result.finalPose = state.pose;
result.finalHeadingDeg = state.headingDeg;
result.airborne = state.airborne;
result.safetyErrors = unique(safetyErrors);
result.ok = isempty(result.safetyErrors) && ~state.airborne && abs(state.pose(3) - siteMap.origin.z) < 1e-6;

exportSimulationResult(result, projectRoot);

fprintf("\nAction sequence:\n");
for i = 1:numel(actionLog)
    fprintf("  %s\n", actionLog(i));
end

fprintf("\nFinal pose: x=%.2f, y=%.2f, z=%.2f, heading=%.1f deg\n", ...
    state.pose(1), state.pose(2), state.pose(3), state.headingDeg);
fprintf("Total simulated time: %.2fs\n", state.time);

if result.ok
    fprintf("Simulation result: PASS. No boundary or no-fly-zone violation detected.\n");
else
    fprintf("Simulation result: FAIL or NEED REVIEW.\n");
    if state.airborne
        fprintf("  - Final state is still airborne. The action sequence should include land.\n");
    end
    if abs(state.pose(3) - siteMap.origin.z) >= 1e-6
        fprintf("  - Final altitude is not at origin height.\n");
    end
    for i = 1:numel(result.safetyErrors)
        fprintf("  - %s\n", result.safetyErrors(i));
    end
end
end

function path = normalizePath(projectRoot, maybeRelative)
candidate = string(maybeRelative);
if startsWith(candidate, "/")
    path = char(candidate);
else
    path = fullfile(projectRoot, char(candidate));
end
path = char(java.io.File(path).getCanonicalPath());
end
