# 姜星海源码借鉴方案

参考源码位置：

```text
/home/abc/桌面/14-2024120228-姜星海-源代码
```

该源码主题为“自然语言驱动的无人机控制原型系统”，与当前 `SWING_CONTROL` 项目高度相关。它的核心路线是：

```text
自然语言指令
  -> 本地大模型生成工具调用序列
  -> 工具调用合法性校验
  -> 转换为 MAVSDK / MAVLink 控制指令
  -> 无人机执行
  -> dry-run 基准测试与结果分析
```

当前项目使用 Parrot Swing 和 `pyparrot`，不是 Pixhawk / ArduPilot / MAVSDK，因此不能直接照搬飞控代码，但可以完整借鉴它的“语义规划中间层”设计。

## 1. 可直接借鉴的结构

姜星海源码结构：

```text
辅助脚本/
├── 语义规划/
│   ├── interactive_nlp_control.py
│   ├── dry_run_benchmark.py
│   ├── tool_call_validator.py
│   ├── instruction_to_mavlink_converter.py
│   └── result_analyzer.py
├── 无人机控制/
│   └── mavsdk_basic_control.py
├── 机载推理/
├── 硬件测试/
└── 香橙派环境配置/
```

对应迁移到当前项目：

```text
src/swing_control/
├── app/
│   └── interactive_text_control.py
├── nlp/
│   └── instruction_parser.py
├── safety/
│   └── action_validator.py
├── planning/
│   └── action_planner.py
├── flight/
│   └── swing_action_executor.py
└── evaluation/
    ├── dry_run_benchmark.py
    └── result_analyzer.py
```

## 2. 最值得借鉴的部分

### 2.1 交互式自然语言控制

参考文件：

```text
辅助脚本/语义规划/interactive_nlp_control.py
```

它的做法是：

```text
用户输入中文指令
  -> Ollama 本地模型
  -> 输出 JSON 工具调用序列
```

当前项目可改为：

```text
用户输入中文指令
  -> Ollama / Qwen 本地模型
  -> 输出 Swing 动作序列 JSON
```

示例输出：

```json
[
  {"tool": "pre_flight_check", "parameters": {}},
  {"tool": "takeoff", "parameters": {"duration_s": 5}},
  {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}},
  {"tool": "land", "parameters": {"duration_s": 5}}
]
```

### 2.2 工具调用合法性校验

参考文件：

```text
辅助脚本/语义规划/tool_call_validator.py
```

它把每个工具的参数类型、必填字段和取值范围写成白名单，这是当前项目最应该借鉴的安全层。

当前项目应定义 Swing 可用工具：

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
hover
switch_plane_forward
switch_quadricopter
get_status
```

并限制参数：

```text
duration_s: 0.2 - 5
speed/roll/pitch/yaw: -30 - 30
vertical_movement: -30 - 30
```

安全原则：

- 未通过校验的工具调用不能进入飞控层。
- 任何包含起飞的序列必须人工确认。
- 动作序列中必须有降落或取消逻辑。
- 默认 dry-run，不直接飞。

### 2.3 指令转换层

参考文件：

```text
辅助脚本/语义规划/instruction_to_mavlink_converter.py
```

它把工具调用转换为 MAVSDK 指令。当前项目应改成把工具调用转换为 `pyparrot` 指令。

迁移映射：

```text
takeoff -> swing.safe_takeoff(5)
land -> swing.safe_land(5)
fly_forward -> swing.fly_direct(pitch=20, ...)
fly_backward -> swing.fly_direct(pitch=-20, ...)
fly_left -> swing.fly_direct(roll=-20, ...)
fly_right -> swing.fly_direct(roll=20, ...)
turn_left -> swing.fly_direct(yaw=-20, ...)
turn_right -> swing.fly_direct(yaw=20, ...)
hover -> swing.smart_sleep(duration)
switch_plane_forward -> swing.set_flying_mode("plane_forward")
switch_quadricopter -> swing.set_flying_mode("quadricopter")
```

### 2.4 Dry-run 基准测试

参考文件：

```text
辅助脚本/语义规划/dry_run_benchmark.py
```

它把自然语言测试集按 L1、L2、L3、EDGE 分级，并计算工具选择准确率。

当前项目可建立自己的测试集：

```text
L1：起飞、降落、向前、向左、悬停
L2：起飞后前进再降落
L3：起飞、转向、模式切换、返回、降落
EDGE：超高、超时、未知目标、危险指令
```

输出指标：

```text
工具选择准确率
参数合法率
JSON 格式正确率
安全拦截成功率
平均响应时间
```

### 2.5 结果分析

参考文件：

```text
辅助脚本/语义规划/result_analyzer.py
```

当前项目可用它的思路生成：

```text
不同难度等级准确率
失败指令列表
安全拦截统计
响应时间统计
```

用于项目答辩和结项材料。

## 3. 不建议照搬的部分

### 3.1 MAVSDK / MAVLink 飞控代码

参考文件：

```text
辅助脚本/无人机控制/mavsdk_basic_control.py
```

该脚本面向 Pixhawk / ArduPilot，当前 Parrot Swing 走 BLE 和 `pyparrot`，所以不能直接运行或照搬。

可借鉴的是执行流程：

```text
连接无人机
  -> 等待连接成功
  -> 起飞
  -> 执行动作
  -> 降落
```

但实现要换成：

```text
pyparrot.Minidrone.Swing
```

### 3.2 香橙派 / OpenVINO / NCS2

参考目录：

```text
辅助脚本/香橙派环境配置/
辅助脚本/机载推理/
辅助脚本/硬件测试/
```

当前项目暂时不需要 Orange Pi、OpenVINO、NCS2 和 YOLOv8 机载视觉。除非后续要做目标识别，否则先不加入，避免环境过重。

### 3.3 QT 集成终端

参考目录：

```text
集成终端QT项目/
```

当前阶段不建议先做 QT 界面。优先完成命令行闭环：

```text
中文指令 -> JSON -> 校验 -> dry-run -> pyparrot执行
```

后续如果要答辩展示，再考虑用 Web 或 QT 做可视化终端。

## 4. 当前项目建议落地方案

建议在 `SWING_CONTROL` 中实现一个“Swing 语义控制最小原型”。

### 4.1 目录补充

```text
src/swing_control/
├── app/
│   └── interactive_text_control.py
├── nlp/
│   └── instruction_parser.py
├── safety/
│   └── action_validator.py
├── flight/
│   └── swing_action_executor.py
├── evaluation/
│   ├── dry_run_benchmark.py
│   └── result_analyzer.py
└── logging_utils.py
```

### 4.2 默认运行方式

动作校验器可先单独运行：

```bash
PYTHONPATH=src python -m swing_control.safety.action_validator
```

先只 dry-run：

```bash
python -m swing_control.app.interactive_text_control --dry-run
```

示例：

```text
请输入自然语言指令：起飞后向前飞两秒再降落
```

输出：

```json
[
  {"tool": "pre_flight_check", "parameters": {}},
  {"tool": "takeoff", "parameters": {"duration_s": 5}},
  {"tool": "fly_forward", "parameters": {"duration_s": 2, "speed": 20}},
  {"tool": "land", "parameters": {"duration_s": 5}}
]
```

真机执行必须显式开启：

```bash
python -m swing_control.app.interactive_text_control --execute --addr E0:14:89:09:3D:CB
```

执行前必须二次确认。

## 5. 大模型 Prompt 借鉴

姜星海源码里的 prompt 是“无人机任务规划助手 + 工具列表 + 严格 JSON 输出”。当前项目建议改成：

```text
你是 Parrot Swing 无人机自然语言控制规划器。
你的任务是把中文飞行指令转换为 JSON 工具调用序列。
只能使用工具列表中的工具，不允许编造工具。
必须严格输出 JSON 数组，不要输出解释文字。
如果指令危险、超出能力或无法理解，输出 error 工具。
```

工具列表：

```text
pre_flight_check()
takeoff(duration_s)
land(duration_s)
fly_forward(duration_s, speed)
fly_backward(duration_s, speed)
fly_left(duration_s, speed)
fly_right(duration_s, speed)
turn_left(duration_s, yaw)
turn_right(duration_s, yaw)
hover(duration_s)
switch_plane_forward()
switch_quadricopter()
get_status()
error(message)
```

## 6. 最终可交付闭环

最终项目可以做成：

```text
Ollama/Qwen 本地大模型
  -> 解析中文无人机指令
  -> 生成 Swing 工具调用 JSON
  -> action_validator 校验合法性
  -> dry-run 输出动作序列
  -> 用户确认
  -> swing_action_executor 调用 pyparrot
  -> 写入 data/logs/*.jsonl
  -> evaluation 统计准确率和安全拦截率
```

这条路线继承了姜星海源码的主要论文逻辑，同时适配当前 Parrot Swing 项目的真实硬件和现有自动化脚本。
