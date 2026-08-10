# SWING_CONTROL 技术文档

本文档汇总本项目在多轮交互后形成的完整技术逻辑，覆盖项目目的、运行链路、目录结构、代码文件职责、核心函数、MATLAB/Simulink 仿真、真机蓝牙恢复、Ollama 接入、动作校验、dry-run、人工确认、pyparrot 执行和日志保存方式。

## 1. 项目目的

本项目目标是构建一个“自然语言/语音 -> 动作解析 -> 安全校验 -> MATLAB/Simulink 仿真验证”的山区无人机智能控制原型。

当前项目聚焦 Parrot Swing 小型无人机，先实现室内/近距离 BLE 控制的可演示闭环。更完整的山区农业应用目标包括：农户用中文口语下达巡田、悬停、移动、转向、起降等指令，系统将自然语言转成结构化动作，再经过安全规则限制和人工确认，最终在 MATLAB/Simulink 中仿真验证飞行轨迹和安全性，真机执行仅作为可选环节。

当前已实现的核心能力：

- 中文文本指令解析为 Swing 动作 JSON。
- 连续中文交互 CLI，支持多轮输入、预览、确认和执行。
- 麦克风说话控制 CLI，支持录音、Whisper 转文字、预览、确认和执行。
- Ollama 本地模型调用，默认模型为 `qwen3.5:4b`。
- 当模型输出不稳定时，使用规则兜底解析常见中文飞行动作。
- 地图目标区域识别与路径规划，支持禁飞区绕行。
- 动作 JSON 安全校验。
- dry-run 输出动作序列和对应 pyparrot 调用预览。
- 真机执行前强制人工输入 `确认执行`。
- pyparrot 真机执行器，支持起飞、降落、悬停、移动、转向、模式切换。
- 异常时尝试安全降落。
- `data/logs` 保存 JSONL 运行日志。
- 参照 `/home/abc/桌面/LowAir-GS/pyparrot` 的 MT7925 蓝牙恢复逻辑，加入本项目自动化脚本。
- **MATLAB 脚本仿真代码**：三维轨迹绘制、地图安全检查、PASS/FAIL 结论。
- **MATLAB 结果导出代码**：轨迹 CSV、结果 JSON、仿真 PNG 自动导出到 `data/simulation/`。
- **Simulink 构建脚本**：提供动作速度命令转换和 `.slx` 模型构建脚本，用于后续动态仿真展示。
- A*/网格路径规划、轨迹平滑与风扰动模型的初步代码结构。

当前未完整实现但保留结构的能力：

- 真实 GPS/GIS 地图。
- 定位闭环下的真实避障、返航路径和实际飞行误差校正。
- 多无人机调度或高级任务规划。
- Simulink 动态仿真模型的实际 `.slx` 文件生成与 GUI 实测。
- MATLAB 仿真在 MATLAB GUI 中的实际运行验证（当前 shell 未检测到 `matlab`/`octave` 命令）。
- 自动化测试运行环境仍缺少 `pytest`、`PyYAML`、`pandas`、`scipy` 等依赖。

## 2. 项目运行总逻辑

### 2.1 dry-run 演示链路

dry-run 不连接无人机，适合验证指令解析和动作安全性。

```text
中文指令
  -> run_swing_instruction.sh
  -> swing_control.app.run_instruction
  -> instruction_parser 调用 Ollama
  -> 解析为动作 JSON
  -> 保存 data/processed/instructions/last_actions.json
  -> action_validator 安全校验
  -> action_planner 生成动作预览
  -> 输出 pyparrot 调用预览
  -> 写入 data/logs/*.jsonl
```

运行：

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_instruction.sh "起飞后悬停2秒再降落"
```

关闭日志：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --no-log
```

### 2.2 中文指令真机执行链路

真机执行会连接蓝牙和无人机，必须保证 Swing 在空旷安全区域。

```text
run_swing_instruction.sh --execute
  -> 检查 Python / Ollama / pyparrot
  -> 调用 model/fix_mt7925_bluetooth.sh 恢复蓝牙
  -> 如未传 --addr，自动扫描 Swing 地址
  -> 扫描失败时再执行一次蓝牙恢复并重扫
  -> demoSwingDirectFlight.py --connect-only 连接测试
  -> run_instruction.py 解析中文指令
  -> 保存动作 JSON
  -> action_validator 校验
  -> action_planner 输出 dry-run 预览
  -> manual_confirmation 要求输入“确认执行”
  -> SwingActionExecutor 调用 pyparrot 真机执行
  -> 异常自动尝试 safe_land(5)
  -> disconnect
  -> 写入 data/logs/*.jsonl
```

运行：

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute
```

已知 Swing 地址时跳过扫描：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute --addr E0:14:89:09:3D:CB
```

### 2.3 连续中文交互链路

连续交互入口用于产品演示中的“输入语言 -> 预览 -> 确认 -> 执行 -> 继续输入”。

```text
run_swing_interactive.sh
  -> 启动 interactive_control.py
  -> 用户反复输入中文指令
  -> 每条指令调用 Ollama/规则兜底解析
  -> 交互短指令补全起飞/降落保护动作
  -> action_validator 校验
  -> action_planner 输出动作预览
  -> dry-run 模式只展示
  -> --execute 模式要求输入“确认执行”
  -> SwingActionExecutor 真机执行
  -> 回到下一条指令输入
```

dry-run 交互：

```bash
./model/run_swing_interactive.sh
```

真机交互：

```bash
./model/run_swing_interactive.sh --execute
```

### 2.4 麦克风语音控制链路

语音入口用于“按 Enter -> 说话 -> 自动转文字 -> 复用中文控制链路”。

```text
run_swing_voice.sh
  -> 启动 voice_control.py
  -> 按 Enter 开始录音
  -> microphone.py 调用 arecord 或 ffmpeg 保存 wav
  -> transcriber.py 调用 openai-whisper 或 whisper 命令转文字
  -> 将识别文本交给 interactive_control.handle_instruction
  -> Ollama/规则兜底解析
  -> 动作校验和 dry-run 预览
  -> --execute 模式要求输入“确认执行”
  -> SwingActionExecutor 真机执行
  -> 回到下一轮录音
```

运行：

```bash
./model/run_swing_voice.sh
```

真机语音执行：

```bash
./model/run_swing_voice.sh --execute
```

### 2.5 动作 JSON 真机执行链路

如果已经有动作 JSON 文件，可以跳过中文解析，直接进入校验、预览、确认、执行。

```bash
./model/run_swing_actions.sh --addr E0:14:89:09:3D:CB
```

默认读取：

```text
data/processed/instructions/demo_actions.json
```

指定文件：

```bash
./model/run_swing_actions.sh --addr E0:14:89:09:3D:CB --file data/processed/instructions/last_actions.json
```

### 2.6 直接飞行 demo 链路

该链路借鉴 LowAir-GS 的 pyparrot 模式，主要用于验证 Swing 基础连接和动作接口。

```text
run_swing_direct_flight.sh
  -> 蓝牙恢复
  -> 扫描 Swing
  -> 写入地址到 demoSwingDirectFlight.py
  -> 连接测试
  -> 用户按 Enter 确认
  -> demoSwingDirectFlight.py 执行基础动作
```

运行：

```bash
./model/run_swing_direct_flight.sh
```

## 3. 项目目录结构及大类作用

```text
SWING_CONTROL/
├── README.md
├── TECHNICAL_DOCUMENTATION.md
├── OPENCODE_PROJECT_STATUS_GUIDE.md
├── Makefile
├── pyproject.toml
├── requirements.txt
├── environment.yml
├── environment-llm.yml
├── configs/
├── data/
├── docs/
├── matlab/
├── simulink/
├── model/
├── src/
├── tests/
├── assets/
└── 三下乡项目申请.docx
```

### 3.1 根目录文件

- `README.md`：项目入口说明，包含快速运行、目录结构和文档索引。
- `TECHNICAL_DOCUMENTATION.md`：本文档，作为完整技术说明。
- `OPENCODE_PROJECT_STATUS_GUIDE.md`：面向 OpenCode 的项目现状、缺口和后续实践指导。
- `Makefile`：常用命令入口，如 `make map-demo`、`make text-demo`、`make voice-check`、`make test`。
- `pyproject.toml`：基础 Python 项目元信息和 pytest 配置。
- `requirements.txt`：当前项目 Python 依赖列表，包含 pyparrot 相关依赖和后续自然语言/数据处理依赖。
- `environment.yml`：通用 conda 环境配置。
- `environment-llm.yml`：大模型/语音识别扩展环境配置，包含 PyTorch、transformers、openai-whisper、ollama 等。
- `三下乡项目申请.docx`：项目申请文档，用于提炼产品制作流程和项目背景。

### 3.2 `configs/`

配置目录。

- `configs/default.yaml`：项目默认配置。包含项目名称、默认 Python、无人机类型和地址、Ollama 模型、飞行限制、安全策略、数据路径等。

### 3.3 `data/`

数据与运行产物目录。

- `data/processed/instructions/`：保存解析后的动作 JSON。
- `data/processed/instructions/demo_actions.json`：动作 JSON 示例。
- `data/processed/instructions/last_actions.json`：最近一次中文指令解析结果。
- `data/processed/instructions/map_last_actions.json`：地图规划命令保存的最近一次动作序列。
- `data/logs/`：保存 JSONL 运行日志。
- `data/maps/`：地图数据目录，当前包含 `site_map.json` 本地演示地图。
- `data/simulation/`：MATLAB 仿真运行后生成的轨迹 CSV、结果 JSON 和图片 PNG。该目录为生成产物，默认不入库。

### 3.4 `matlab/`

MATLAB 脚本仿真目录。

- `matlab/README.md`：MATLAB 仿真运行说明。
- `matlab/simulate_swing_actions.m`：主仿真入口，读取动作 JSON 和地图 JSON。
- `matlab/applySwingAction.m`：将动作序列转换为仿真位姿变化。
- `matlab/applyWindDisturbance.m`：风扰动模型。
- `matlab/checkMapSafety.m`：检查边界、禁飞区和安全状态。
- `matlab/plotSwingSimulation.m`：绘制三维轨迹、目标区域和禁飞区。
- `matlab/actionsToTimeline.m`：动作序列转时间序列。
- `matlab/exportSimulationResult.m`：导出 CSV、JSON、PNG 结果。

### 3.5 `simulink/`

Simulink 动态仿真目录。

- `simulink/README.md`：Simulink 模型搭建和运行说明。
- `simulink/actionsToVelocityCmd.m`：动作 JSON 转 Simulink 速度命令。
- `simulink/build_swing_simulink_model.m`：生成 `swing_language_control_sim.slx` 的构建脚本。

当前状态：构建脚本已存在，仍需在 MATLAB/Simulink GUI 中运行并生成 `.slx` 文件。

### 3.6 `docs/`

项目专题文档目录。用于解释不同功能模块的设计和实现流程。

主要文档：

- `ACTION_VALIDATOR_FLOW.md`：动作校验逻辑。
- `DRY_RUN_FLOW.md`：dry-run 动作序列逻辑。
- `MANUAL_CONFIRMATION_FLOW.md`：人工确认逻辑。
- `SWING_ACTION_EXECUTOR_FLOW.md`：pyparrot 真机执行逻辑。
- `LOGGING_FLOW.md`：日志保存逻辑。
- `OLLAMA_USAGE.md`：Ollama 使用说明。
- `ADD_LLAMA_MODEL.md`：如何加入 Llama 模型。
- `BLUETOOTH_RECOVERY_FLOW.md`：蓝牙恢复逻辑。
- `REAL_DRONE_OPERATION_FLOW.md`：无人机实际操作链路。
- `CURRENT_PROJECT_STATUS_AND_LOGIC.md`：当前项目状态和缺口。
- `FULL_LOCAL_PIPELINE.md`：基于本机配置的完整运行流程。
- `REFERENCE_ADAPTATION_PLAN.md`：借鉴姜星海毕业论文/相似项目结构后的方案。
- `PRODUCT_BUILD_FLOW.md`：产品制作流程逻辑。
- `PROJECT_STRUCTURE.md`：项目结构说明。
- `ENVIRONMENT.md`、`ENV_CHECK_RESULT.md`、`LLM_INSTALL.md`：环境安装与检查说明。

### 3.7 `model/`

真机脚本和 pyparrot demo 目录。这里是本项目直接控制 Swing 的主要 shell 入口。

### 3.8 `src/swing_control/`

Python 源码目录，按功能拆分为 app、nlp、safety、planning、flight 等模块。

其中 `src/swing_control/planning/` 当前包含动作预览、地图路线规划、A*/网格路径规划、轨迹平滑和风扰动模型。

### 3.9 `tests/`

测试目录，已包含核心单元测试：

- `tests/test_action_validator.py`
- `tests/test_instruction_parser.py`
- `tests/test_path_planner.py`
- `tests/test_route_planner.py`

当前 shell 环境缺少 `pytest`，需要安装依赖后运行：

```bash
python -m pip install pytest PyYAML pandas scipy
PYTHONPATH=src python -m pytest -q
```

### 3.10 `assets/`

资源目录，目前只有 README，占位用于后续演示图片、界面资源、模型资源等。

## 4. 每个代码文件作用详解

### 4.1 Shell 脚本

#### `model/run_swing_instruction.sh`

中文指令完整入口。

作用：

- 自动定位项目根目录。
- 选择 Python 解释器，优先 `/home/abc/miniconda3/bin/python`。
- dry-run 模式下直接调用 `swing_control.app.run_instruction`。
- `--execute` 模式下先准备蓝牙，再扫描 Swing 地址，再连接测试，最后进入 Python 真机执行链路。
- 支持 `--addr`、`--model`、`--no-sudo`、`--skip-bluetooth-fix`、`--bluetooth-device`、`--update-bluetooth-firmware`、`--install-bluetooth-fix`、`--no-bluetooth-retry` 等参数。

关键函数：

- `log()`：统一时间戳日志输出。
- `die()`：输出错误并退出。
- `run_privileged()`：根据 `RUN_WITH_SUDO` 判断是否使用 `sudo`。
- `run_connection_test(addr)`：调用 `demoSwingDirectFlight.py --connect-only` 做只连接测试。
- `main()`：参数解析和主流程。

#### `model/run_swing_interactive.sh`

连续中文交互控制入口。

作用：

- dry-run 模式下直接启动 `swing_control.app.interactive_control`。
- `--execute` 模式下先恢复蓝牙、扫描 Swing、连接测试，再启动交互控制。
- 支持反复输入中文指令，每条指令独立预览、确认、执行。
- 支持 `--addr`、`--model`、`--no-log`、`--retries`、蓝牙恢复参数等。

关键函数：

- `run_connection_test(addr)`：交互真机执行前的只连接测试。
- `run_privileged()`：sudo 管理。
- `main()`：参数解析、蓝牙准备、启动 Python 交互入口。

#### `model/run_swing_voice.sh`

麦克风说话控制入口。

作用：

- dry-run 模式下启动 `swing_control.app.voice_control`。
- `--execute` 模式下先恢复蓝牙、扫描 Swing、连接测试，再启动语音控制。
- 支持录音时长、麦克风设备、ASR 后端、Whisper 模型等参数。

关键函数：

- `run_connection_test(addr)`：语音真机执行前的只连接测试。
- `run_privileged()`：sudo 管理。
- `main()`：参数解析、蓝牙准备、启动 Python 语音入口。

#### `model/run_swing_actions.sh`

动作 JSON 真机执行入口。

作用：

- 接收 `--addr` 指定 Swing 地址。
- 从 `--file` 或 `--json` 读取动作序列。
- 默认读取 `data/processed/instructions/demo_actions.json`。
- 执行蓝牙恢复。
- 调用 `swing_control.app.execute_actions` 进入校验、预览、确认、真机执行链路。

关键函数：

- `log()`、`die()`、`run_privileged()`。
- `main()`：解析参数、准备蓝牙、启动 Python 执行入口。

#### `model/run_swing_direct_flight.sh`

直接飞行 demo 自动化入口。

作用：

- 参照 LowAir-GS 的 pyparrot 自动连接模式。
- 恢复蓝牙。
- 扫描 Swing 地址。
- 将扫描到的地址写入 `demoSwingDirectFlight.py`。
- 先跑连接测试。
- 用户按 Enter 后执行基础飞行动作 demo。

关键函数：

- `write_swing_addr(addr)`：用 Python 正则替换 `demoSwingDirectFlight.py` 中的默认地址。
- `run_connection_test(addr)`：只连接测试。
- `run_privileged()`：sudo 管理。
- `main()`：五步流程控制。

#### `model/swing_bluetooth_common.sh`

蓝牙恢复和 Swing 扫描公共函数库。

作用：

- 抽取三个入口脚本共用的蓝牙恢复和扫描逻辑。
- 参照 LowAir-GS 中 `fix_mt7925_bluetooth.sh` 的 MT7925 恢复方式。

关键变量：

- `BLUETOOTH_DEVICE`：默认 `0489:e111`。
- `UPDATE_BLUETOOTH_FIRMWARE`：是否更新固件。
- `INSTALL_BLUETOOTH_FIX`：是否安装开机自动恢复服务。
- `RETRY_BLUETOOTH_RECOVERY`：扫描失败后是否再次恢复蓝牙并重扫。

关键函数：

- `bluetooth_fix_args()`：根据环境变量生成 `fix_mt7925_bluetooth.sh` 参数。
- `bluetooth_controller_usable()`：检查 `/sys/class/bluetooth/hci*`、零地址和 `bluetoothctl show`。
- `prepare_bluetooth_controller()`：执行蓝牙恢复，并验证控制器是否可用。
- `strip_ansi()`：清除扫描输出中的 ANSI 控制字符。
- `scan_with_pyparrot()`：调用 `python -m pyparrot.scripts.findMinidrone` 扫描 Swing。
- `scan_with_bluetoothctl()`：用 `bluetoothctl scan on` 扫描 20 秒。
- `extract_swing_addr()`：从扫描输出中提取 Swing MAC 地址。
- `find_swing_addr()`：合并 pyparrot 和 bluetoothctl 扫描结果。
- `find_swing_addr_with_recovery()`：扫描失败后自动恢复蓝牙并重扫一次。

#### `model/fix_mt7925_bluetooth.sh`

MT7925 蓝牙恢复脚本，来自 LowAir-GS 的 pyparrot 项目并调整了本项目提示路径。

作用：

- 针对 USB 设备 `0489:e111`。
- 向 `btusb` 写入 `new_id`。
- 禁用 USB autosuspend。
- 重载 `btusb` / `btmtk`。
- `rfkill unblock bluetooth`。
- 启动 `bluetooth.service`。
- 尝试拉起 HCI 控制器。
- 检查 `bluetoothctl show` 是否仍为 `No default controller available`。
- 支持 `--update-firmware` 下载固件。
- 支持 `--install-persistent` 安装 systemd 开机恢复服务。

关键函数：

- `find_usb_devices()`：扫描 `/sys/bus/usb/devices` 中匹配 VID/PID 的设备。
- `show_status()`：输出 USB、HCI、BlueZ 状态。
- `install_firmware()`：下载并安装 MT7925 蓝牙固件。
- `bind_btusb()`：绑定目标接口到 `btusb`。
- `reset_stack()`：停止服务、重载模块、解除 rfkill、启动服务。
- `power_on_hci()`：拉起 hci 控制器。
- `detect_success()`：判断恢复是否成功。
- `install_persistent_service()`：安装 systemd 持久化服务。
- `main()`：完整恢复流程。

#### `model/demoSwingDirectFlight.py`

pyparrot 直接飞行 demo。

作用：

- 创建 `Swing(addr)`。
- `connect(num_retries)` 连接无人机。
- 支持 `--connect-only` 只测试连接，不起飞。
- 完整模式下执行：状态更新、起飞、左右移动、左右转向、固定翼模式切换、四旋翼模式切换、降落、断开连接。

关键函数：

- `parse_args()`：解析 `--addr`、`--connect-only`、`--retries`。
- `main()`：执行连接和基础飞行动作。

### 4.2 Python 应用入口

#### `src/swing_control/app/run_instruction.py`

完整中文指令流水线入口。

作用：

- 接收中文指令。
- 调用 `parse_instruction()`。
- 保存动作 JSON 到 `data/processed/instructions/last_actions.json`。
- 调用 `validate_action_sequence()` 校验。
- 调用 `plan_actions()` 输出 dry-run 预览。
- 非 `--execute` 时结束。
- `--execute` 时进行人工确认，然后调用 `SwingActionExecutor`。
- 将每一步写入 JSONL 日志。

关键常量：

- `DEFAULT_ADDR`：默认从 `SWING_ADDR` 获取，否则用 `E0:14:89:09:3D:CB`。
- `DEFAULT_ACTION_OUTPUT`：默认保存到 `data/processed/instructions/last_actions.json`。

关键函数：

- `main()`：完整 CLI 流程。

退出码逻辑：

- `0`：成功或 dry-run 完成。
- `1`：解析失败。
- `2`：校验失败。
- `3`：人工确认拒绝。
- `4`：真机执行失败。

#### `src/swing_control/app/interactive_control.py`

连续中文交互控制入口。

作用：

- 启动命令行循环，提示 `飞行指令>`。
- 支持输入 `help` / `帮助` 查看示例。
- 支持输入 `q` / `退出` / `结束` 退出。
- 每条中文指令都会解析为动作 JSON、保存文件、校验、预览。
- dry-run 模式不连接无人机。
- `--execute` 模式下每条指令执行前都要求输入 `确认执行`。
- 对 `向前飞1秒`、`右转1秒` 这类交互短指令进行安全补全：自动补充起飞前检查、安全起飞和安全降落，并在终端显示“交互补全”提示。

关键常量：

- `DEFAULT_ADDR`：默认 Swing 地址。
- `DEFAULT_ACTION_OUTPUT`：默认保存到 `data/processed/instructions/interactive_last_actions.json`。
- `EXIT_WORDS`：退出词。
- `HELP_WORDS`：帮助词。
- `AIRBORNE_COMMANDS`：需要处于空中才能执行的动作集合。

关键函数：

- `main()`：交互循环主入口。
- `handle_instruction(instruction, args, logger, turn_index)`：处理一轮中文指令。
- `normalize_interactive_actions(actions)`：对交互短指令补全起飞/降落保护动作。
- `print_help()`：输出交互示例。

#### `src/swing_control/app/voice_control.py`

麦克风说话控制入口。

作用：

- 提示用户按 Enter 开始录音。
- 调用 `record_microphone()` 保存 wav 音频。
- 调用 `transcribe_audio()` 将语音转文字。
- 打印识别文本。
- 将识别文本送入 `handle_instruction()`，复用中文交互控制的解析、校验、预览、确认和执行逻辑。

关键参数：

- `--record-seconds`：每次录音时长，默认 4 秒。
- `--audio-dir`：音频保存目录，默认 `data/raw/audio`。
- `--audio-device`：录音设备，默认 `default`。
- `--asr-backend`：`auto`、`whisper` 或 `whisper-cli`。
- `--asr-model`：Whisper 模型，默认 `base`。
- `--asr-language`：语言代码，默认 `zh`。

关键函数：

- `main()`：语音控制循环。
- `normalize_spoken_instruction(text)`：对 Whisper 常见识别差异做归一化，例如 `起飛` -> `起飞`、`玄廳` -> `悬停`、`兩` -> `两`。

#### `src/swing_control/asr/microphone.py`

麦克风录音模块。

关键数据结构：

- `RecordingResult`：录音是否成功、音频路径、录音后端、错误信息。

关键函数：

- `make_audio_path(audio_dir, prefix="voice_command")`：生成带时间戳的 wav 文件路径。
- `record_microphone(output_path, seconds=4.0, device="default", sample_rate=16000)`：录音主函数，优先 `arecord`，失败后尝试 `ffmpeg`。
- `_record_with_arecord()`：使用 ALSA `arecord` 录制单声道 16 kHz wav。
- `_record_with_ffmpeg()`：使用 ffmpeg pulse 输入录制 wav。
- `_run_record_command()`：执行录音命令并检查输出文件。

#### `src/swing_control/asr/transcriber.py`

语音转文字模块。

关键数据结构：

- `TranscriptionResult`：转写是否成功、识别文本、ASR 后端、错误信息。

关键函数：

- `transcribe_audio(audio_path, backend="auto", model="base", language="zh")`：ASR 主函数。
- `_transcribe_with_python_whisper()`：使用 Python `openai-whisper` 包。
- `_transcribe_with_whisper_cli()`：使用 `whisper` 命令行。

#### `src/swing_control/app/parse_instruction.py`

单独解析中文指令入口。

作用：

- 仅负责把中文指令转动作 JSON。
- 可选 `--dry-run`，此时会继续做校验和动作预览。
- 适合单独调试模型输出。

关键函数：

- `main()`：解析参数、调用 `parse_instruction()`、可选校验与预览。

#### `src/swing_control/app/dry_run_actions.py`

动作 JSON dry-run 入口。

作用：

- 从 `--demo`、`--json` 或 `--file` 加载动作序列。
- 调用 `validate_action_sequence()`。
- 调用 `plan_actions()`。
- 打印动作序列和 pyparrot 预览。
- 可选 `--confirm` 测试人工确认，但不执行无人机。

关键对象：

- `DEMO_ACTIONS`：内置示例动作。

关键函数：

- `load_actions(args)`：从 demo、文件或 JSON 字符串读取动作。
- `print_steps(steps)`：打印 dry-run 动作序列。
- `main()`：CLI 主流程。

#### `src/swing_control/app/execute_actions.py`

动作 JSON 真机执行入口。

作用：

- 从文件或 JSON 字符串读取动作。
- 校验动作。
- 输出 dry-run 预览。
- 必要时人工确认。
- 调用 `SwingActionExecutor` 真机执行。
- 写入日志。

关键函数：

- `load_actions(args)`：加载动作 JSON。
- `main()`：真机动作执行主流程。

### 4.3 自然语言解析模块

#### `src/swing_control/nlp/instruction_parser.py`

中文指令解析为动作 JSON。

关键常量：

- `DEFAULT_MODEL`：默认从环境变量 `SWING_LLM_MODEL` 获取，否则为 `qwen3.5:4b`。
- `SYSTEM_PROMPT`：限制模型只能输出 JSON 数组，只能使用项目支持的工具。

关键数据结构：

- `ParseResult`：
  - `ok`：解析是否成功。
  - `actions`：动作 JSON 列表。
  - `raw_output`：模型原始输出。
  - `error`：错误信息。

关键函数：

- `parse_instruction(instruction, model=DEFAULT_MODEL)`：主解析函数。先调用 Ollama HTTP，失败后调用 Ollama CLI；如模型输出不是 JSON 数组，则尝试规则兜底。
- `_call_ollama_http(model, prompt)`：请求 `http://127.0.0.1:11434/api/generate`，使用 `format: json`、`stream: false`、`think: false`、低温度输出。
- `_call_ollama_cli(model, prompt)`：通过 `ollama run` 调用模型。
- `_extract_json_array(text)`：从模型输出中截取第一个 `[` 到最后一个 `]`，解析为 JSON 数组。
- `_rule_based_parse(instruction)`：规则兜底解析，支持起飞、降落、悬停、前后左右、左右转、上升、下降等常见中文表达。
- `_extract_seconds(text, keywords)`：从中文表达中提取秒数。
- `_chinese_number_to_float(value)`：将“半、一、二、两、三...”转换为数字。
- `_clamp_duration(value)`：将时长限制在 `0.2` 到 `5.0` 秒。

### 4.4 安全校验模块

#### `src/swing_control/safety/action_validator.py`

动作 JSON 安全校验核心。

关键数据结构：

- `ParamRule`：描述参数类型、最小值、最大值。
- `ToolRule`：描述工具必填参数、可选参数、参数规则、是否要求已起飞、是否是运动动作、是否需要人工确认。
- `ValidationResult`：返回校验结果、错误、警告、是否需要人工确认。

支持工具：

```text
pre_flight_check
get_status
takeoff
land
hover
fly_forward
fly_backward
fly_left
fly_right
turn_left
turn_right
fly_up
fly_down
switch_plane_forward
switch_quadricopter
error
```

参数范围：

- `duration_s`：`0.2` 到 `5.0`。
- `speed`：`1.0` 到 `30.0`。
- `yaw`：`1.0` 到 `30.0`。
- `vertical_movement`：`1.0` 到 `30.0`。
- `message`：字符串。

关键函数：

- `validate_action(action, index)`：校验单个动作对象，检查 tool、parameters、必填参数、未知参数、类型和值域。
- `validate_action_sequence(actions, max_actions=12, max_motion_duration_s=20.0)`：校验完整动作序列。检查是否为数组、是否为空、动作数量、`error` 是否单独出现、起飞/降落顺序、降落后是否继续动作、运动是否需要先起飞、累计运动时间、是否需要人工确认。
- `_demo()`：本模块直接运行时的示例校验。

重要安全逻辑：

- 包含运动动作必须包含 `takeoff`。
- 包含 `takeoff` 必须包含 `land`。
- `land`、移动、转向、升降、模式切换必须在起飞后。
- 降落后不允许继续飞行动作。
- `error` 工具只能单独出现。
- 起飞、运动、模式切换会标记为需要人工确认。

#### `src/swing_control/safety/manual_confirmation.py`

人工确认模块。

关键常量：

- `CONFIRM_PHRASE = "确认执行"`。
- `CANCEL_WORDS = {"q", "quit", "cancel", "取消", "不执行", "no", "n"}`。

关键数据结构：

- `ConfirmationResult`：包含 `confirmed` 和 `message`。

关键函数：

- `build_confirmation_summary(step_descriptions)`：生成即将执行动作的中文摘要。
- `request_manual_confirmation(step_descriptions, input_func=input, output_func=print)`：要求用户输入固定短语。只有完全输入 `确认执行` 才放行。

### 4.5 动作规划与 dry-run 模块

#### `src/swing_control/planning/action_planner.py`

将已校验动作转换为可读的 dry-run 步骤。

关键数据结构：

- `PlannedStep`：
  - `index`：序号。
  - `tool`：动作工具名。
  - `description`：中文动作说明。
  - `pyparrot_preview`：对应 pyparrot 调用预览。
  - `parameters`：原始参数。

关键函数：

- `_num(params, name, default=0.0)`：安全取数值参数。
- `plan_action(action, index)`：单条动作转成 `PlannedStep`。
- `plan_actions(actions)`：动作数组转 dry-run 步骤数组。

动作预览映射：

- `takeoff` -> `swing.safe_takeoff(duration_s)`
- `land` -> `swing.safe_land(duration_s)`
- `hover` -> `swing.smart_sleep(duration_s)`
- `fly_forward` -> `swing.fly_direct(roll=0, pitch=speed, ...)`
- `fly_backward` -> `pitch=-speed`
- `fly_left` -> `roll=-speed`
- `fly_right` -> `roll=speed`
- `turn_left` -> `yaw=-yaw`
- `turn_right` -> `yaw=yaw`
- `fly_up` -> `vertical_movement=vertical`
- `fly_down` -> `vertical_movement=-vertical`
- `switch_plane_forward` -> `swing.set_flying_mode("plane_forward")`
- `switch_quadricopter` -> `swing.set_flying_mode("quadricopter")`

### 4.6 真机执行模块

#### `src/swing_control/flight/swing_action_executor.py`

pyparrot 真机执行核心。

关键数据结构：

- `ExecutionResult`：
  - `ok`：是否执行成功。
  - `executed_tools`：已执行动作列表。
  - `errors`：错误列表。
  - `log_path`：日志路径。

关键类：

- `SwingActionExecutor`

构造参数：

- `addr`：Swing BLE 地址。
- `retries`：连接重试次数。
- `swing_factory`：可注入工厂，便于测试时替换真实 Swing。
- `auto_land_on_error`：异常时是否自动降落。
- `logger`：JSONL 日志器。

关键方法：

- `_default_swing_factory(addr)`：默认导入 `pyparrot.Minidrone.Swing` 并创建对象。
- `connect()`：执行 `Swing(addr).connect(num_retries=retries)`。
- `disconnect()`：断开连接。
- `execute(actions, validate=True)`：可选再次校验、连接无人机、逐条执行动作、异常处理、最终断开连接。
- `execute_action(action)`：将单条动作映射到 pyparrot 调用。
- `_log(event, **fields)`：写日志。
- `_log_path()`：返回日志路径。

执行映射：

- `pre_flight_check` -> `ask_for_state_update()` + `smart_sleep(1)`
- `get_status` -> `ask_for_state_update()` + `smart_sleep(1)`
- `takeoff` -> `safe_takeoff(duration_s)`
- `land` -> `safe_land(duration_s)`
- `hover` -> `smart_sleep(duration_s)`
- `fly_forward/backward/left/right` -> `fly_direct(...)`
- `turn_left/right` -> `fly_direct(yaw=...)`
- `fly_up/down` -> `fly_direct(vertical_movement=...)`
- `switch_plane_forward` -> `set_flying_mode("plane_forward")`
- `switch_quadricopter` -> `set_flying_mode("quadricopter")`

辅助函数：

- `_float(params, name)`：参数转 float。
- `_roll_pitch_for_motion(tool, speed)`：计算前后左右移动对应的 roll/pitch。

异常安全：

- 如果执行过程中抛异常且 `airborne=True`，会尝试 `safe_land(5)`。
- 无论成功或失败，只要已连接，最终都会 `disconnect()`。

### 4.7 日志模块

#### `src/swing_control/logging_utils.py`

JSONL 运行日志工具。

关键类：

- `JsonlRunLogger`

关键方法：

- `__init__(log_dir="data/logs", prefix="swing_run", run_type="unknown")`：创建日志目录和日志文件。
- `log(event, **fields)`：追加一条事件。
- `finish(exit_code, **fields)`：写入 `run_finished` 事件。

辅助函数：

- `_jsonable(value)`：将 dataclass、Path、dict、list 等转换成可 JSON 序列化对象。

日志文件格式：

```text
data/logs/swing_run_YYYYMMDD_HHMMSS_microseconds.jsonl
```

常见事件：

```text
instruction_received
instruction_parsed
actions_saved
actions_loaded
validation_result
planned_steps
manual_confirmation
execution_requested
connect_start
connect_result
action_start
action_done
execution_done
execution_exception
auto_land_start
auto_land_done
disconnect_start
disconnect_done
run_finished
```

### 4.8 包初始化与占位模块

- `src/swing_control/__init__.py`：Python 包初始化文件。
- `src/swing_control/app/__init__.py`：app 子包初始化。
- `src/swing_control/nlp/__init__.py`：nlp 子包初始化。
- `src/swing_control/safety/__init__.py`：safety 子包初始化。
- `src/swing_control/planning/__init__.py`：planning 子包初始化。
- `src/swing_control/flight/__init__.py`：flight 子包初始化。
- `src/swing_control/asr/README.md`：语音识别模块占位，后续接入麦克风录音和 Whisper。
- `src/swing_control/mapping/site_map.py`：加载本地地图、匹配命名区域、检查边界和禁飞区。
- `src/swing_control/mapping/README.md`：地图模块说明。
- `src/swing_control/planning/route_planner.py`：将地图目标区域转换为 Swing 相对动作序列。

`__pycache__/` 是 Python 编译缓存，不属于项目源码。

## 5. 动作 JSON 协议

动作序列必须是 JSON 数组，每个元素格式如下：

```json
{
  "tool": "takeoff",
  "parameters": {
    "duration_s": 5
  }
}
```

示例：

```json
[
  {"tool": "pre_flight_check", "parameters": {}},
  {"tool": "takeoff", "parameters": {"duration_s": 5}},
  {"tool": "hover", "parameters": {"duration_s": 2}},
  {"tool": "land", "parameters": {"duration_s": 5}}
]
```

## 6. 蓝牙恢复技术逻辑

本项目蓝牙恢复参照 `/home/abc/桌面/LowAir-GS/pyparrot` 的自动化连接经验，重点处理 MT7925 蓝牙控制器在 Linux 下可能出现的 `No default controller available`。

恢复流程：

```text
fix_mt7925_bluetooth.sh
  -> 检查目标 USB 设备 0489:e111
  -> modprobe btusb
  -> 写入 /sys/bus/usb/drivers/btusb/new_id
  -> 找到目标接口并绑定到 btusb
  -> 禁用 autosuspend
  -> systemctl stop bluetooth
  -> modprobe -r btusb btmtk
  -> modprobe btusb
  -> rfkill unblock bluetooth
  -> systemctl start bluetooth
  -> hciconfig hciX up
  -> btmgmt power on
  -> bluetoothctl show 验证
```

常用命令：

```bash
sudo ./model/fix_mt7925_bluetooth.sh
sudo ./model/fix_mt7925_bluetooth.sh --update-firmware
sudo ./model/fix_mt7925_bluetooth.sh --install-persistent
```

入口脚本参数：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute --bluetooth-device 0489:e111
./model/run_swing_direct_flight.sh --update-bluetooth-firmware
./model/run_swing_direct_flight.sh --install-bluetooth-fix
```

判断是否恢复成功：

```bash
bluetoothctl show
```

正常应看到控制器信息和 `Powered: yes`。如果仍是 `No default controller available`，说明系统仍未注册可用 HCI 控制器，需要固件更新、重启、重新插拔设备，或更换 Linux 兼容 USB 蓝牙适配器。

## 7. Ollama 与大语言模型逻辑

当前本机已安装：

```text
ollama 0.32.5
qwen3.5:4b
openai-whisper 20250625
torch 2.13.0+cu130
```

项目默认使用：

```text
SWING_LLM_MODEL=qwen3.5:4b
```

切换模型：

```bash
SWING_LLM_MODEL=llama3.2:3b ./model/run_swing_instruction.sh "起飞后悬停2秒再降落"
```

或：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --model qwen3.5:4b
```

推荐后续下载更适合中文指令的小模型：

```bash
ollama pull qwen2.5:3b
```

当前解析器先走 HTTP API：

```text
http://127.0.0.1:11434/api/generate
```

HTTP 不可用时走：

```bash
ollama run MODEL PROMPT
```

如果模型输出不是合法动作 JSON，会触发规则兜底解析。

## 8. 运行方式汇总

### 8.1 中文指令 dry-run

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_instruction.sh "起飞后悬停2秒再降落"
```

### 8.2 中文指令真机执行

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute
```

### 8.3 指定 Swing 地址真机执行

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute --addr E0:14:89:09:3D:CB
```

### 8.4 连续中文交互 dry-run

```bash
./model/run_swing_interactive.sh
```

### 8.5 连续中文交互真机执行

```bash
./model/run_swing_interactive.sh --execute
```

已知 Swing 地址时：

```bash
./model/run_swing_interactive.sh --execute --addr E0:14:89:09:3D:CB
```

### 8.6 麦克风语音控制 dry-run

```bash
./model/run_swing_voice.sh
```

### 8.7 麦克风语音控制真机执行

```bash
./model/run_swing_voice.sh --execute
```

指定录音时长和 Whisper 模型：

```bash
./model/run_swing_voice.sh --record-seconds 5 --asr-model base
```

### 8.8 动作 JSON dry-run

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.dry_run_actions --demo
```

### 8.9 动作 JSON 真机执行

```bash
./model/run_swing_actions.sh --addr E0:14:89:09:3D:CB --file data/processed/instructions/demo_actions.json
```

### 8.10 单独解析中文指令

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" \
  --dry-run
```

### 8.11 直接 pyparrot 飞行 demo

```bash
./model/run_swing_direct_flight.sh
```

### 8.12 只测试连接

```bash
sudo /home/abc/miniconda3/bin/python model/demoSwingDirectFlight.py \
  --addr E0:14:89:09:3D:CB \
  --connect-only
```

## 9. 环境依赖

当前核心运行依赖：

```text
Python
Ollama
qwen3.5:4b
pyparrot
bluepy
untangle
zeroconf
opencv-python
numpy
BlueZ 工具：bluetoothctl / hciconfig / rfkill
```

后续语音和大模型扩展依赖：

```text
PyYAML
ollama Python 包
torch
transformers
openai-whisper
SpeechRecognition
jieba
pandas
scipy
networkx
pydantic
rich
```

安装 LLM 环境建议：

```bash
conda activate swing-control-llm
python -m pip install jieba pydantic rich SpeechRecognition transformers accelerate sentencepiece openai-whisper ollama pandas scipy networkx PyYAML
```

不要使用裸 `pip install`，避免装到错误环境。

## 10. 当前技术状态与缺口

已可运行：

- 中文指令 dry-run。
- 麦克风录音入口。
- 本地地图目标解析和简化路径规划。
- 动作 JSON dry-run。
- 动作校验。
- 动作预览。
- 日志保存。
- 真机执行代码链路。
- 蓝牙恢复脚本接入。

真机运行前仍需确认：

- `bluetoothctl show` 不能是 `No default controller available`。
- Swing 电量充足、已开机、靠近电脑。
- 操作区域空旷安全。
- 输入 `确认执行` 后才会执行真机动作。

后续建议补齐：

- 真实 GIS/GeoJSON/DEM 地图数据。
- 定位闭环、复杂避障、返航路径。
- 测试：为 `action_validator`、`instruction_parser`、`SwingActionExecutor` 增加单元测试。
- 模型提示词优化：减少 qwen3.5 输出 `{"error":"无法理解"}` 的概率。
