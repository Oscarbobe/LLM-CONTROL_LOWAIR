# dry-run 输出动作序列实现逻辑

`dry-run` 的含义是：只做解析、校验和动作预演，不连接无人机，不调用 `pyparrot` 真机飞行动作。

## 1. 输入

输入来自大语言模型生成的动作 JSON：

```json
[
  {"tool": "pre_flight_check", "parameters": {}},
  {"tool": "takeoff", "parameters": {"duration_s": 5}},
  {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}},
  {"tool": "land", "parameters": {"duration_s": 5}}
]
```

## 2. 实现流程

```text
动作 JSON
  -> action_validator 校验工具和参数
  -> action_planner 转换为计划步骤
  -> 打印自然语言动作说明
  -> 打印对应 pyparrot 调用预览
  -> 停止，不连接无人机
```

## 3. 模块分工

```text
src/swing_control/safety/action_validator.py
```

负责判断动作能不能执行。

```text
src/swing_control/planning/action_planner.py
```

负责把已通过校验的动作转换成可读步骤和 `pyparrot` 调用预览。

```text
src/swing_control/app/dry_run_actions.py
```

负责命令行入口，读取 JSON，调用校验器和规划器，输出 dry-run 结果。

## 4. 运行方式

运行内置示例：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.dry_run_actions --demo
```

直接传 JSON：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.dry_run_actions \
  --json '[{"tool":"takeoff","parameters":{"duration_s":5}},{"tool":"hover","parameters":{"duration_s":2}},{"tool":"land","parameters":{"duration_s":5}}]'
```

从文件读取：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.dry_run_actions --file data/processed/instructions/demo_actions.json
```

## 5. 输出示例

```text
校验结果： 通过

警告：
- 动作序列包含起飞、运动或模式切换，真机执行前必须人工确认
需要人工确认： 是

Dry-run 动作序列：
1. 执行起飞前安全检查
   tool: pre_flight_check
   pyparrot: # check bluetooth, battery, area, manual confirmation
2. 安全起飞，等待 5 秒
   tool: takeoff
   pyparrot: swing.safe_takeoff(5)
3. 向前飞行 2 秒，速度参数 20
   tool: fly_forward
   pyparrot: swing.fly_direct(roll=0, pitch=20, yaw=0, vertical_movement=0, duration=2)
4. 安全降落，等待 5 秒
   tool: land
   pyparrot: swing.safe_land(5)
```

## 6. 为什么这样做

`dry-run` 是真机执行前的安全缓冲层：

- 可以检查 LLM 有没有生成非法工具
- 可以检查参数是否超范围
- 可以提前看到每一步会做什么
- 可以确认最终会调用哪些 `pyparrot` 方法
- 不会启动蓝牙连接，也不会让无人机起飞
