# 项目结构说明

## 根目录

```text
SWING_CONTROL/
```

项目总目录，保存申报书、运行说明、依赖文件、产品代码、数据和测试文件。

## `model/`

当前已经可以运行的 Parrot Swing 控制脚本目录。

```text
model/
├── SWING_CONTROL_GUIDE.md
├── demoSwingDirectFlight.py
├── fix_mt7925_bluetooth.sh
└── run_swing_direct_flight.sh
```

用途：

- 修复蓝牙控制器
- 扫描 Swing
- 写入 Swing 地址
- 连接测试
- 安全确认后执行飞行 demo

## `configs/`

项目配置目录。

```text
configs/default.yaml
```

用于保存默认无人机地址、飞行高度、安全限制、数据路径等配置。

## `docs/`

项目文档目录。

```text
docs/
├── ENVIRONMENT.md
├── PRODUCT_BUILD_FLOW.md
└── PROJECT_STRUCTURE.md
```

用途：

- 说明运行环境
- 说明产品制作流程
- 说明目录结构和模块职责

## `data/`

项目数据目录。

```text
data/
├── raw/
│   ├── audio/
│   └── text/
├── processed/
│   └── instructions/
├── maps/
└── logs/
```

用途：

- `raw/audio/`：原始语音数据
- `raw/text/`：原始文本指令
- `processed/instructions/`：结构化指令数据
- `maps/`：地图、地块、障碍物、禁飞区数据
- `logs/`：飞行测试和系统运行日志

## `src/swing_control/`

后续产品代码目录。

```text
src/swing_control/
├── app/
├── asr/
├── flight/
├── mapping/
├── nlp/
├── planning/
└── safety/
```

模块职责：

- `asr/`：语音识别，将语音转为文本
- `nlp/`：自然语言理解，将文本转为结构化任务
- `mapping/`：地图建模和语义区域管理
- `planning/`：航点生成和路径规划
- `safety/`：安全限制、异常指令拦截、地理围栏
- `flight/`：无人机连接和飞控指令下发
- `app/`：系统总入口，串联完整闭环流程

## `tests/`

测试目录。

建议后续补充：

- 指令解析测试
- 地图匹配测试
- 路径规划测试
- 安全规则测试
- 飞控接口模拟测试

## `assets/`

素材目录。

用于保存答辩图、流程图、系统架构图、演示图片等。

