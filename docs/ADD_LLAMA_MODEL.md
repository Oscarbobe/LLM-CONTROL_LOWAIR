# 把 Llama 加入当前项目

当前项目的大模型入口已经走 Ollama，因此加入 Llama 的方式是：

```text
下载 Llama 模型
  -> 在 parse_instruction 中指定模型名
  -> dry-run 验证 JSON 输出
  -> 再进入动作校验和真机执行流程
```

## 1. 下载 Llama 模型

推荐先用轻量模型：

```bash
ollama pull llama3.2:3b
```

验证：

```bash
ollama list
ollama run llama3.2:3b "把'起飞后悬停2秒再降落'解析成JSON"
```

## 2. 在项目中临时使用 Llama

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" \
  --model llama3.2:3b \
  --dry-run
```

## 3. 把 Llama 设为默认模型

当前项目支持环境变量：

```bash
export SWING_LLM_MODEL=llama3.2:3b
```

之后可以省略 `--model`：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" \
  --dry-run
```

## 4. 当前模型配置

配置文件位置：

```text
configs/default.yaml
```

相关字段：

```yaml
llm:
  provider: ollama
  recommended_chinese_model: qwen2.5:3b
  llama_model: llama3.2:3b
  current_local_model: qwen3.5:4b
  env_override: SWING_LLM_MODEL
```

## 5. 推荐选择

如果项目主要处理中文农业指令，仍推荐：

```text
qwen2.5:3b
```

如果你明确想使用 Llama：

```text
llama3.2:3b
```

当前本机已经有：

```text
qwen3.5:4b
```

所以现在无需下载也能先跑：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" \
  --model qwen3.5:4b \
  --dry-run
```

