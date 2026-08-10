# 自然语言无人机控制 — MATLAB/Simulink 仿真验证平台

本项目将自然语言/语音输入转换为结构化飞行指令，经地图路径规划和安全校验后，在 **MATLAB/Simulink** 中仿真验证飞行轨迹与安全性。Parrot Swing 真机执行仅作为可选验证。

## 主展示链路

```text
中文指令 / 语音输入
  → 动作 JSON
  → 地图路径规划（目标区域识别 + 禁飞区绕行）
  → 安全校验
  → MATLAB 仿真（轨迹图 + PASS/FAIL）
  → 真机执行（可选）
```

## 快速开始

### 1. 文本指令 → 动作 JSON（dry-run）

```bash
cd /home/abc/桌面/SWING_CONTROL
PYTHONPATH=src python -m swing_control.app.parse_instruction "起飞后悬停2秒再降落" --dry-run
```

### 2. 地图指令 → 动作 JSON + 保存

```bash
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到果园上方悬停两秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json
```

### 3. MATLAB 仿真

```matlab
cd('/home/abc/桌面/SWING_CONTROL/matlab')
simulate_swing_actions('../data/processed/instructions/map_last_actions.json')
```

详细说明见 [matlab/README.md](matlab/README.md)。

说明：MATLAB 脚本和导出逻辑已在项目中补齐，但当前命令行环境未检测到 `matlab`/`octave`，需要在 MATLAB GUI 中实际运行确认图形窗口和导出文件。

### 4. 语音控制

```bash
./model/run_swing_voice.sh --check-env
./model/run_swing_voice.sh --no-log
```

## 项目结构

```text
SWING_CONTROL/
├── README.md
├── Makefile
├── pyproject.toml
├── configs/
│   └── default.yaml
├── data/
│   ├── maps/
│   │   └── site_map.json          # 地图（目标区域、禁飞区）
│   ├── processed/
│   │   └── instructions/          # 生成的动作 JSON
│   ├── simulation/                # MATLAB 仿真导出（CSV/JSON/PNG）
│   └── logs/
├── matlab/
│   ├── README.md
│   ├── simulate_swing_actions.m   # 主仿真入口
│   ├── applySwingAction.m         # 动作模拟
│   ├── applyWindDisturbance.m     # 风扰动模拟
│   ├── checkMapSafety.m           # 地图安全检查
│   ├── plotSwingSimulation.m      # 三维轨迹绘图
│   ├── actionsToTimeline.m        # 动作 → 时间序列
│   └── exportSimulationResult.m   # 导出 CSV/JSON/PNG
├── simulink/
│   ├── README.md
│   ├── actionsToVelocityCmd.m      # 动作 → Simulink 速度命令
│   └── build_swing_simulink_model.m # 生成 .slx 的构建脚本
├── model/
│   ├── run_swing_voice.sh
│   ├── run_swing_instruction.sh
│   └── ...
├── src/
│   └── swing_control/
│       ├── app/                   # 系统入口
│       ├── asr/                   # 语音识别
│       ├── flight/                # 飞控执行（pyparrot）
│       ├── mapping/               # 地图与语义区域
│       ├── nlp/                   # 指令解析（Ollama + 规则）
│       ├── planning/              # 路径规划（A*/平滑/风扰动）
│       └── safety/                # 安全校验（action_validator）
└── tests/
    ├── test_action_validator.py
    ├── test_instruction_parser.py
    ├── test_path_planner.py
    └── test_route_planner.py
```

## 已实现能力

| 模块 | 状态 |
|------|------|
| 中文指令 → 动作 JSON（Ollama + 规则兜底） | 已实现 |
| 地图目标识别 + 路径规划 + 禁飞区绕行 | 已实现 |
| 动作安全校验（白名单/参数范围/序列规则） | 已实现 |
| 语音输入（麦克风 → Whisper → 控制链路） | 已实现 |
| MATLAB 脚本仿真（轨迹绘图 + 安全结论） | 代码已具备，待 MATLAB GUI 实测 |
| MATLAB 结果导出（CSV/JSON/PNG） | 代码已具备，待 MATLAB GUI 实测 |
| Simulink 动态模型 | 构建脚本已具备，待生成 `.slx` 并实测 |
| 真机执行（pyparrot + 蓝牙） | 已实现，可选验证 |

## 文档入口

- [MATLAB 仿真指南](matlab/README.md)
- [技术文档](TECHNICAL_DOCUMENTATION.md)
- [项目状态与后续计划](OPENCODE_PROJECT_STATUS_GUIDE.md)
- [运行环境说明](docs/ENVIRONMENT.md)
- [Ollama 安装说明](docs/LLM_INSTALL.md)
- [地图控制使用](docs/MAP_CONTROL_USAGE.md)
- [语音控制使用](docs/VOICE_CONTROL_USAGE.md)

## 运行测试

```bash
python -m pip install pytest PyYAML pandas scipy
PYTHONPATH=src pytest
```

或使用 Makefile：

```bash
make test
make map-demo
make text-demo
```
