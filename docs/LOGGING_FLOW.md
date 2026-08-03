# data/logs 保存日志功能

项目运行日志统一保存到：

```text
data/logs/
```

日志格式是 JSON Lines，文件后缀为 `.jsonl`。每一行是一条事件，方便后续分析、复盘和答辩展示。

## 1. 日志模块

```text
src/swing_control/logging_utils.py
```

核心类：

```python
JsonlRunLogger
```

它会自动创建 `data/logs`，并生成唯一日志文件：

```text
data/logs/swing_run_YYYYMMDD_HHMMSS_microseconds.jsonl
```

## 2. 已接入的入口

dry-run 入口：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.dry_run_actions --file data/processed/instructions/demo_actions.json
```

真机执行入口：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.execute_actions --addr E0:14:89:09:3D:CB --file data/processed/instructions/demo_actions.json
```

一键真机脚本：

```bash
./model/run_swing_actions.sh --addr E0:14:89:09:3D:CB
```

## 3. 记录内容

dry-run 会记录：

```text
actions_loaded
validation_result
planned_steps
manual_confirmation
run_finished
```

真机执行会额外记录：

```text
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

## 4. 日志示例

```json
{"time":"2026-08-02T17:50:00","run_type":"dry_run","event":"actions_loaded","actions":[...]}
{"time":"2026-08-02T17:50:00","run_type":"dry_run","event":"validation_result","result":{"ok":true,"errors":[]}}
{"time":"2026-08-02T17:50:00","run_type":"dry_run","event":"planned_steps","steps":[...]}
{"time":"2026-08-02T17:50:01","run_type":"dry_run","event":"run_finished","exit_code":0,"status":"dry_run_done"}
```

## 5. 关闭日志

如果某次调试不想写日志，可以加：

```bash
--no-log
```

示例：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.dry_run_actions --demo --no-log
```

## 6. 指定日志目录

```bash
--log-dir /tmp/swing_logs
```

示例：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.dry_run_actions --demo --log-dir /tmp/swing_logs
```

