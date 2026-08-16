# OpenCode 项目现状与后续实践指导

本文档用于让 OpenCode 快速了解当前 `LLM-CONTROL_LOWAIR` 项目的真实状态，并指导后续继续开发。

当前项目定位：

```text
自然语言 / 语音输入
→ 动作 JSON
→ 地图路径规划
→ 安全校验
→ MATLAB 脚本仿真
→ Simulink 动态仿真
→ 真机执行作为可选验证
```

项目主线应继续保持“仿真优先、真机可选”。真机蓝牙和飞行环境不稳定时，不影响主展示链路。

## 当前状态

### 已实现

```text
中文指令 dry-run
语音录音与 Whisper 转文字
Ollama/qwen3.5:4b 调用
规则兜底解析
地图目标识别
A*/网格路径规划
轨迹平滑
风扰动模型
动作 JSON 保存
动作安全校验
人工确认
pyparrot 真机执行接口
MATLAB 脚本仿真代码
MATLAB 结果导出代码
Simulink 构建脚本
Simulink .slx 模型文件
pytest 自动化测试
```

### 当前验证结果

```text
PYTHONPATH=src python -m pytest -q
72 passed

Ubuntu 侧交付入口已补齐：

```bash
make check-env
make delivery-check
make report
./run_demo.sh
./run_demo_menu.sh
make streamlit
./scripts/package_release.sh
```

其中 `make delivery-check` 会串联环境检查、测试、文本 dry-run、地图规划和 `data/reports/latest_report.md` 生成。交付环境建议使用 `.python-version` / `environment-delivery.yml` 中的 Python 3.11。
```

已验证命令：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到果园上方悬停两秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json
```

语音环境检查已通过：

```bash
./model/run_swing_voice.sh --check-env
```

### 当前关键文件

```text
README.md
TECHNICAL_DOCUMENTATION.md
MATLAB_SIMULINK_OPERATION_MANUAL.md
Makefile
pyproject.toml
data/maps/site_map.json
data/processed/instructions/map_last_actions.json
matlab/simulate_swing_actions.m
matlab/exportSimulationResult.m
simulink/swing_language_control_sim.slx
src/swing_control/planning/path_planner.py
src/swing_control/planning/route_planner.py
src/swing_control/planning/trajectory_smoother.py
src/swing_control/planning/wind_model.py
tests/test_action_validator.py
tests/test_instruction_parser.py
tests/test_path_planner.py
tests/test_route_planner.py
```

## 仍需完成

### 1. Windows MATLAB 实测

代码已具备，但仍需在 Windows MATLAB GUI 中实际运行：

```matlab
projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR';
cd(projectRoot);
addpath(fullfile(projectRoot, 'matlab'));
result = simulate_swing_actions(fullfile('data', 'processed', 'instructions', 'map_last_actions.json'));
```

验收目标：

```text
弹出三维轨迹图
data/simulation/latest_trajectory.csv
data/simulation/latest_result.json
data/simulation/latest_figure.png
```

### 2. Windows Simulink 实测

`.slx` 文件已存在：

```text
simulink/swing_language_control_sim.slx
```

仍需在 Windows MATLAB/Simulink 中打开并运行：

```matlab
projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR';
cd(projectRoot);
addpath(fullfile(projectRoot, 'simulink'));
actionsToVelocityCmd(fullfile('data', 'processed', 'instructions', 'map_last_actions.json'));
open_system(fullfile(projectRoot, 'simulink', 'swing_language_control_sim.slx'));
sim('swing_language_control_sim');
```

验收目标：

```text
Scope 中有 x/y/z 曲线
XY Graph 中有平面轨迹
safeFlag 正常路线保持 1
```

### 3. 文档维护

根目录 Windows 手册是 MATLAB/Simulink 操作的主入口：

```text
MATLAB_SIMULINK_OPERATION_MANUAL.md
```

后续如果修改 MATLAB 或 Simulink 文件，应同步更新：

```text
README.md
TECHNICAL_DOCUMENTATION.md
matlab/README.md
simulink/README.md
```

### 4. 模型解析稳定性

当前默认模型：

```text
qwen3.5:4b
```

它可以调用，但对短中文飞行指令仍可能输出：

```json
{"error":"无法理解"}
```

项目通过规则兜底保证可运行。后续可以继续优化：

```text
instruction_parser.py 的 SYSTEM_PROMPT
地图指令规则优先级
qwen2.5:3b / 其他中文模型对比
```

### 5. 工程测试扩展

当前测试已覆盖核心规划与解析。后续可选增加：

```text
tests/test_swing_action_executor_fake.py
tests/test_voice_control_normalization.py
tests/test_map_route_cli.py
```

其中真机执行器测试应使用 fake/mock，不应依赖真实蓝牙无人机。

## 推荐展示流程

```text
1. Python 生成动作 JSON
2. 展示 data/maps/site_map.json 中的目标区和禁飞区
3. 展示 map_route 输出的动作 JSON 和安全校验
4. 在 MATLAB 中运行 simulate_swing_actions
5. 展示轨迹图和 data/simulation 导出文件
6. 打开 Simulink .slx 展示动态模型
7. 真机连接作为可选补充
```

## OpenCode 后续任务建议

优先级从高到低：

```text
1. 根据 Windows MATLAB 实测结果修复 MATLAB 路径/导出兼容问题。
2. 根据 Windows Simulink 实测结果修复 .slx 模型输入、Scope 或 safeFlag 问题。
3. 同步 README、TECHNICAL_DOCUMENTATION.md 和 MATLAB_SIMULINK_OPERATION_MANUAL.md。
4. 增加 SwingActionExecutor fake 测试。
5. 优化 qwen3.5:4b prompt 或加入更稳定中文模型配置。
6. 加入真实 GIS/GeoJSON/DEM 地图数据支持。
```

## 提交前检查

提交前建议运行：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到果园上方悬停两秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json
git status --short
```

不要提交：

```text
__pycache__/
.pytest_cache/
data/logs/*.jsonl
data/raw/audio/*.wav
data/raw/audio/*.txt
data/simulation/
```

一句话总结：

```text
当前项目已具备 Python 解析/规划/测试链路和 MATLAB/Simulink 仿真文件；下一步重点是 Windows MATLAB/Simulink 实测与文档同步。
```
