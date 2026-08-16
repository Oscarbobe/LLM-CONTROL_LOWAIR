# MATLAB 脚本仿真指南

本目录保存 MATLAB 脚本仿真文件。Windows 上的完整操作步骤以根目录文档为准：

```text
MATLAB_SIMULINK_OPERATION_MANUAL.md
```

## 文件说明

```text
simulate_swing_actions.m     主入口，读取动作 JSON 和地图 JSON
applySwingAction.m           将动作转换为位姿变化
checkMapSafety.m             检查边界和禁飞区
plotSwingSimulation.m        绘制三维轨迹图
actionsToTimeline.m          动作序列转时间序列
applyWindDisturbance.m       风扰动模拟
exportSimulationResult.m     导出 CSV、JSON、PNG
```

## Windows 推荐运行方式

先在 PowerShell 中生成动作 JSON：

```powershell
$projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR'
Set-Location -LiteralPath $projectRoot
$env:PYTHONPATH = (Join-Path $projectRoot 'src')
python -m swing_control.app.map_route `
  '飞到果园上方悬停两秒再降落' `
  --save-actions '.\data\processed\instructions\map_last_actions.json'
```

然后在 MATLAB 中运行：

```matlab
projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR';
cd(projectRoot);
addpath(fullfile(projectRoot, 'matlab'));
result = simulate_swing_actions(fullfile('data', 'processed', 'instructions', 'map_last_actions.json'));
```

## 预期输出

MATLAB 命令窗口应输出：

```text
Action sequence
Final pose
Total simulated time
Simulation result: PASS 或 FAIL
```

图形窗口应显示：

```text
蓝色轨迹线
起飞点
目标区域
禁飞区
```

运行成功后应生成：

```text
data/simulation/latest_trajectory.csv
data/simulation/latest_result.json
data/simulation/latest_figure.png
```

## 当前状态

```text
MATLAB 仿真代码已具备
导出代码已具备
仍需在 Windows MATLAB GUI 中实测运行并确认 data/simulation 输出
```

## 常见问题

如果提示找不到函数：

```matlab
addpath(fullfile(projectRoot, 'matlab'));
```

如果提示找不到动作 JSON：

```text
先运行 PowerShell 中的 map_route --save-actions 命令。
```

如果仿真结果为 FAIL：

```text
查看 result.safetyErrors，检查路线是否越界或进入禁飞区。
```
