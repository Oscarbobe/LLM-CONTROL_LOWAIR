# 环境检查结果

检查时间：2026-08-02

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

缺少：

- `ollama`

## 2. 硬件与驱动

已检测到 NVIDIA GPU：

```text
NVIDIA GeForce RTX 5060 Laptop GPU, 8151 MiB, Driver 595.84
```

## 3. base 环境

Python：

```text
Python 3.13.13
```

已安装：

- `pyparrot`
- `bluepy`
- `untangle`
- `zeroconf`
- `cv2`
- `numpy`
- `pydantic`
- `rich`

缺少：

- `PyYAML`
- `SpeechRecognition`
- `jieba`
- `networkx`
- `pandas`
- `scipy`
- `torch`
- `transformers`
- `openai-whisper`
- `ollama`

说明：不建议把大模型依赖安装到 base 环境，因为当前 base 是 Python 3.13。

## 4. swing-control-llm 环境

该环境已存在：

```text
/home/abc/miniconda3/envs/swing-control-llm
Python 3.11.15
```

已安装：

- `PyYAML`
- `networkx`
- `pandas`
- `scipy`

缺少：

- `SpeechRecognition`
- `jieba`
- `pydantic`
- `rich`
- `torch`
- `transformers`
- `openai-whisper`
- `ollama`
- `accelerate`
- `sentencepiece`

## 5. 额外问题

在 `swing-control-llm` 环境中执行：

```bash
conda run -n swing-control-llm which pip
```

结果指向：

```text
/home/abc/.local/bin/pip
```

这说明直接运行 `pip` 可能不会安装到当前 conda 环境。后续安装必须使用：

```bash
conda run -n swing-control-llm python -m pip install ...
```

或先激活环境后使用：

```bash
conda activate swing-control-llm
python -m pip install ...
```

不要直接使用裸 `pip install ...`。

