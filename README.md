# 基于自然语言的山区无人机智能控制项目

本项目用于构建“语音输入 -> 指令解析 -> 路径规划 -> 安全校验 -> 无人机控制”的产品原型。当前仓库已包含 Parrot Swing 自动化连接与飞行测试脚本，并补充了后续自然语言控制系统的项目结构。

## 快速运行现有自动化脚本

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_direct_flight.sh
```

已知 Swing 地址时可直接运行：

```bash
./model/run_swing_direct_flight.sh --addr E0:14:89:09:3D:CB
```

脚本会依次执行蓝牙修复、设备扫描、连接测试、安全确认和飞行 demo。

如果要执行语义规划动作 JSON，使用完整执行入口：

```bash
./model/run_swing_actions.sh --addr E0:14:89:09:3D:CB
```

默认读取：

```text
data/processed/instructions/demo_actions.json
```

如果要直接从中文指令进入完整流程，使用：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落"
```

默认只 dry-run，不连接无人机。真机执行必须显式加：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute
```

脚本会借鉴 `model/run_swing_direct_flight.sh` 的实机模式：蓝牙修复、自动扫描 Swing 地址、连接测试、动作预览、人工输入 `确认执行`，最后才调用 pyparrot 真机执行。已知地址时可跳过扫描：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute --addr E0:14:89:09:3D:CB
```

如果要进入连续中文交互控制，使用：

```bash
./model/run_swing_interactive.sh
```

默认只 dry-run。真机交互执行使用：

```bash
./model/run_swing_interactive.sh --execute
```

进入后可反复输入中文指令，例如 `起飞后悬停2秒再降落`、`向前飞1秒`。每条真机指令都会先输出动作预览，并要求输入 `确认执行`。

如果要使用麦克风说话控制，使用：

```bash
./model/run_swing_voice.sh
```

默认只录音、识别和 dry-run。真机语音执行使用：

```bash
./model/run_swing_voice.sh --execute
```

语音识别需要安装 Whisper：

```bash
python -m pip install openai-whisper
```

项目已加入本地地图能力，地图文件位于：

```text
data/maps/site_map.json
```

现在可以使用带目标区域的指令：

```text
飞到果园上方悬停两秒再降落
巡视玉米地
飞到水渠旁边悬停一秒
```

单独测试地图规划：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.map_route "飞到果园上方悬停两秒再降落"
```

## 项目结构

```text
SWING_CONTROL/
├── README.md
├── requirements.txt
├── environment.yml
├── configs/
│   └── default.yaml
├── docs/
│   ├── ENVIRONMENT.md
│   ├── PRODUCT_BUILD_FLOW.md
│   └── PROJECT_STRUCTURE.md
├── data/
│   ├── raw/
│   │   ├── audio/
│   │   └── text/
│   ├── processed/
│   │   └── instructions/
│   ├── maps/
│   └── logs/
├── model/
│   ├── SWING_CONTROL_GUIDE.md
│   ├── demoSwingDirectFlight.py
│   ├── fix_mt7925_bluetooth.sh
│   ├── run_swing_actions.sh
│   ├── run_swing_interactive.sh
│   ├── run_swing_instruction.sh
│   ├── run_swing_voice.sh
│   ├── swing_bluetooth_common.sh
│   └── run_swing_direct_flight.sh
├── src/
│   └── swing_control/
│       ├── app/
│       ├── asr/
│       ├── flight/
│       ├── mapping/
│       ├── nlp/
│       ├── planning/
│       └── safety/
├── tests/
├── assets/
└── 三下乡项目申请.docx
```

## 文档入口

- [完整技术文档](TECHNICAL_DOCUMENTATION.md)
- [当前项目缺口与完整项目逻辑](docs/CURRENT_PROJECT_STATUS_AND_LOGIC.md)
- [基于本机配置的完整项目流程](docs/FULL_LOCAL_PIPELINE.md)
- [无人机实际操作流程](docs/REAL_DRONE_OPERATION_FLOW.md)
- [真机蓝牙控制器恢复流程](docs/BLUETOOTH_RECOVERY_FLOW.md)
- [麦克风语音控制使用教程](docs/VOICE_CONTROL_USAGE.md)
- [地图能力使用教程](docs/MAP_CONTROL_USAGE.md)
- [运行环境说明](docs/ENVIRONMENT.md)
- [大语言模型安装说明](docs/LLM_INSTALL.md)
- [Ollama 使用说明](docs/OLLAMA_USAGE.md)
- [把 Llama 加入项目](docs/ADD_LLAMA_MODEL.md)
- [产品制作流程逻辑](docs/PRODUCT_BUILD_FLOW.md)
- [项目结构说明](docs/PROJECT_STRUCTURE.md)
- [dry-run 动作序列说明](docs/DRY_RUN_FLOW.md)
- [用户确认功能说明](docs/MANUAL_CONFIRMATION_FLOW.md)
- [pyparrot 真机执行说明](docs/SWING_ACTION_EXECUTOR_FLOW.md)
- [data/logs 日志说明](docs/LOGGING_FLOW.md)
- [Swing 自动化控制说明](model/SWING_CONTROL_GUIDE.md)

## 项目流程
采集山区农业场景中的自然语言指令
围绕农户常见作业需求，收集“巡田”“飞到果园上方”“喷洒农药”“查看玉米地”等口语化指令，同时记录方言表达、模糊方位描述和农事术语。

清洗并结构化标注指令数据
对采集到的语音或文本指令进行筛选、去噪、分类和标注，将自然语言整理为标准数据集。标注内容包括任务类型、目标区域、动作方式、飞行高度、方向、速度、安全限制等。

构建自然语言指令解析模块
训练或调用语音识别与语义理解模型，将农户输入的口语指令转换为机器可理解的结构化任务。例如：
“飞到那片玉米地上方巡视”
转换为：目标区域=玉米地，动作=飞行巡视，高度=安全高度，模式=巡航。

建立山区三维空间地图
利用 GIS、地形测绘或已有地图数据，对目标山区进行空间建模，标注农田边界、果园位置、植被区域、障碍物、电线、房屋、禁飞区等信息，形成局部三维数字地图。

完成语言指令与地理坐标匹配
将自然语言中的模糊空间表达转化为具体地理位置。例如“那片果园”“山坡上的农田”“靠近水渠的区域”，通过地图标注和语义匹配转换为无人机可执行的坐标点或飞行区域。

设计路径规划逻辑
根据目标坐标、地形高度、障碍物分布和任务类型，生成安全飞行路径。路径规划需要包含起飞点、目标点、巡航路线、避障路线、返航路线和降落点。

加入底层安全控制机制
在飞行任务执行前，对指令和路径进行安全检查，包括异常指令拦截、地理围栏限制、最低/最高飞行高度限制、障碍物避让、弱网环境保护、失联返航或悬停机制。

对接无人机飞控系统
将解析后的任务参数和规划路径转换为无人机控制指令，实现起飞、移动、转向、悬停、巡航、模式切换、降落等动作控制。

搭建“语音输入-指令解析-路径规划-飞行控制”闭环系统
把语音输入模块、自然语言解析模块、三维地图模块、路径规划模块、安全控制模块和无人机飞控模块集成为完整原型系统。

实验室环境仿真测试
在室内或仿真环境中测试不同指令场景，检查语音识别准确率、指令解析正确率、路径规划合理性、飞行控制响应速度和安全拦截效果。

实机连接与基础动作测试
先进行无人机连接测试，再验证基础动作，包括起飞、降落、前后左右移动、悬停、转向、模式切换等，确保飞控接口稳定可用。

山区实地场景测试
选择真实山区农业场景进行测试，验证无人机能否根据自然语言指令完成巡田、定位、飞行、避障、返航等任务。

收集测试数据并迭代优化
记录每次测试中的识别错误、路径偏差、响应延迟、飞行误差和用户反馈，反复优化语音识别、指令解析、地图匹配、路径规划和安全控制逻辑。

形成可演示产品原型
最终形成一套可运行的山区无人机自然语言控制原型系统，实现农户通过简单语言指令控制无人机完成基础农业作业任务。
