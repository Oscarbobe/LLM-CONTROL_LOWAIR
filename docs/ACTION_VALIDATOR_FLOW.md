# action_validator 校验功能实现逻辑与流程

`action_validator` 的作用是把大语言模型生成的动作序列挡在飞控执行层之前。只有通过白名单、参数、顺序和安全规则校验的动作，才允许进入 `swing_action_executor`。

## 1. 输入格式

输入必须是 JSON 数组，每个元素是一个动作对象：

```json
[
  {"tool": "pre_flight_check", "parameters": {}},
  {"tool": "takeoff", "parameters": {"duration_s": 5}},
  {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}},
  {"tool": "land", "parameters": {"duration_s": 5}}
]
```

每个动作必须包含：

- `tool`：动作名称
- `parameters`：参数对象，没有参数时传 `{}`

## 2. 校验流程

```text
LLM 输出 JSON
  -> JSON 结构校验
  -> 工具白名单校验
  -> 必填参数校验
  -> 未知参数校验
  -> 参数类型校验
  -> 参数范围校验
  -> 单条动作语义校验
  -> 整体动作序列安全校验
  -> 输出 ValidationResult
```

## 3. 工具白名单

当前允许的 Swing 工具：

```text
pre_flight_check
takeoff
land
fly_forward
fly_backward
fly_left
fly_right
turn_left
turn_right
fly_up
fly_down
hover
switch_plane_forward
switch_quadricopter
get_status
error
```

不在白名单中的工具一律拒绝。

## 4. 参数规则

### 4.1 通用时间参数

```text
duration_s: 0.2 - 5.0
```

防止模型生成过长飞行动作。

### 4.2 速度与姿态参数

```text
speed: 1 - 30
yaw: 1 - 30
vertical_movement: 1 - 30
```

这些值最终会映射到 `pyparrot` 的 `fly_direct` 参数。

## 5. 单条动作校验

每条动作独立检查：

1. 是否是对象
2. 是否包含 `tool`
3. `tool` 是否在白名单中
4. `parameters` 是否是对象
5. 必填参数是否存在
6. 是否出现未知参数
7. 参数类型是否正确
8. 参数范围是否安全

示例：

```json
{"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}}
```

通过。

```json
{"tool": "fly_forward", "parameters": {"duration_s": 20, "speed": 80}}
```

拒绝，原因是持续时间和速度都超出限制。

## 6. 序列级安全校验

单条动作合法不代表整个序列安全，因此还要检查动作顺序。

规则：

1. 空动作序列拒绝。
2. `error` 动作只能单独出现。
3. 起飞前只允许 `pre_flight_check`、`get_status`、`takeoff`、`error`。
4. 起飞后不能再次 `takeoff`。
5. 降落后不能继续飞行动作。
6. 包含飞行动作时，序列必须包含 `takeoff`。
7. 包含 `takeoff` 时，序列必须包含 `land`。
8. 动作数量不能超过 `max_actions`，默认 12。
9. 累计运动时长不能超过 `max_motion_duration_s`，默认 20 秒。
10. 包含 `takeoff` 或运动动作时，必须要求人工确认。

## 7. 输出结果

校验器输出 `ValidationResult`：

```python
ValidationResult(
    ok=True,
    errors=[],
    warnings=["动作序列包含起飞或运动动作，必须人工确认。"],
    require_manual_confirm=True,
)
```

如果失败：

```python
ValidationResult(
    ok=False,
    errors=["第2步参数 duration_s=20 超出范围，应在 [0.2, 5.0] 内"],
    warnings=[],
    require_manual_confirm=False,
)
```

## 8. 与项目其他模块的关系

```text
instruction_parser
  -> 生成动作 JSON
action_validator
  -> 拦截非法动作
swing_action_executor
  -> 只执行已通过校验的动作
logging_utils
  -> 记录校验结果与失败原因
```

## 9. 推荐运行方式

先 dry-run：

```bash
PYTHONPATH=src python -m swing_control.safety.action_validator
```

后续接入交互式控制：

```bash
PYTHONPATH=src python -m swing_control.app.interactive_text_control --dry-run
```

真机执行前必须经过：

```text
LLM JSON -> action_validator -> 用户确认 -> pyparrot执行
```

