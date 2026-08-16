# 环境检查结果

更新时间：2026-08-12

## 1. Python 与测试

当前 Python 环境已具备项目测试所需依赖：

```text
pytest 9.1.1
PyYAML 6.0.3
ollama Python 包
socksio 1.0.0
pandas 3.0.5
scipy 1.18.0
numpy 2.4.6
networkx 3.6.1
openai-whisper 20250625
torch 2.13.0+cu130
bluepy
```

当前测试结果：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src python -m pytest -q
```

结果：

```text
72 passed

新增 Ubuntu 交付检查入口：

```bash
make check-env
make delivery-check
```
```

## 2. Ollama 与模型

已安装：

```text
ollama 0.32.5
qwen3.5:4b
```

验证：

```bash
ollama list
python -c "import ollama; print('ollama import ok')"
```

## 3. 语音环境

已检测通过：

```text
arecord
ffmpeg
whisper 命令
Python whisper
torch cuda=True
麦克风设备 ALC257 Analog
```

检查命令：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
./model/run_swing_voice.sh --check-env
```

## 4. MATLAB/Simulink

Linux shell 中未检测 `matlab`/`octave` 命令。当前 MATLAB/Simulink 操作转到 Windows 系统进行。

Windows 操作手册：

```text
MATLAB_SIMULINK_OPERATION_MANUAL.md
```

当前仓库已包含：

```text
matlab/*.m
simulink/actionsToVelocityCmd.m
simulink/build_swing_simulink_model.m
simulink/swing_language_control_sim.slx
```

仍需在 Windows MATLAB/Simulink GUI 中确认：

```text
data/simulation/latest_trajectory.csv
data/simulation/latest_result.json
data/simulation/latest_figure.png
Scope/XY Graph/safeFlag 正常显示
```

## 5. 真机环境

Linux 真机飞行前仍需确认：

```text
Bluetooth controller 可用
Swing 已开机且电量充足
操作区域安全
执行前人工输入“确认执行”
```

真机链路是可选验证，不影响 MATLAB/Simulink 仿真主线。
