function build_swing_simulink_model()
%BUILD_SWING_SIMULINK_MODEL Programmatically create the Swing Simulink model.
%
% Creates swing_language_control_sim.slx in the current directory.
% Run this once to generate the model, then open it in Simulink.
%
% Model architecture:
%   [From Workspace: velCmd] -> [Demux] -> [Integrators] -> [Mux] -> [Scope XYZ]
%                                              |                |
%                                         [XY Graph]    [Safety Check] -> [Display]
%                                                              |
%                                                         [Stop if Unsafe]

modelName = 'swing_language_control_sim';

if bdIsLoaded(modelName)
    close_system(modelName, 0);
end

new_system(modelName);
open_system(modelName);

% Block positions [left, top, right, bottom]
x0 = 30;  y0 = 30;
col = @(c) x0 + c * 150;
row = @(r) y0 + r * 60;

% From Workspace: velocity command input
add_block('simulink/Sources/From Workspace', [modelName '/From Workspace'], ...
    'Position', [col(0), row(1)-15, col(0)+60, row(1)+15]);
set_param([modelName '/From Workspace'], 'VariableName', 'velCmd');

% Demux: split [vx, vy, vz]
add_block('simulink/Signal Routing/Demux', [modelName '/Demux'], ...
    'Position', [col(1), row(0)-25, col(1)+10, row(2)+25]);
set_param([modelName '/Demux'], 'Outputs', '3');

% Integrators: vx->x, vy->y, vz->z
labels = {'x', 'y', 'z'};
initVals = {'siteMap.origin.x', 'siteMap.origin.y', 'siteMap.origin.z'};
for i = 1:3
    blockName = sprintf('Integrator %s', labels{i});
    add_block('simulink/Continuous/Integrator', [modelName '/' blockName], ...
        'Position', [col(2), row(i)-15, col(2)+30, row(i)+15]);
    set_param([modelName '/' blockName], 'InitialCondition', initVals{i});
end

% Mux: combine [x, y, z]
add_block('simulink/Signal Routing/Mux', [modelName '/Mux'], ...
    'Position', [col(3), row(0)-25, col(3)+10, row(2)+25]);
set_param([modelName '/Mux'], 'Inputs', '3');

% Scope: x, y, z over time
add_block('simulink/Sinks/Scope', [modelName '/Scope XYZ'], ...
    'Position', [col(4), row(1)-45, col(4)+40, row(1)+45]);
set_param([modelName '/Scope XYZ'], 'NumInputPorts', '3');

% XY Graph: 2D trajectory (x vs y)
add_block('simulink/Sinks/XY Graph', [modelName '/XY Graph'], ...
    'Position', [col(4), row(2)+30, col(4)+40, row(2)+70]);
set_param([modelName '/XY Graph'], 'xmin', '-10', 'xmax', '10', ...
    'ymin', '-10', 'ymax', '10');

% MATLAB Function: safety check
add_block('simulink/User-Defined Functions/MATLAB Function', ...
    [modelName '/Safety Check'], ...
    'Position', [col(3)+50, row(3)+50, col(3)+120, row(3)+110]);

% Display: safeFlag
add_block('simulink/Sinks/Display', [modelName '/Display safeFlag'], ...
    'Position', [col(4)+50, row(3)+50, col(4)+110, row(3)+80]);

% Stop Simulation: halt if unsafe
add_block('simulink/Sinks/Stop Simulation', [modelName '/Stop if Unsafe'], ...
    'Position', [col(4)+50, row(3)+100, col(4)+110, row(3)+130]);

% NOT logic: Stop when safeFlag == 0
add_block('simulink/Logic and Bit Operations/Logical Operator', ...
    [modelName '/NOT'], ...
    'Position', [col(4)+15, row(3)+80, col(4)+35, row(3)+110]);
set_param([modelName '/NOT'], 'Operator', 'NOT');

% ---- Wiring ----
add_line(modelName, 'From Workspace/1', 'Demux/1');
for i = 1:3
    add_line(modelName, sprintf('Demux/%d', i), ...
        sprintf('Integrator %s/1', labels{i}));
    add_line(modelName, sprintf('Integrator %s/1', labels{i}), ...
        sprintf('Mux/%d', i));
end
add_line(modelName, 'Mux/1', 'Scope XYZ/1');
add_line(modelName, 'Integrator x/1', 'XY Graph/1');
add_line(modelName, 'Integrator y/1', 'XY Graph/2');
add_line(modelName, 'Mux/1', 'Safety Check/1');
add_line(modelName, 'Safety Check/1', 'Display safeFlag/1');
add_line(modelName, 'Safety Check/1', 'NOT/1');
add_line(modelName, 'NOT/1', 'Stop if Unsafe/1');

% Write Safety Check MATLAB Function code
sf = sfroot;
mach = sf.find('-isa', 'Stateflow.Machine', 'Name', modelName);
if ~isempty(mach)
    chart = mach.find('-isa', 'Stateflow.EMChart');
    if ~isempty(chart)
        chart.Script = sprintf([ ...
            'function safeFlag = safetyCheck(pos)\n', ...
            '%% pos = [x, y, z]\n', ...
            'persistent mapData\n', ...
            'if isempty(mapData)\n', ...
            '    mapData = evalin(''base'', ''siteMap'');\n', ...
            'end\n', ...
            'safeFlag = 1;\n', ...
            'x = pos(1); y = pos(2); z = pos(3);\n', ...
            'if x < mapData.limits.min_x || x > mapData.limits.max_x\n', ...
            '    safeFlag = 0; return;\n', ...
            'end\n', ...
            'if y < mapData.limits.min_y || y > mapData.limits.max_y\n', ...
            '    safeFlag = 0; return;\n', ...
            'end\n', ...
            'if z < mapData.limits.min_z || z > mapData.limits.max_z\n', ...
            '    safeFlag = 0; return;\n', ...
            'end\n', ...
            'if isfield(mapData, ''no_fly_zones'')\n', ...
            '    zones = mapData.no_fly_zones;\n', ...
            '    for i = 1:numel(zones)\n', ...
            '        zone = zones(i);\n', ...
            '        protectedR = zone.radius_m + zone.buffer_m;\n', ...
            '        dist = hypot(x - zone.center.x, y - zone.center.y);\n', ...
            '        if dist <= protectedR\n', ...
            '            safeFlag = 0; return;\n', ...
            '        end\n', ...
            '    end\n', ...
            'end\n', ...
            'end\n' ...
        ]);
    end
end

% Configure model
set_param(modelName, 'StopTime', 'simDuration');
set_param(modelName, 'Solver', 'ode4');
set_param(modelName, 'FixedStep', '0.1');

% Add annotation
annotationText = sprintf('Swing Language Control Simulink Model\nVelocity cmd -> Integrators -> Position -> Safety Check');
Simulink.Annotation([modelName '/ModelInfo'], 'Text', annotationText, ...
    'Position', [col(1), row(3)+130, col(4), row(3)+160]);

save_system(modelName);
fprintf('Simulink model saved: %s.slx\n', modelName);
fprintf('Model blocks:\n');
fprintf('  From Workspace (velCmd) -> Demux -> 3x Integrator -> Mux\n');
fprintf('  -> Scope XYZ (x,y,z over time)\n');
fprintf('  -> XY Graph (x vs y top-down view)\n');
fprintf('  -> Safety Check (MATLAB Function) -> Display safeFlag\n');
fprintf('  -> NOT -> Stop Simulation (halts if safeFlag=0)\n');
fprintf('\nTo run:\n');
fprintf('  1. actionsToVelocityCmd\n');
fprintf('  2. sim(''%s'')\n', modelName);
end
