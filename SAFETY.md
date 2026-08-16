# 安全交付说明

本项目默认把 MATLAB/Simulink 仿真作为主要验收方式，真机飞行只作为可选验证。任何连接 Parrot Swing 的命令都必须在空旷、低高度、旁边有人看护的环境中运行。

## 交付默认模式

- 默认使用 dry-run、地图规划和 MATLAB/Simulink 仿真验证，不连接无人机。
- 真机执行必须显式传入 `--execute`。
- 真机执行前会进行动作校验，并要求人工输入 `确认执行`。
- 运行日志保存到 `data/logs/*.jsonl`，语音录音保存到 `data/raw/audio/`。

## 真机飞行前检查

- Swing 电量充足，螺旋桨安装牢固。
- 起飞点周围至少 2 米无人员、墙体和易碎物。
- Ubuntu 蓝牙控制器可用，`bluetoothctl list` 能看到控制器。
- 已通过 `./model/run_swing_voice.sh --check-env` 和 `make check-env`。
- 指令先 dry-run，再执行真机。

## 禁止事项

- 不在人员头顶、狭窄走廊、窗边或户外强风环境中测试。
- 不跳过人工确认。
- 不把模型自由输出直接下发给真机，必须经过 `action_validator`。
