# Simulink 动态仿真指南

本目录保存 Simulink 动态仿真相关文件。Windows 上的完整操作步骤以根目录文档为准：

```text
MATLAB_SIMULINK_OPERATION_MANUAL.md
```

## 文件说明

```text
actionsToVelocityCmd.m          动作 JSON → 速度命令 velCmd
build_swing_simulink_model.m    自动构建 Simulink 模型
swing_language_control_sim.slx  已生成的 Simulink 动态模型
```

## 模型作用

`swing_language_control_sim.slx` 将动作序列转换成速度输入，通过三轴积分器得到位置曲线，并输出安全状态。

核心结构：

```text
velCmd
→ From Workspace
→ vx/vy/vz
→ Integrator
→ x/y/z
→ Scope / XY Graph / safeFlag
```

## Windows 推荐运行方式

在 MATLAB 中运行：

```matlab
projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR';
cd(projectRoot);
addpath(fullfile(projectRoot, 'simulink'));

actionsToVelocityCmd(fullfile('data', 'processed', 'instructions', 'map_last_actions.json'));
open_system(fullfile(projectRoot, 'simulink', 'swing_language_control_sim.slx'));
sim('swing_language_control_sim');
```

如果需要重新生成 `.slx`：

```matlab
cd(fullfile(projectRoot, 'simulink'));
build_swing_simulink_model;
```

## 验收标准

```text
velCmd 已出现在 MATLAB 工作区
Scope 中能看到 x/y/z 曲线
XY Graph 中能看到平面轨迹
safeFlag 正常路线保持 1
```

## 当前状态

```text
actionsToVelocityCmd.m 已存在
build_swing_simulink_model.m 已存在
swing_language_control_sim.slx 已存在
仍需在 Windows MATLAB/Simulink GUI 中实测运行
```

## 专有名词

```text
velCmd：
速度命令矩阵，通常为 [time, vx, vy, vz]。

Integrator：
积分器，把速度积分成位置。

safeFlag：
安全标志，1 表示安全，0 表示越界或进入禁飞区。

From Workspace：
Simulink 从 MATLAB 工作区读取变量的模块。
```
