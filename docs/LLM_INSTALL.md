# 大语言模型安装说明

本项目建议把“大语言模型环境”和“无人机飞控环境”分开安装。飞控脚本当前可以使用 `/home/abc/miniconda3/bin/python`，大语言模型建议新建 Python 3.11 环境。

## 1. 当前机器检测结果

已具备：

- Ubuntu / Linux
- NVIDIA GPU：GeForce RTX 5060 Laptop GPU
- 显存：约 8 GB
- NVIDIA Driver：595.84
- BlueZ 蓝牙工具链
- `pyparrot`
- `bluepy`
- `untangle`
- `zeroconf`
- `opencv-python`
- `numpy`

当前缺少：

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

说明：当前 base Python 是 3.13。大模型生态中 `torch`、`transformers`、`whisper` 对 Python 3.10 / 3.11 支持更稳，因此不建议直接装进 base 环境。

## 2. 方案一：本地 Ollama 方式

适合快速运行本地大语言模型，不需要自己写复杂加载代码。

### 安装 Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

验证：

```bash
ollama --version
```

### 下载并运行模型

8 GB 显存建议先用 7B / 8B 量级模型。

```bash
ollama pull qwen2.5:7b
ollama run qwen2.5:7b
```

也可以使用更小的模型：

```bash
ollama pull qwen2.5:3b
ollama run qwen2.5:3b
```

### 项目中调用 Ollama

安装 Python 客户端：

```bash
pip install ollama
```

示例：

```python
import ollama

resp = ollama.chat(
    model="qwen2.5:7b",
    messages=[
        {"role": "system", "content": "你是无人机自然语言指令解析器。"},
        {"role": "user", "content": "飞到那片玉米地上方巡视"},
    ],
)

print(resp["message"]["content"])
```

## 3. 方案二：Transformers 本地模型方式

适合后续自己控制模型加载、提示词、结构化输出和微调。

### 创建独立 conda 环境

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
conda env create -f environment-llm.yml
conda activate swing-control-llm
```

如果环境已存在：

```bash
conda env update -f environment-llm.yml --prune
conda activate swing-control-llm
```

### 验证 PyTorch

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

输出 `True` 表示 GPU 可用。

### 安装模型

建议从小模型开始：

- `Qwen/Qwen2.5-1.5B-Instruct`
- `Qwen/Qwen2.5-3B-Instruct`
- `Qwen/Qwen2.5-7B-Instruct`

8 GB 显存更推荐 1.5B / 3B；7B 可能需要量化或降低上下文长度。

示例代码：

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen2.5-1.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    torch_dtype="auto",
)

messages = [
    {"role": "system", "content": "你是无人机自然语言指令解析器，只输出 JSON。"},
    {"role": "user", "content": "飞到那片玉米地上方巡视"},
]

text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
)
inputs = tokenizer([text], return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=256)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 4. 语音识别模型安装

如果需要把语音转文字，可以安装 Whisper：

```bash
conda activate swing-control-llm
pip install openai-whisper
sudo apt install -y ffmpeg
```

验证：

```bash
whisper --help
```

示例：

```bash
whisper data/raw/audio/demo.wav --language Chinese --model small
```

## 5. 推荐项目路线

第一阶段：

```text
文本指令 -> LLM 指令解析 -> JSON 任务
```

第二阶段：

```text
语音 -> Whisper -> 文本指令 -> LLM 指令解析 -> JSON 任务
```

第三阶段：

```text
JSON 任务 -> 地图匹配 -> 路径规划 -> 安全校验 -> 飞控执行
```

## 6. 不建议的做法

- 不建议直接在 base Python 3.13 里安装完整 LLM 依赖。
- 不建议一开始就下载 14B、32B 或更大的模型。
- 不建议在未完成安全校验前把大模型输出直接交给无人机执行。

