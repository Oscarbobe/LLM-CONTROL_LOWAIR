# App 系统入口模块

职责：串联完整闭环流程。

```text
语音输入 -> 语音识别 -> 指令解析 -> 地图匹配 -> 路径规划 -> 安全校验 -> 飞控执行 -> 日志记录
```

当前入口：

```text
parse_instruction.py
run_instruction.py
interactive_control.py
voice_control.py
dry_run_actions.py
execute_actions.py
```

`parse_instruction.py` 使用 Ollama 把中文指令转换为动作 JSON。

`run_instruction.py` 串联中文指令解析、校验、dry-run、日志保存和可选真机执行。

`interactive_control.py` 提供连续中文交互循环，支持反复输入中文指令、输出动作预览、人工确认和可选真机执行。

`voice_control.py` 提供麦克风说话控制循环，负责录音、ASR 转文字，并复用 `interactive_control.py` 的解析、预览、确认和执行逻辑。

`dry_run_actions.py` 只输出动作序列，不连接无人机。

`execute_actions.py` 会在校验和用户确认后调用 `pyparrot` 真机执行。
