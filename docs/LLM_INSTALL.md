# 大语言模型安装与当前状态

本文档说明当前大语言模型环境状态和后续可选扩展。当前项目已能使用本地 Ollama 模型完成 dry-run 链路，且规则兜底可保证基础飞行指令稳定生成动作 JSON。

## 1. 当前已安装状态

```text
Ollama: 0.32.5
当前模型: qwen3.5:4b
Python ollama 包: 已安装
socksio: 已安装
openai-whisper: 已安装
torch: 2.13.0+cu130, cuda=True
pytest/PyYAML/pandas/scipy/networkx: 已安装
```

测试结果：

```text
PYTHONPATH=src python -m pytest -q
72 passed
```

## 2. 验证 Ollama

```bash
ollama list
ollama run qwen3.5:4b "把'起飞后悬停2秒再降落'解析成JSON"
```

项目内验证：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" \
  --model qwen3.5:4b \
  --dry-run \
  --no-log
```

## 3. 当前模型策略

`qwen3.5:4b` 已可用，但对短飞行指令可能输出：

```json
{"error":"无法理解"}
```

项目已经设计了规则兜底：

```text
LLM 输出可用 → 使用 LLM JSON
LLM 输出不可用 → 使用规则解析
地图目标指令 → 优先进入地图规划
```

因此当前项目不依赖 LLM 直接控制无人机。

## 4. 可选下载模型

如果需要对比中文指令解析效果，可下载：

```bash
ollama pull qwen2.5:3b
```

运行：

```bash
PYTHONPATH=src python -m swing_control.app.parse_instruction \
  "飞到果园上方悬停两秒再降落" \
  --model qwen2.5:3b \
  --dry-run \
  --no-log
```

## 5. 语音识别

当前已安装 `openai-whisper`，语音环境检查通过：

```bash
./model/run_swing_voice.sh --check-env
```

语音控制：

```bash
./model/run_swing_voice.sh --no-log
```

## 6. 后续可选方向

```text
优化 instruction_parser.py 的 SYSTEM_PROMPT
增加更多中文飞行指令样例
对比 qwen2.5:3b 与 qwen3.5:4b
加入结构化输出自动修复
为语音识别误词补更多归一化规则
```

## 7. 不建议的做法

```text
不要让 LLM 输出绕过 action_validator
不要在没有 dry-run 预览和人工确认时执行真机
不要把 MATLAB/Simulink 仿真与真机执行混为一谈
不要为了模型效果下载过大的模型影响展示稳定性
```
