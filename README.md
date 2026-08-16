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

### 0. 环境安装

推荐使用 Python 3.11。项目已提供 `.python-version` 和 `environment-delivery.yml`。

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
conda env create -f environment-delivery.yml
conda activate llm-control-lowair
./scripts/install_ubuntu_deps.sh
```

安装后的最终验收命令：

```bash
make check-env
make delivery-check
```

详细说明见 [Ubuntu 交付安装与最终验收](docs/DELIVERY_INSTALL_ACCEPTANCE.md)。

### 0. Ubuntu 交付检查

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
make check-env
make delivery-check
```

`make delivery-check` 会串联环境检查、自动化测试、文本 dry-run、地图规划和交付报告生成。生成报告位于：

```text
data/reports/latest_report.md
```

### 1. 文本指令 → 动作 JSON（dry-run）

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
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
cd('/home/abc/桌面/LLM-CONTROL_LOWAIR/matlab')
simulate_swing_actions('../data/processed/instructions/map_last_actions.json')
```

详细说明见 [matlab/README.md](matlab/README.md)。

说明：MATLAB 脚本和导出逻辑已在项目中补齐，但当前命令行环境未检测到 `matlab`/`octave`，需要在 MATLAB GUI 中实际运行确认图形窗口和导出文件。

### 4. 语音控制

```bash
./model/run_swing_voice.sh --check-env
./model/run_swing_voice.sh --no-log
```

### 5. 一键演示和发布包

```bash
./run_demo.sh
./run_demo.sh --full
./run_demo.sh --menu
./run_demo.sh --streamlit
./run_demo_menu.sh
./scripts/package_release.sh
```

发布包输出到 `dist/`。

Streamlit 功能展示面板：

```bash
make streamlit
```

打开浏览器访问 `http://127.0.0.1:8501`。

## 项目结构

```text
LLM-CONTROL_LOWAIR/
├── README.md
├── SAFETY.md
├── Makefile
├── pyproject.toml
├── .python-version
├── environment-delivery.yml        # Ubuntu 交付环境（Python 3.11）
├── run_demo.sh                     # 快速演示入口
├── run_demo_menu.sh                # 交互式 Shell 演示菜单
├── demo_streamlit.py               # Streamlit 功能展示面板
├── examples/                      # Ubuntu 演示命令和样例口令
├── scripts/                       # 环境检查、依赖安装、交付验证脚本
├── configs/
│   └── default.yaml
├── data/
│   ├── maps/
│   │   └── site_map.json          # 地图（目标区域、禁飞区）
│   ├── processed/
│   │   └── instructions/          # 生成的动作 JSON
│   ├── simulation/                # MATLAB 仿真导出（CSV/JSON/PNG）
│   ├── reports/                   # Ubuntu 交付报告（运行生成）
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
│   ├── actionsToVelocityCmd.m       # 动作 → Simulink 速度命令
│   ├── build_swing_simulink_model.m # 生成 .slx 的构建脚本
│   └── swing_language_control_sim.slx # 已生成的 Simulink 模型
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
| Simulink 动态模型 | `.slx` 已生成，待 Windows MATLAB/Simulink 实测运行 |
| 真机执行（pyparrot + 蓝牙） | 已实现，可选验证 |
| Ubuntu 交付检查和报告生成 | 已实现 |

## 文档入口

- [MATLAB 仿真指南](matlab/README.md)
- [Windows MATLAB/Simulink 操作手册](MATLAB_SIMULINK_OPERATION_MANUAL.md)
- [技术文档](TECHNICAL_DOCUMENTATION.md)
- [安全交付说明](SAFETY.md)
- [Ubuntu 交付安装与最终验收](docs/DELIVERY_INSTALL_ACCEPTANCE.md)
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

当前验证状态：

```text
PYTHONPATH=src python -m pytest -q
72 passed
```

或使用 Makefile：

```bash
make test
make map-demo
make text-demo
make check-env
make report
make delivery-check
make demo
make menu
make streamlit
make package
```
