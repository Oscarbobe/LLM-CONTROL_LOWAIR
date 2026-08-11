# 用户确认功能实现逻辑

用户确认功能是飞控执行前的最后一道人工安全闸门。它不负责判断动作是否合法，合法性由 `action_validator` 完成；它只负责在动作将要进入真机执行前，让用户明确确认。

## 1. 所在模块

```text
src/swing_control/safety/manual_confirmation.py
```

dry-run 演示入口：

```text
src/swing_control/app/dry_run_actions.py
```

## 2. 触发条件

只有当 `action_validator` 返回：

```python
require_manual_confirm=True
```

时才需要用户确认。

会触发确认的动作包括：

```text
takeoff
fly_forward
fly_backward
fly_left
fly_right
turn_left
turn_right
fly_up
fly_down
switch_plane_forward
switch_quadricopter
```

## 3. 实现流程

```text
LLM 生成动作 JSON
  -> action_validator 校验
  -> action_planner 输出 dry-run 动作预览
  -> 判断 require_manual_confirm
  -> 展示即将执行的动作清单
  -> 要求用户输入固定确认短语
  -> 输入正确：允许进入执行器
  -> 输入错误或取消：拒绝执行
```

## 4. 固定确认短语

当前固定确认短语是：

```text
确认执行
```

取消可以输入：

```text
q
取消
no
n
```

不用简单回车确认，是为了避免误触发真机飞行。

## 5. dry-run 中演示确认

运行：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.dry_run_actions --demo --confirm
```

程序会先输出动作序列，再显示：

```text
如确认真机执行，请输入：确认执行
取消请输入：q
```

注意：当前命令仍然只是 dry-run，不会连接无人机。

## 6. 后续真机执行器接入方式

真机执行器应按这个顺序调用：

```python
validation = validate_action_sequence(actions)
if not validation.ok:
    stop()

steps = plan_actions(actions)
if validation.require_manual_confirm:
    confirmation = request_manual_confirmation(step.description for step in steps)
    if not confirmation.confirmed:
        stop()

execute_with_pyparrot(actions)
```

这样可以保证：

- 非法动作不会进入确认阶段
- 用户能看到完整动作清单
- 没有明确输入 `确认执行` 就不会进入真机执行
- dry-run 和真机执行使用同一套确认逻辑

