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

- [运行环境说明](docs/ENVIRONMENT.md)
- [大语言模型安装说明](docs/LLM_INSTALL.md)
- [产品制作流程逻辑](docs/PRODUCT_BUILD_FLOW.md)
- [项目结构说明](docs/PROJECT_STRUCTURE.md)
- [Swing 自动化控制说明](model/SWING_CONTROL_GUIDE.md)

## 完整链路
中文指令
  -> Ollama/qwen2.5:3b
  -> instruction_parser 生成动作 JSON
  -> action_validator 校验安全性
  -> action_planner 输出 dry-run 预览
  -> manual_confirmation 用户输入“确认执行”
  -> run_swing_actions.sh 准备蓝牙
  -> swing_action_executor 调用 pyparrot
  -> Parrot Swing 执行动作
  -> 异常时 safe_land(5)
  -> disconnect
  -> data/logs 保存 jsonl 日志

  ## question
  还没有实现
语音输入
现在是键盘输入中文，不是麦克风说话控制。
需要补：
麦克风录音 -> Whisper/SpeechRecognition 转文字 -> 送入 interactive_control

地图与目标区域理解
现在只能理解“起飞、悬停、向前飞、转向、降落”这类基础动作。
还不能理解：
飞到果园上方
巡视玉米地
沿山坡飞一圈
到水渠旁边悬停

真实路径规划
当前 action_planner.py 是动作预览，不是真正航线规划。
还需要：
目标区域 -> 坐标/航点 -> 避障 -> 返航/降落路径

电量/状态安全闭环
现在 pre_flight_check 只是请求状态，没有真正解析电量、姿态、异常状态并拦截飞行。

更稳定的大模型解析
当前 qwen3.5:4b 经常输出 error，项目靠规则兜底保证 demo 能跑。
建议后续换或补：
ollama pull qwen2.5:3b
并优化 prompt/样例。

自动化测试
目前缺正式测试文件，建议补：
tests/test_action_validator.py
tests/test_instruction_parser.py
tests/test_interactive_control.py
tests/test_swing_action_executor_fake.py

打通真正全链路还需要的最终形态
语音输入
  -> ASR 转文字
  -> 中文交互控制
  -> LLM/规则解析
  -> 地图区域匹配
  -> 路径规划
  -> 安全校验
  -> dry-run 预览
  -> 用户确认
  -> pyparrot 真机执行
  -> 飞行状态/日志反馈
