# MATLAB 仿真运行指南

## 前置条件

- MATLAB R2019b 或更高版本（需要 `jsondecode` / `jsonencode` / `writematrix`）
- 已通过 Python 生成动作 JSON 文件

## 快速开始

### 1. 生成动作 JSON（Python 端）

在项目根目录运行：

```bash
cd /home/abc/桌面/SWING_CONTROL
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到果园上方悬停两秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json
```

其他常用指令：

```bash
# 巡视玉米地
PYTHONPATH=src python -m swing_control.app.map_route \
  "巡视玉米地" \
  --save-actions data/processed/instructions/map_last_actions.json

# 飞到水渠旁边
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到水渠旁边悬停一秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json
```

### 2. 在 MATLAB 中运行仿真

打开 MATLAB，在命令窗口输入：

```matlab
cd('/home/abc/桌面/SWING_CONTROL/matlab')
simulate_swing_actions
```

默认读取 `data/processed/instructions/interactive_last_actions.json`。
如需指定文件：

```matlab
simulate_swing_actions('../data/processed/instructions/map_last_actions.json')
```

## 预期输出

### 命令行输出

```
Swing MATLAB simulation
Action file: /home/abc/桌面/SWING_CONTROL/data/processed/instructions/map_last_actions.json
Map file:    /home/abc/桌面/SWING_CONTROL/data/maps/site_map.json

Action sequence:
  01. pre_flight_check: no pose change
  02. takeoff 5.00s to z=1.50m
  03. fly_forward 3.00s, distance 3.00m
  ...
  Simulation result: PASS. No boundary or no-fly-zone violation detected.

Simulation results exported to data/simulation/:
  .../data/simulation/latest_trajectory.csv
  .../data/simulation/latest_result.json
  .../data/simulation/latest_figure.png
```

### 图形窗口

- **蓝色轨迹线**：无人机飞行路径
- **黑色圆点**：起飞点 (origin)
- **绿色五角星 + 圆**：目标区域（果园、玉米地、水渠等）
- **红色虚线圆 + 阴影**：禁飞区（房屋、电线杆）

### 导出文件

| 文件 | 内容 |
|------|------|
| `data/simulation/latest_trajectory.csv` | 时间序列：time, x, y, z, heading |
| `data/simulation/latest_result.json` | 仿真结论：ok, safetyErrors, finalPose, totalTime |
| `data/simulation/latest_figure.png` | 三维轨迹图截图 |

## 单独使用工具函数

### actionsToTimeline — 动作 JSON 转时间序列

```matlab
actions = jsondecode(fileread('../data/processed/instructions/map_last_actions.json'));
siteMap = jsondecode(fileread('../data/maps/site_map.json'));
trajectory = actionsToTimeline(actions, siteMap);
% trajectory = [t, x, y, z, headingDeg] 矩阵，采样间隔 0.1s
```

### exportSimulationResult — 手动导出

```matlab
% result 必须是 simulate_swing_actions 的返回值
exportSimulationResult(result, '/home/abc/桌面/SWING_CONTROL')
```

## 常见问题

**Q: 提示 "Action file not found"**
→ 先运行 Python 端的 `map_route --save-actions` 命令生成动作 JSON。

**Q: 轨迹图不显示**
→ 确保 MATLAB 工作目录为 `matlab/`，且 `applySwingAction.m`、`checkMapSafety.m`、`plotSwingSimulation.m` 在同一目录下。

**Q: 仿真结果为 FAIL**
→ 检查命令行输出的具体原因（未降落、越界、进入禁飞区），调整指令或地图参数。

**Q: 没有 MATLAB GUI（纯命令行）**
→ 可以安装 GNU Octave，但部分函数（`jsonencode`、`writematrix`）需要适配。推荐使用 MATLAB 图形界面。