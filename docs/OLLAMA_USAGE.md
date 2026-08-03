# Ollama 使用说明

当前机器已安装 Ollama：

```text
ollama version 0.32.5
```

但当前还没有下载模型。

## 1. 下载推荐模型

8GB 显存建议先下载小模型：

```bash
ollama pull qwen2.5:3b
```

如果 3B 跑通，再试：

```bash
ollama pull qwen2.5:7b
```

## 2. 验证 Ollama

```bash
ollama list
ollama run qwen2.5:3b "把'起飞后悬停2秒再降落'解析成JSON"
```

## 3. 在本项目中解析中文指令

```bash
cd /home/abc/桌面/SWING_CONTROL
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" \
  --model qwen2.5:3b \
  --dry-run
```

输出内容：

```text
模型原始输出
动作 JSON
校验结果
Dry-run 动作序列
日志文件路径
```

## 4. 后续接入真机

建议流程：

```text
parse_instruction 生成动作 JSON
  -> dry_run_actions 检查动作
  -> execute_actions 或 run_swing_actions.sh 真机执行
```

真机执行前仍然必须输入：

```text
确认执行
```

## 5. 使用 Llama

详见：

```text
docs/ADD_LLAMA_MODEL.md
```
