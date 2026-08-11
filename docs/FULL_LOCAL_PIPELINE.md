# 基于本机配置的完整项目流程

本机已具备：

```text
Ollama 0.32.5
qwen3.5:4b
pyparrot
BlueZ 蓝牙工具
NVIDIA GPU
```

当前项目默认模型已配置为：

```text
qwen3.5:4b
```

## 1. 最完整的一条命令

只做 dry-run，不连接无人机：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
./model/run_swing_instruction.sh "起飞后悬停2秒再降落"
```

执行链路：

```text
中文指令
  -> Ollama qwen3.5:4b
  -> Swing 动作 JSON
  -> action_validator 安全校验
  -> action_planner 动作预览
  -> 保存 last_actions.json
  -> 保存 data/logs/*.jsonl
```

## 2. 真机执行命令

确认 dry-run 输出正确后，再执行：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute
```

真机执行会额外执行：

```text
蓝牙修复
  -> 自动扫描 Swing 地址
  -> 连接测试
  -> 中文指令解析
  -> 动作安全校验
  -> dry-run 动作预览
  -> 用户输入“确认执行”
  -> pyparrot 连接 Swing
  -> safe_takeoff / smart_sleep / safe_land
  -> disconnect
```

如果已经知道 Swing 地址，可以跳过扫描：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute --addr E0:14:89:09:3D:CB
```

## 3. 中间产物

解析出的动作 JSON 默认保存到：

```text
data/processed/instructions/last_actions.json
```

运行日志保存到：

```text
data/logs/
```
