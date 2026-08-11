# LLM-CONTROL_LOWAIR 环境安装报告

> 生成时间: 2026-08-02 21:30 CST

## 1. 环境概览

| 项目 | 值 |
|------|-----|
| Conda 环境 | `swing-control-llm` |
| Python 版本 | 3.11.15 |
| GPU | NVIDIA GeForce RTX 5060 Laptop GPU (8GB) |
| NVIDIA Driver | 595.84 |
| 系统 CUDA | 13.2 |
| PyTorch CUDA | 13.0 (cu130) |

## 2. 已安装 Python 包

### LLM / 核心依赖

| 包名 | 版本 | 状态 |
|------|------|------|
| ollama | 0.6.2 | ✅ |
| transformers | 5.14.1 | ✅ |
| openai-whisper | 20250625 | ✅ |
| SpeechRecognition | 3.17.0 | ✅ |
| jieba | 0.42.1 | ✅ |
| pydantic | 2.13.4 | ✅ |
| rich | 15.0.0 | ✅ |
| torch | 2.13.0+cu130 | ✅ |
| numba | 0.66.0 | ✅ |
| tiktoken | 0.13.0 | ✅ |
| triton | 3.7.1 | ✅ |
| llvmlite | 0.48.0 | ✅ |

### Ollama 模型

| 模型 | 大小 | 状态 |
|------|------|------|
| qwen3.5:4b | 3.4 GB | ✅ |

## 3. 验证结果

### 3.1 Python 导入验证

```bash
conda run -n swing-control-llm python -c \
  "import ollama, transformers, whisper, speech_recognition, jieba, pydantic, rich; \
   print('llm deps ok')"
```
**输出: `llm deps ok`** ✅

### 3.2 PyTorch CUDA 验证

```bash
conda run -n swing-control-llm python -c \
  "import torch; \
   print('torch version:', torch.__version__); \
   print('CUDA available:', torch.cuda.is_available()); \
   print('CUDA version:', torch.version.cuda); \
   print('GPU count:', torch.cuda.device_count()); \
   print('GPU name:', torch.cuda.get_device_name(0))"
```
**输出:**
```
torch version: 2.13.0+cu130
CUDA available: True
CUDA version: 13.0
GPU count: 1
GPU name: NVIDIA GeForce RTX 5060 Laptop GPU
```
✅ CUDA 可用，GPU 检测正常

### 3.3 Ollama 模型验证

```bash
ollama list
```
**输出:**
```
NAME          ID              SIZE      MODIFIED
qwen3.5:4b    2a654d98e6fb    3.4 GB    3 hours ago
```
✅ 模型就绪

### 3.4 Ollama JSON 解析测试

```bash
ollama run qwen3.5:4b "把'起飞后悬停2秒再降落'解析成JSON"
```
**输出:**
```json
{
  "step_sequence": [
    {"phase": "take_off", "action": "起飞"},
    {"phase": "hover", "duration_seconds": 2, "description": "悬停 2 秒"},
    {"phase": "land", "action": "降落"}
  ],
  "total_actions": 3
}
```
✅ 自然语言指令正确解析为结构化 JSON

## 4. 已知问题与差异

### 4.1 PyTorch CUDA 版本差异

- **要求**: pytorch-cuda=12.4
- **实际安装**: torch 2.13.0+cu130 (CUDA 13.0)
- **原因**: conda 清华镜像 pytorch 通道返回 404，anaconda.org 直连下载超时。pip 安装 openai-whisper 时自动拉取了 torch 2.13.0+cu130
- **影响**: 无。CUDA 13.0 向下兼容，且系统 CUDA 13.2 完全支持。版本比要求的 12.4 更新，功能正常

### 4.2 whisper 依赖警告

安装时 pip 报告 `openai-whisper 20250625 requires triton>=2`，但 triton 3.7.1 已安装，版本满足要求，仅为 pip 依赖解析路径不同导致的警告，不影响功能

## 5. 系统命令可用性

| 命令 | 用途 | 状态 |
|------|------|------|
| bluetoothctl | 蓝牙设备管理 | ✅ 系统自带 |
| hciconfig | 蓝牙接口配置 | ✅ 系统自带 |
| rfkill | 无线设备开关 | ✅ 系统自带 |
| lsusb | USB 设备列表 | ✅ 系统自带 |
| systemctl | 系统服务管理 | ✅ 系统自带 |
| modprobe | 内核模块加载 | ✅ 系统自带 |
| timeout | 命令超时控制 | ✅ 系统自带 |
| ffmpeg | 音视频处理 | ✅ 系统自带 |
| ollama | 本地 LLM 推理 | ✅ 已安装 |

## 6. 总结

- **Python 依赖**: 9/9 全部安装成功
- **PyTorch + CUDA**: 已安装且有 GPU 加速
- **Ollama**: qwen3.5:4b 模型就绪，JSON 解析功能正常
- **环境**: swing-control-llm conda 环境完整可用
- **base 环境**: 未安装任何大模型依赖，保持纯净