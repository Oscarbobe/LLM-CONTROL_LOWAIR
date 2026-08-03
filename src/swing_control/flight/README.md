# Flight 飞控模块

职责：连接无人机并下发飞控动作。

当前可运行脚本位于：

```text
model/run_swing_direct_flight.sh
model/demoSwingDirectFlight.py
```

当前已实现：

```text
swing_action_executor.py
```

它负责把通过 `action_validator` 校验并经过用户确认的动作 JSON 转换为 `pyparrot` 真机调用。
