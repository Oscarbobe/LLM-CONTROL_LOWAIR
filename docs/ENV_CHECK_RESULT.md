# 环境检查结果

检查时间：2026-08-03

## 1. 系统命令

已安装：

- `bluetoothctl`
- `hciconfig`
- `rfkill`
- `lsusb`
- `systemctl`
- `modprobe`
- `timeout`
- `ffmpeg`
- `arecord`
- `parec`
- `pactl`
- `ollama`
- `whisper`

## 2. 蓝牙状态

当前蓝牙控制器已可用：

```text
Controller 48:45:E6:6D:8B:70
Powered: yes
```

## 3. Ollama 与模型

已安装：

```text
ollama 0.32.5
qwen3.5:4b
```

## 4. 麦克风与 ASR

已检测到麦克风：

```text
card 1: PCH [HDA Intel PCH], device 0: ALC257 Analog
```

已安装：

```text
openai-whisper 20250625
torch 2.13.0+cu130
torch cuda=True
```

语音控制环境自检命令：

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_voice.sh --check-env
```

## 5. base Python 环境

Python：

```text
/home/abc/miniconda3/bin/python
```

已安装：

- `pyparrot`
- `bluepy`
- `untangle`
- `zeroconf`
- `cv2`
- `numpy`
- `torch`
- `openai-whisper`
- `networkx`
- `pydantic`
- `rich`

仍缺少的扩展依赖：

- `PyYAML`
- `ollama` Python 包
- `transformers`
- `SpeechRecognition`
- `jieba`
- `pandas`
- `scipy`

说明：

- 当前项目调用 Ollama 使用 HTTP/CLI，不强依赖 Python `ollama` 包。
- 当前语音控制使用 `openai-whisper`，不强依赖 `SpeechRecognition`。
- `PyYAML`、`transformers`、`jieba`、`pandas`、`scipy` 主要用于后续配置解析、模型扩展、中文分词、数据处理和路径规划扩展。

## 6. 当前可运行能力

```text
中文文本交互 dry-run: 可运行
中文文本交互真机执行: 可运行，需 Swing 开机并确认执行
麦克风语音控制 dry-run: 环境已具备
麦克风语音控制真机执行: 环境已具备，需真机安全区域
蓝牙恢复: 已接入
pyparrot 真机飞行: 已接入
```
