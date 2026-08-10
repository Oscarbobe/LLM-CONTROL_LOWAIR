# Simulink 动态仿真模型

## 概述

`swing_language_control_sim.slx` 是一个 Simulink 动态模型，将 Swing 动作 JSON 转换为速度命令，通过三轴积分器模拟无人机位置变化，并实时进行安全检查。

## 模型架构

```
┌─────────────────┐     ┌─────────┐     ┌──────────────┐     ┌───────┐     ┌───────────┐
│ From Workspace  │────▶│  Demux  │────▶│ 3 Integrators │────▶│  Mux  │────▶│ Scope XYZ │
│   velCmd        │     │ vx,vy,vz│     │  vx→x vy→y   │     │ x,y,z │     │ x,y,z(t)  │
│ [t, vx, vy, vz] │     └─────────┘     │  vz→z        │     └───┬───┘     └───────────┘
└─────────────────┘                     └──────┬───────┘         │
                                         x,y   │                 │
                                               ▼                 ▼
                                        ┌──────────┐    ┌──────────────┐
                                        │ XY Graph │    │ Safety Check │
                                        │  x vs y  │    │  MATLAB Fcn  │
                                        └──────────┘    └──────┬───────┘
                                                               │ safeFlag
                                                          ┌────┴────┐
                                                          │ Display │
                                                          └────┬────┘
                                                               │
                                                          ┌────┴──────────┐
                                                          │ NOT → Stop    │
                                                          │ if safeFlag=0 │
                                                          └───────────────┘
```

### 模块说明

| 模块 | 类型 | 功能 |
|------|------|------|
| From Workspace | 输入 | 读取 `velCmd` 矩阵 `[t, vx, vy, vz]` |
| Demux | 信号路由 | 将速度向量拆分为 vx, vy, vz 三路 |
| Integrator x/y/z | 连续积分器 | 对速度积分得到位置，初始条件为地图原点 |
| Mux | 信号路由 | 合并 x, y, z 为一路信号 |
| Scope XYZ | 示波器 | 显示 x, y, z 随时间变化的三通道曲线 |
| XY Graph | 二维图 | 显示 x-y 平面轨迹（俯视图） |
| Safety Check | MATLAB Function | 检查位置是否越界/进入禁飞区，返回 safeFlag |
| Display safeFlag | 数字显示 | 实时显示安全标志（1=安全, 0=危险） |
| NOT + Stop | 逻辑+停止 | safeFlag=0 时自动停止仿真 |

## 前置条件

- MATLAB R2019b+ 含 Simulink
- 已通过 Python 生成动作 JSON 文件

## 使用方法

### 1. 生成动作 JSON

```bash
cd /home/abc/桌面/SWING_CONTROL
make map-demo
```

### 2. 构建 Simulink 模型（首次）

在 MATLAB 命令窗口：

```matlab
cd('/home/abc/桌面/SWING_CONTROL/simulink')
build_swing_simulink_model
```

这会生成 `swing_language_control_sim.slx`。

### 3. 运行仿真

```matlab
% 加载动作数据到工作区
actionsToVelocityCmd('../data/processed/instructions/map_last_actions.json')

% 打开模型并运行
open_system('swing_language_control_sim')
sim('swing_language_control_sim')
```

### 4. 测试不同指令

```matlab
% 正常路线：飞到果园
actionsToVelocityCmd('../data/processed/instructions/map_last_actions.json')
sim('swing_language_control_sim')
% 预期：safeFlag = 1，仿真完成

% 危险路线（手动构造越界动作）
% 预期：safeFlag 变为 0，仿真自动停止
```

## 验收标准

| 验收项 | 预期结果 |
|--------|----------|
| Scope XYZ 显示 | x, y, z 三条曲线随时间变化 |
| XY Graph 显示 | 二维俯视轨迹，可看到起点→目标→降落 |
| 正常路线 safeFlag | 始终为 1，仿真正常完成 |
| 危险路线 safeFlag | 进入禁飞区/越界时变为 0，仿真自动停止 |
| 积分器初始条件 | x=y=z=0（地图原点） |

## 文件清单

| 文件 | 说明 |
|------|------|
| `build_swing_simulink_model.m` | 构建 Simulink 模型的脚本 |
| `actionsToVelocityCmd.m` | 动作 JSON → 速度命令时间序列 |
| `swing_language_control_sim.slx` | 生成的 Simulink 模型文件 |
| `README.md` | 本文档 |

## 与 MATLAB 脚本仿真的关系

| 对比维度 | MATLAB 脚本 (`simulate_swing_actions.m`) | Simulink 模型 |
|----------|----------------------------------------|---------------|
| 仿真方式 | 循环遍历动作，逐步更新状态 | 连续积分器，实时求解 |
| 可视化 | 静态 3D 图 (`plot3`) | 动态 Scope + XY Graph |
| 安全检查 | 每步采样后检查 | 实时连续检查，不安全时立即停止 |
| 导出 | CSV/JSON/PNG | 通过 Scope 记录数据 |
| 适用场景 | 离线分析、报告生成 | 动态演示、实时监控 |

两者互补：MATLAB 脚本用于离线分析和结果导出，Simulink 模型用于动态展示和答辩演示。