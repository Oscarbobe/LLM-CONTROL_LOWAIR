# swing_action_executor 调用 pyparrot 实现逻辑

`swing_action_executor` 是真机执行层，负责把已经通过校验和人工确认的动作 JSON 转换成 `pyparrot` 调用。

## 1. 所在模块

```text
src/swing_control/flight/swing_action_executor.py
```

真机执行入口：

```text
src/swing_control/app/execute_actions.py
src/swing_control/app/run_instruction.py
```

## 2. 执行流程

```text
动作 JSON
  -> action_validator 校验
  -> action_planner 输出动作预览
  -> manual_confirmation 人工确认
  -> run_swing_actions.sh 准备蓝牙环境
  -> SwingActionExecutor 连接无人机
  -> 逐条执行 pyparrot 动作
  -> 异常时尝试安全降落
  -> 断开连接
  -> 写入 data/logs/*.jsonl
```

## 3. 动作映射

```text
takeoff -> swing.safe_takeoff(duration_s)
land -> swing.safe_land(duration_s)
hover -> swing.smart_sleep(duration_s)
get_status -> swing.ask_for_state_update()
fly_forward -> swing.fly_direct(roll=0, pitch=speed, yaw=0, vertical_movement=0, duration=duration_s)
fly_backward -> swing.fly_direct(roll=0, pitch=-speed, yaw=0, vertical_movement=0, duration=duration_s)
fly_left -> swing.fly_direct(roll=-speed, pitch=0, yaw=0, vertical_movement=0, duration=duration_s)
fly_right -> swing.fly_direct(roll=speed, pitch=0, yaw=0, vertical_movement=0, duration=duration_s)
turn_left -> swing.fly_direct(roll=0, pitch=0, yaw=-yaw, vertical_movement=0, duration=duration_s)
turn_right -> swing.fly_direct(roll=0, pitch=0, yaw=yaw, vertical_movement=0, duration=duration_s)
fly_up -> swing.fly_direct(roll=0, pitch=0, yaw=0, vertical_movement=vertical_movement, duration=duration_s)
fly_down -> swing.fly_direct(roll=0, pitch=0, yaw=0, vertical_movement=-vertical_movement, duration=duration_s)
switch_plane_forward -> swing.set_flying_mode("plane_forward")
switch_quadricopter -> swing.set_flying_mode("quadricopter")
```

## 4. 真机运行方式

先 dry-run：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.dry_run_actions --demo --confirm
```

确认动作无误后，再真机执行：

推荐使用一键脚本，它会先处理蓝牙，再进入完整执行流程：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
./model/run_swing_actions.sh --addr E0:14:89:09:3D:CB
```

如果从中文指令直接进入真机操作，推荐使用：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute
```

该脚本会先复用 `model/run_swing_direct_flight.sh` 的实机准备模式：修复蓝牙、扫描 Swing、连接测试；连接测试成功后才进入动作预览和人工确认。

也可以直接运行 Python 入口：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.execute_actions \
  --addr E0:14:89:09:3D:CB \
  --json '[{"tool":"pre_flight_check","parameters":{}},{"tool":"takeoff","parameters":{"duration_s":5}},{"tool":"hover","parameters":{"duration_s":2}},{"tool":"land","parameters":{"duration_s":5}}]'
```

程序会再次展示动作清单，并要求输入：

```text
确认执行
```

输入其他内容会取消执行。

也可以从示例文件执行：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.execute_actions \
  --addr E0:14:89:09:3D:CB \
  --file data/processed/instructions/demo_actions.json
```

## 5. 安全策略

- 执行器内部会再次依赖已校验动作，不直接接收自然语言。
- 真机执行入口会先跑 `action_validator`。
- 起飞、移动、模式切换必须人工确认。
- 如果执行过程中异常，且系统判断已经起飞，会尝试 `safe_land(5)`。
- 无论成功或失败，最后都会调用 `disconnect()`。
- 每次完整执行都会记录 JSONL 日志，默认保存在 `data/logs/`。
- 如果需要关闭日志，可在 Python 入口加 `--no-log`。

## 6. 日志事件

日志文件格式为 JSON Lines，每一行是一个事件：

```text
actions_loaded
validation_result
planned_steps
manual_confirmation
execution_requested
connect_start
connect_result
action_start
action_done
execution_done
execution_exception
auto_land_start
auto_land_done
disconnect_start
disconnect_done
```
