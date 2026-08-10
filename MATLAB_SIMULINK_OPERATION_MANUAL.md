# MATLAB/Simulink 操作手册

本文档只说明需要在 MATLAB/Simulink 中完成的操作，用于把本项目从“Python 生成动作 JSON”推进到“MATLAB/Simulink 仿真验证”。

当前项目主线：

```text
中文/语音指令
→ Python 生成动作 JSON
→ MATLAB 脚本仿真轨迹
→ Simulink 动态仿真
→ 输出安全结论
→ 真机执行作为可选验证
```

## 一、操作前准备

### 1. 确认项目目录

项目路径：

```text
/home/abc/桌面/SWING_CONTROL
```

后续 MATLAB 中都围绕这个目录操作。

### 2. 先在 Python 端生成动作 JSON

在终端运行：

```bash
cd /home/abc/桌面/SWING_CONTROL
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到果园上方悬停两秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json
```

也可以用 Makefile：

```bash
cd /home/abc/桌面/SWING_CONTROL
make map-demo
```

生成文件：

```text
data/processed/instructions/map_last_actions.json
```

为什么要做这一步：

```text
MATLAB 不负责理解中文。
Python 端负责把中文指令转换为结构化动作 JSON。
MATLAB/Simulink 只读取这个 JSON 做仿真。
```

专有名词解释：

```text
动作 JSON：
一种结构化动作列表。例如 takeoff、fly_forward、hover、land。
它是自然语言和仿真/真机执行之间的中间格式。

dry-run：
只生成和预览动作，不连接无人机，不执行真机飞行。

map_route：
本项目的地图路线规划入口，把“飞到果园”等地图指令转换为动作序列。
```

### 3. 确认 MATLAB 版本

建议使用：

```text
MATLAB R2019b 或更高版本
Simulink 工具箱
```

为什么需要这个版本：

```text
项目中的 MATLAB 脚本使用 jsondecode、jsonencode、writematrix 等函数。
这些函数在较新的 MATLAB 版本中更稳定。
Simulink 动态仿真需要额外安装 Simulink。
```

专有名词解释：

```text
MATLAB：
矩阵计算和工程仿真软件，本项目用它读取动作 JSON、计算轨迹、画图和导出结果。

Simulink：
MATLAB 的图形化动态系统仿真工具。本项目用它搭建速度输入、积分器、轨迹显示和安全检查模型。

jsondecode：
MATLAB 中把 JSON 文本转换为结构体/数组的函数。

writematrix：
MATLAB 中把矩阵保存为 CSV 等表格文件的函数。
```

## 二、MATLAB 脚本仿真

MATLAB 脚本仿真是第一优先级。它比 Simulink 更容易跑通，适合今晚展示、论文截图和结果导出。

### 步骤 1：打开 MATLAB

从桌面或应用菜单打开 MATLAB。

如果是在 MATLAB 命令窗口中操作，不要使用 Linux 终端命令格式。

为什么要做这一步：

```text
当前 shell 中没有检测到 matlab 或 octave 命令。
所以建议从图形界面打开 MATLAB，而不是在终端中直接运行 matlab。
```

### 步骤 2：切换到 MATLAB 脚本目录

在 MATLAB 命令窗口输入：

```matlab
cd('/home/abc/桌面/SWING_CONTROL/matlab')
```

为什么要做这一步：

```text
simulate_swing_actions.m 会调用同目录下的其他函数：
applySwingAction.m
checkMapSafety.m
plotSwingSimulation.m
exportSimulationResult.m

如果工作目录不对，MATLAB 可能找不到这些函数。
```

专有名词解释：

```text
工作目录：
MATLAB 当前执行命令时所在的文件夹。
函数搜索路径：
MATLAB 查找 .m 文件函数的位置。当前目录中的函数通常可以直接调用。
```

### 步骤 3：运行主仿真入口

在 MATLAB 命令窗口输入：

```matlab
simulate_swing_actions('../data/processed/instructions/map_last_actions.json')
```

如果不传参数：

```matlab
simulate_swing_actions
```

默认会读取：

```text
data/processed/instructions/interactive_last_actions.json
```

推荐使用显式参数：

```matlab
simulate_swing_actions('../data/processed/instructions/map_last_actions.json')
```

为什么要做这一步：

```text
这是 MATLAB 脚本仿真的主入口。
它会读取动作 JSON 和地图 JSON，然后模拟无人机从起飞到降落的完整轨迹。
```

涉及文件：

```text
matlab/simulate_swing_actions.m
data/processed/instructions/map_last_actions.json
data/maps/site_map.json
```

专有名词解释：

```text
主入口：
用户直接运行的第一个函数，负责组织整个流程。

site_map.json：
地图文件，包含起飞点、目标区域、禁飞区、地图边界等信息。

trajectory：
轨迹，表示无人机随时间变化的位置点序列。
```

### 步骤 4：查看 MATLAB 命令行输出

正常情况下，命令窗口会输出类似内容：

```text
Swing MATLAB simulation
Action file: ...
Map file: ...

Action sequence:
  01. pre_flight_check: no pose change
  02. takeoff 5.00s to z=1.50m
  03. fly_forward 1.50s, distance 1.50m
  ...

Final pose: x=..., y=..., z=...
Total simulated time: ...
Simulation result: PASS
```

为什么要看这部分：

```text
命令行输出用于确认动作是否按顺序执行。
如果仿真失败，错误原因也会显示在这里。
```

专有名词解释：

```text
PASS：
仿真通过，表示未越界、未进入禁飞区，并完成降落。

FAIL：
仿真失败或需要检查，可能原因包括越界、进入禁飞区、最后未降落等。

Final pose：
最终位置，通常应该回到地面高度。

Total simulated time：
仿真总时间，由所有动作持续时间累加得到。
```

### 步骤 5：查看三维轨迹图

运行成功后会弹出图形窗口。

图中元素含义：

```text
蓝色线：无人机仿真飞行轨迹
黑色点：起飞点 origin
绿色目标点/区域：果园、玉米地、水渠等任务目标
红色虚线圆：禁飞区保护范围
红色半透明区域：禁飞区危险范围
```

为什么要看轨迹图：

```text
轨迹图可以直观看出无人机是否绕开禁飞区，是否到达目标区域，是否超出地图范围。
这比只看动作 JSON 更适合展示和答辩。
```

专有名词解释：

```text
三维轨迹：
用 x、y、z 三个坐标表示的飞行路径。

origin：
坐标原点，也就是起飞点。

no-fly zone：
禁飞区，表示无人机不能进入的区域。

buffer：
安全缓冲区。实际障碍物半径之外再扩一圈，避免贴边飞行。
```

### 步骤 6：检查导出结果

仿真成功后，到项目目录查看：

```text
data/simulation/
```

应生成：

```text
data/simulation/latest_trajectory.csv
data/simulation/latest_result.json
data/simulation/latest_figure.png
```

为什么要导出：

```text
CSV 可以保存轨迹数据。
JSON 可以保存安全结论。
PNG 可以保存仿真图，用于论文、汇报和答辩。
```

专有名词解释：

```text
CSV：
表格文本文件，适合保存时间、x、y、z、高度、航向角等轨迹数据。

JSON：
结构化文本文件，适合保存仿真是否通过、错误列表、最终位置等结果。

PNG：
图片文件，适合保存轨迹图。
```

### 步骤 7：打开导出的结果文件

可以在 MATLAB 中输入：

```matlab
readmatrix('../data/simulation/latest_trajectory.csv')
```

也可以直接用文件管理器打开：

```text
/home/abc/桌面/SWING_CONTROL/data/simulation/latest_figure.png
```

为什么要做这一步：

```text
确认仿真结果真的落盘，而不是只在 MATLAB 窗口中显示。
有导出文件，后续写文档、截图、展示都会更稳。
```

## 三、MATLAB 工具函数说明

这些函数一般不需要单独运行，但需要知道它们各自做什么。

### 1. simulate_swing_actions.m

作用：

```text
主仿真入口。
读取动作 JSON。
读取地图 JSON。
调用动作更新、安全检查、绘图和结果导出函数。
```

为什么重要：

```text
这是 MATLAB 仿真的总控脚本。
```

### 2. applySwingAction.m

作用：

```text
把单个动作转换成位置变化。
例如 fly_forward 1.5 秒会让 x 坐标增加一定距离。
```

为什么重要：

```text
它相当于 MATLAB 里的虚拟无人机执行器。
真机中是 pyparrot 执行动作，仿真中是这个函数更新 pose。
```

专有名词解释：

```text
pose：
位姿，通常包含位置和朝向。本项目中主要使用 [x, y, z] 和 headingDeg。

headingDeg：
航向角，单位是度，表示无人机朝向。
```

### 3. checkMapSafety.m

作用：

```text
检查当前位置是否越界。
检查当前位置是否进入禁飞区。
返回安全错误列表。
```

为什么重要：

```text
它是 MATLAB 仿真中的安全监控模块。
即使 Python 已经做过动作校验，MATLAB 仍要根据实际轨迹再检查一次。
```

### 4. plotSwingSimulation.m

作用：

```text
画出目标区域、禁飞区、起飞点和飞行轨迹。
```

为什么重要：

```text
它让项目从“代码输出”变成“可视化展示”。
```

### 5. actionsToTimeline.m

作用：

```text
把动作 JSON 转换成时间序列轨迹。
```

为什么重要：

```text
Simulink 更适合处理随时间变化的信号。
时间序列是动作 JSON 和 Simulink 动态模型之间的桥梁。
```

专有名词解释：

```text
时间序列：
按时间排列的数据。例如 t=0s、t=0.1s、t=0.2s 时无人机在哪里。
```

### 6. exportSimulationResult.m

作用：

```text
导出轨迹 CSV、结果 JSON 和仿真图片 PNG。
```

为什么重要：

```text
它让仿真结果可以被保存、提交和复现。
```

### 7. applyWindDisturbance.m

作用：

```text
给仿真轨迹加入风扰动或位置偏移。
```

为什么重要：

```text
真实无人机飞行会受到风、误差和控制延迟影响。
加入扰动可以让仿真更接近真实场景。
```

专有名词解释：

```text
风扰动：
风对无人机位置造成的偏移。

误差模型：
用数学方式模拟真实系统中的不确定性。
```

## 四、Simulink 动态仿真

Simulink 是第二优先级。先确保 MATLAB 脚本仿真跑通，再做 Simulink。

### 步骤 1：切换到 Simulink 目录

在 MATLAB 命令窗口输入：

```matlab
cd('/home/abc/桌面/SWING_CONTROL/simulink')
```

为什么要做这一步：

```text
Simulink 构建脚本 build_swing_simulink_model.m 在 simulink/ 目录下。
切换目录后可以直接运行该脚本。
```

### 步骤 2：生成 Simulink 模型

运行：

```matlab
build_swing_simulink_model
```

预期生成：

```text
simulink/swing_language_control_sim.slx
```

为什么要做这一步：

```text
当前项目中保存的是“生成模型的脚本”，不是已经生成好的 .slx 模型。
运行脚本后，MATLAB 会自动搭建 Simulink 模型。
```

专有名词解释：

```text
.slx：
Simulink 模型文件格式。可以双击打开，里面是图形化仿真模块。

构建脚本：
用 MATLAB 代码自动创建 Simulink 模型的脚本。
```

### 步骤 3：把动作 JSON 转成速度命令

运行：

```matlab
actionsToVelocityCmd('../data/processed/instructions/map_last_actions.json')
```

运行后，MATLAB 工作区中应出现：

```text
velCmd
```

为什么要做这一步：

```text
Simulink 不直接读取动作 JSON 中的 takeoff、fly_forward 等字符串。
Simulink 更适合读取数值信号。
所以需要把动作转换为速度命令 vx、vy、vz。
```

专有名词解释：

```text
velCmd：
velocity command 的缩写，速度命令。
通常格式是 [time, vx, vy, vz]。

vx：
x 方向速度。

vy：
y 方向速度。

vz：
z 方向速度，也就是上升或下降速度。
```

### 步骤 4：打开 Simulink 模型

运行：

```matlab
open_system('swing_language_control_sim')
```

为什么要做这一步：

```text
打开模型后可以看到 From Workspace、Integrator、Scope、XY Graph、Safety Check 等模块。
这适合展示模型结构。
```

专有名词解释：

```text
From Workspace：
从 MATLAB 工作区读取变量的 Simulink 输入模块。

Workspace：
MATLAB 当前内存变量区域。例如 velCmd 就存在工作区中。

Scope：
Simulink 中显示信号曲线的示波器模块。

XY Graph：
显示 x-y 平面轨迹的图形模块。
```

### 步骤 5：运行 Simulink 仿真

运行：

```matlab
sim('swing_language_control_sim')
```

也可以在 Simulink 窗口中点击 Run。

为什么要做这一步：

```text
这一步会让 Simulink 按时间推进仿真。
速度命令经过积分器后变成位置曲线。
安全检查模块会实时判断是否越界或进入禁飞区。
```

专有名词解释：

```text
sim：
MATLAB 中运行 Simulink 模型的函数。

Integrator：
积分器。把速度积分成位置。
数学上是 x(t) = x(0) + ∫vx(t)dt。

safeFlag：
安全标志。1 表示安全，0 表示危险。
```

### 步骤 6：查看 Scope 和 XY Graph

运行后查看：

```text
Scope XYZ
XY Graph
Display safeFlag
```

应该看到：

```text
x、y、z 随时间变化曲线
x-y 平面轨迹
safeFlag 正常情况下保持 1
```

为什么要看这些：

```text
Scope 用于证明动态过程是按时间变化的。
XY Graph 用于展示俯视轨迹。
safeFlag 用于证明模型具备安全监控逻辑。
```

### 步骤 7：保存 Simulink 模型

如果模型正常生成并打开，在 MATLAB 中运行：

```matlab
save_system('swing_language_control_sim')
```

为什么要做这一步：

```text
保存后项目目录中会保留 .slx 文件。
下次展示时可以直接打开模型，而不必重新构建。
```

## 五、推荐完整操作顺序

第一次完整验证建议按下面顺序做：

```text
1. 终端运行 make map-demo，生成动作 JSON
2. MATLAB 进入 matlab/ 目录
3. 运行 simulate_swing_actions('../data/processed/instructions/map_last_actions.json')
4. 确认弹出三维轨迹图
5. 确认 data/simulation/ 生成 CSV、JSON、PNG
6. MATLAB 进入 simulink/ 目录
7. 运行 build_swing_simulink_model
8. 运行 actionsToVelocityCmd('../data/processed/instructions/map_last_actions.json')
9. 运行 open_system('swing_language_control_sim')
10. 运行 sim('swing_language_control_sim')
11. 查看 Scope、XY Graph 和 safeFlag
12. 保存 .slx 模型
```

为什么这个顺序最稳：

```text
先用 MATLAB 脚本验证动作和地图数据没有问题。
再用 Simulink 做动态模型。
如果脚本仿真都不通过，Simulink 也没有必要继续跑。
```

## 六、验收标准

### MATLAB 脚本仿真验收

必须满足：

```text
能读取 map_last_actions.json
能读取 site_map.json
能输出 Action sequence
能弹出三维轨迹图
能输出 PASS 或 FAIL
能生成 data/simulation/latest_trajectory.csv
能生成 data/simulation/latest_result.json
能生成 data/simulation/latest_figure.png
```

### Simulink 动态仿真验收

必须满足：

```text
能生成 simulink/swing_language_control_sim.slx
能生成 MATLAB 工作区变量 velCmd
能打开 Simulink 模型
能运行 sim('swing_language_control_sim')
Scope 中有 x/y/z 曲线
XY Graph 中有平面轨迹
safeFlag 正常路线保持 1
```

### 展示验收

必须能讲清楚：

```text
中文指令如何变成动作 JSON
动作 JSON 如何变成 MATLAB 轨迹
地图中的目标区和禁飞区如何参与安全验证
Simulink 中速度如何通过积分器变成位置
为什么真机执行只是可选验证
```

## 七、常见问题与处理

### 1. MATLAB 提示找不到函数

可能原因：

```text
当前目录不在 matlab/ 或 simulink/。
```

处理：

```matlab
cd('/home/abc/桌面/SWING_CONTROL/matlab')
```

或：

```matlab
cd('/home/abc/桌面/SWING_CONTROL/simulink')
```

### 2. MATLAB 提示找不到动作 JSON

可能原因：

```text
还没有运行 Python 端 map_route --save-actions。
```

处理：

```bash
cd /home/abc/桌面/SWING_CONTROL
make map-demo
```

### 3. 仿真结果是 FAIL

可能原因：

```text
路线越界
进入禁飞区
最终没有降落
动作 JSON 不完整
地图坐标设置不合理
```

处理：

```text
先查看 MATLAB 命令行输出的 safetyErrors。
再检查 data/maps/site_map.json。
必要时换一条指令重新生成动作 JSON。
```

### 4. Simulink 提示找不到 velCmd

原因：

```text
还没有运行 actionsToVelocityCmd。
```

处理：

```matlab
actionsToVelocityCmd('../data/processed/instructions/map_last_actions.json')
```

### 5. 没有生成 .slx 文件

原因：

```text
build_swing_simulink_model 没有成功运行，或者当前目录不对。
```

处理：

```matlab
cd('/home/abc/桌面/SWING_CONTROL/simulink')
build_swing_simulink_model
```

### 6. 没有 data/simulation 输出

可能原因：

```text
simulate_swing_actions 没有正常运行到结束。
exportSimulationResult 出错。
```

处理：

```text
先确认 MATLAB 命令窗口是否报错。
再确认项目根目录是否可写。
最后检查 data/simulation/ 是否被自动创建。
```

## 八、答辩或展示讲解词

可以按下面逻辑讲：

```text
本项目不是直接把自然语言发送给无人机执行，而是先把自然语言转换为动作 JSON。
动作 JSON 是统一的中间表示，可以交给真机执行器，也可以交给 MATLAB/Simulink 仿真。

在 MATLAB 中，系统读取动作 JSON 和地图 JSON，把 takeoff、fly_forward、hover、land 等动作转换成三维轨迹。
同时，系统根据地图边界和禁飞区检查每个轨迹点是否安全。

在 Simulink 中，动作被进一步转换为速度命令 vx、vy、vz。
速度经过积分器后得到位置 x、y、z。
安全检查模块实时输出 safeFlag，用于判断仿真是否安全。

因此，本项目的重点不是冒险进行真机飞行，而是先通过 MATLAB/Simulink 建立可解释、可复现、可验证的无人机控制仿真平台。
```

## 九、最终需要提交或保留的成果

完成 MATLAB/Simulink 操作后，建议保留：

```text
data/processed/instructions/map_last_actions.json
data/simulation/latest_trajectory.csv
data/simulation/latest_result.json
data/simulation/latest_figure.png
simulink/swing_language_control_sim.slx
```

这些文件分别证明：

```text
map_last_actions.json：中文指令已经转换成动作序列。
latest_trajectory.csv：动作序列已经转换成可分析轨迹。
latest_result.json：安全验证有明确结论。
latest_figure.png：路径和禁飞区可视化。
swing_language_control_sim.slx：Simulink 动态模型已生成。
```
