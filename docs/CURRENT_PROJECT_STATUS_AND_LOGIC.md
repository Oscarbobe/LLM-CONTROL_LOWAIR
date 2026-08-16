# 当前项目状态与完整运行逻辑

本文档记录 `LLM-CONTROL_LOWAIR` 当前真实状态。旧版“语音未实现、测试未实现、依赖缺失”等描述已经不再适用。

## 1. 当前定位

```text
自然语言/语音输入
→ 动作 JSON
→ 地图路径规划
→ 安全校验
→ MATLAB 脚本仿真
→ Simulink 动态仿真
→ 真机执行作为可选验证
```

项目当前重点不是直接依赖真机飞行，而是构建自然语言无人机控制的可验证仿真平台。

## 2. 已实现模块

### 2.1 中文与语音输入

```text
src/swing_control/nlp/instruction_parser.py
src/swing_control/app/parse_instruction.py
src/swing_control/app/interactive_control.py
src/swing_control/app/voice_control.py
src/swing_control/asr/microphone.py
src/swing_control/asr/transcriber.py
```

能力：

```text
中文指令解析
Ollama/qwen3.5:4b 调用
规则兜底解析
麦克风录音
Whisper 语音识别
语音识别文本归一化
```

### 2.2 地图与路径规划

```text
data/maps/site_map.json
src/swing_control/mapping/site_map.py
src/swing_control/planning/route_planner.py
src/swing_control/planning/path_planner.py
src/swing_control/planning/trajectory_smoother.py
src/swing_control/planning/wind_model.py
src/swing_control/app/map_route.py
```

能力：

```text
目标区域识别
禁飞区识别
A*/网格路径规划
路径平滑
风扰动模型
动作 JSON 保存
```

### 2.3 安全校验

```text
src/swing_control/safety/action_validator.py
src/swing_control/safety/manual_confirmation.py
```

能力：

```text
动作白名单
参数范围检查
起飞/降落顺序检查
运动动作时间上限
真机执行前人工确认
```

### 2.4 MATLAB/Simulink 仿真

```text
matlab/
simulink/
MATLAB_SIMULINK_OPERATION_MANUAL.md
```

当前文件：

```text
matlab/simulate_swing_actions.m
matlab/actionsToTimeline.m
matlab/exportSimulationResult.m
simulink/actionsToVelocityCmd.m
simulink/build_swing_simulink_model.m
simulink/swing_language_control_sim.slx
```

状态：

```text
MATLAB 脚本仿真代码已具备
MATLAB 结果导出代码已具备
Simulink .slx 模型已存在
仍需在 Windows MATLAB/Simulink GUI 中实测
```

### 2.5 真机执行

```text
model/
src/swing_control/flight/swing_action_executor.py
```

能力：

```text
蓝牙恢复
Swing 扫描
pyparrot 连接与执行
异常时尝试 safe_land
```

真机执行是可选验证，不是主展示依赖。

## 3. 当前验证结果

已通过：

```bash
PYTHONPATH=src python -m pytest -q
```

结果：

```text
72 passed

Ubuntu 侧已新增交付验证链路：

```bash
make check-env
make delivery-check
make report
```
```

地图规划验证：

```bash
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到果园上方悬停两秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json
```

语音环境验证：

```bash
./model/run_swing_voice.sh --check-env
```

## 4. 当前仍需完成

### 4.1 Windows MATLAB 实测

需要在 Windows MATLAB 中运行：

```matlab
projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR';
cd(projectRoot);
addpath(fullfile(projectRoot, 'matlab'));
result = simulate_swing_actions(fullfile('data', 'processed', 'instructions', 'map_last_actions.json'));
```

预期生成：

```text
data/simulation/latest_trajectory.csv
data/simulation/latest_result.json
data/simulation/latest_figure.png
```

### 4.2 Windows Simulink 实测

需要在 Windows MATLAB/Simulink 中运行：

```matlab
projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR';
cd(projectRoot);
addpath(fullfile(projectRoot, 'simulink'));
actionsToVelocityCmd(fullfile('data', 'processed', 'instructions', 'map_last_actions.json'));
open_system(fullfile(projectRoot, 'simulink', 'swing_language_control_sim.slx'));
sim('swing_language_control_sim');
```

### 4.3 可选增强

```text
真实 GIS/GeoJSON/DEM 地图
定位闭环与真实避障
返航路径
SwingActionExecutor fake/mock 测试
qwen3.5:4b prompt 优化
qwen2.5:3b 模型对比
```

## 5. 推荐展示流程

```text
1. 中文指令生成动作 JSON
2. 展示地图目标区和禁飞区
3. 展示动作安全校验
4. MATLAB 脚本仿真轨迹图
5. Simulink 打开动态模型
6. 真机执行作为可选验证
```

## 6. 一句话结论

```text
当前 Python 控制链路、测试链路和 Simulink 文件已基本完整；剩余核心工作是 Windows MATLAB/Simulink 实测和真实地图/定位闭环增强。
```
