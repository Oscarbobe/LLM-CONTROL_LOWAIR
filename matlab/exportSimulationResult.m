function exportSimulationResult(result, projectRoot)
%EXPORTSIMULATIONRESULT Export simulation results to data/simulation/.
%
% Exports three files:
%   data/simulation/latest_trajectory.csv  – time, x, y, z, heading
%   data/simulation/latest_result.json     – ok, safetyErrors, finalPose, totalTime
%   data/simulation/latest_figure.png      – current figure snapshot

simDir = fullfile(projectRoot, 'data', 'simulation');
if ~exist(simDir, 'dir')
    mkdir(simDir);
end

% --- CSV trajectory ---
csvPath = fullfile(simDir, 'latest_trajectory.csv');
writematrix(result.trajectory, csvPath);

% --- JSON result ---
jsonPath = fullfile(simDir, 'latest_result.json');
export = struct();
export.ok = result.ok;
export.safetyErrors = {result.safetyErrors};
export.finalPose = result.finalPose;
export.finalHeadingDeg = result.finalHeadingDeg;
export.airborne = result.airborne;
export.totalTime = result.trajectory(end, 1);

fid = fopen(jsonPath, 'w');
if fid == -1
    warning('Cannot open %s for writing.', jsonPath);
else
    fprintf(fid, '%s', jsonencode(export, 'PrettyPrint', true));
    fclose(fid);
end

% --- PNG figure ---
pngPath = fullfile(simDir, 'latest_figure.png');
saveas(gcf, pngPath);

fprintf('\nSimulation results exported to data/simulation/:\n');
fprintf('  %s\n', csvPath);
fprintf('  %s\n', jsonPath);
fprintf('  %s\n', pngPath);

end