function trajectory = actionsToTimeline(actions, siteMap)
%ACTIONSTOTIMELINE Convert Swing action JSON into uniform time-series trajectory.
%
% Usage:
%   actions = jsondecode(fileread('data/processed/instructions/map_last_actions.json'));
%   siteMap = jsondecode(fileread('data/maps/site_map.json'));
%   trajectory = actionsToTimeline(actions, siteMap);
%
% Returns matrix [time, x, y, z, headingDeg] with sample interval dt = 0.1s.

dt = 0.1;

state.pose = [siteMap.origin.x, siteMap.origin.y, siteMap.origin.z];
state.headingDeg = 0;
state.airborne = false;
state.time = 0;

trajectory = [state.time, state.pose, state.headingDeg];

for index = 1:numel(actions)
    action = actions(index);
    [state, samples] = applySwingAction(state, action, siteMap);

    if ~isempty(samples)
        trajectory = [trajectory; samples]; %#ok<AGROW>
    else
        trajectory = [trajectory; state.time, state.pose, state.headingDeg]; %#ok<AGROW>
    end
end

end