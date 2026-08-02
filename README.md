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
