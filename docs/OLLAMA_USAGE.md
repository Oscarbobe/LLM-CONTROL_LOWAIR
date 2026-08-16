# Ollama 使用说明

当前机器已安装 Ollama，并已下载项目默认模型：

```text
ollama 0.32.5
qwen3.5:4b
```

Python 侧也已安装 `ollama` 与 `socksio`，可以正常 import。

## 1. 查看模型

```bash
ollama list
```

当前应能看到：

```text
qwen3.5:4b
```

## 2. 项目默认模型

当前默认模型为：

```text
qwen3.5:4b
```

相关配置：

```text
configs/default.yaml
src/swing_control/nlp/instruction_parser.py
model/run_swing_instruction.sh
model/run_swing_interactive.sh
model/run_swing_voice.sh
```

## 3. 验证文本指令解析

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" \
  --model qwen3.5:4b \
  --dry-run \
  --no-log
```

说明：

```text
qwen3.5:4b 有时会输出 {"error":"无法理解"}。
这是已知现象。
项目会启用规则兜底，仍可生成动作 JSON 并通过安全校验。
```

## 4. 可选模型对比

如果后续希望提高中文指令解析稳定性，可以额外下载：

```bash
ollama pull qwen2.5:3b
```

对比运行：

```bash
PYTHONPATH=src python -m swing_control.app.parse_instruction \
  "飞到果园上方悬停两秒再降落" \
  --model qwen2.5:3b \
  --dry-run \
  --no-log
```

## 5. 当前推荐策略

```text
地图目标指令：优先走规则/地图匹配
基础动作指令：规则兜底保证稳定
LLM：用于增强自然语言理解，不直接绕过安全校验
```

真机执行前仍必须经过：

```text
动作 JSON
→ action_validator
→ dry-run 预览
→ 人工输入“确认执行”
```
