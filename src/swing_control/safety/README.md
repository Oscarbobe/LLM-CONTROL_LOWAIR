# Safety 安全控制模块

职责：在飞行任务执行前后进行安全校验。

检查内容包括地理围栏、高度限制、障碍物距离、低电量、失联策略和异常指令拦截。

当前已实现：

```text
action_validator.py
manual_confirmation.py
```

它负责校验大语言模型输出的 Swing 动作序列，只有通过工具白名单、参数范围和序列安全规则的动作才允许进入飞控执行层。

`manual_confirmation.py` 负责在真机执行前要求用户输入固定确认短语，避免误触发起飞或运动动作。

详细流程见：

```text
docs/ACTION_VALIDATOR_FLOW.md
docs/MANUAL_CONFIRMATION_FLOW.md
```
