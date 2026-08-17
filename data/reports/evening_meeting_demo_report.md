# 晚间会议演示详细报告

项目名称：基于自然语言的山区无人机智能控制原型  
仓库名称：LLM-CONTROL_LOWAIR  
会议演示定位：展示“中文/语音指令 -> 地图路径规划 -> 安全校验 -> MATLAB/Simulink 仿真 -> 可选真机执行”的完整闭环  
推荐演示指令：飞到果园上方悬停两秒再降落

## 1. 一句话项目概述

本项目面向山区农业和低空经济应用场景，尝试让无人机能够理解农户的中文自然语言或语音指令，并自动转化为可校验、可仿真、可执行的飞行动作序列。当前版本优先保证仿真验证和安全闭环，真机 Parrot Swing 执行作为可选展示环节。

## 2. 演示主线

```text
中文指令 / 语音输入
  -> 自然语言解析
  -> 动作 JSON
  -> 地图目标识别
  -> A* 路径规划与禁飞区绕行
  -> 动作安全校验
  -> dry-run 执行预览
  -> MATLAB 轨迹仿真与 PASS/FAIL 结论
  -> Simulink 动态模型展示
  -> 真机执行，可选
```

本次会议建议把重点放在前三个价值点：

1. 用户不需要写程序，只需要说中文任务。
2. 系统不是简单翻译动作，而是能识别地图区域并绕开禁飞区。
3. 真机执行前必须经过安全校验、人工确认和仿真验证。

## 3. 当前已完成内容

### 3.1 中文指令解析

核心文件：

- `src/swing_control/nlp/instruction_parser.py`
- `src/swing_control/app/parse_instruction.py`

能力说明：

- 支持中文文本指令输入。
- 支持 Ollama 本地模型调用，默认模型为 `qwen3.5:4b`。
- 当模型输出不稳定时，使用规则兜底解析。
- 地图类指令会优先进入路径规划流程。

示例：

```bash
PYTHONPATH=src python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" --dry-run
```

### 3.2 地图目标识别与路径规划

核心文件：

- `data/maps/site_map.json`
- `src/swing_control/mapping/site_map.py`
- `src/swing_control/planning/route_planner.py`
- `src/swing_control/planning/path_planner.py`
- `src/swing_control/planning/trajectory_smoother.py`
- `src/swing_control/planning/wind_model.py`

地图中已定义：

- 可识别目标区域：果园、玉米地、水渠、起飞点。
- 禁飞区：房屋、电线杆。
- 飞行边界：x=[-6, 6]，y=[-6, 6]，z=[0, 3]。

会议推荐演示命令：

```bash
make map-demo
```

本次刷新验证结果：

```text
地图路径规划：成功
目标区域：果园
警告：A* 路径规划成功，5 个航点（已平滑）
动作校验：通过
```

生成的动作文件：

```text
data/processed/instructions/map_last_actions.json
```

### 3.3 动作安全校验

核心文件：

- `src/swing_control/safety/action_validator.py`
- `src/swing_control/safety/manual_confirmation.py`
- `SAFETY.md`

已实现安全规则：

- 只允许白名单动作工具。
- 限制 `duration_s`、`speed`、`yaw`、`vertical_movement` 参数范围。
- 运动动作必须先起飞。
- 起飞后必须降落。
- 降落后不允许继续飞行动作。
- 累计运动时间不能超过上限。
- 真机执行前要求人工输入确认。

安全价值：

```text
模型输出不会直接下发给无人机，必须经过 action_validator 校验。
```

### 3.4 MATLAB 仿真

核心文件：

- `matlab/simulate_swing_actions.m`
- `matlab/applySwingAction.m`
- `matlab/checkMapSafety.m`
- `matlab/plotSwingSimulation.m`
- `matlab/exportSimulationResult.m`

已有仿真导出：

```text
data/simulation/latest_figure.png
data/simulation/latest_trajectory.csv
data/simulation/latest_result.json
```

当前 `latest_result.json` 结果：

```json
{
  "ok": true,
  "safetyErrors": [],
  "finalPose": [3, 2, 0],
  "finalHeadingDeg": 0,
  "airborne": false,
  "totalTime": 18.400000000000002
}
```

会议可讲结论：

```text
仿真结论 PASS；飞行后无人机处于已降落状态；末端位置为果园目标附近；没有边界或禁飞区违规。
```

### 3.5 Simulink 动态模型

核心文件：

- `simulink/swing_language_control_sim.slx`
- `simulink/actionsToVelocityCmd.m`
- `simulink/build_swing_simulink_model.m`
- `MATLAB_SIMULINK_OPERATION_MANUAL.md`

当前状态：

- `.slx` 模型文件已存在。
- 动作转速度命令脚本已存在。
- 仍建议在 Windows MATLAB/Simulink GUI 中现场实测或录制视频。

### 3.6 语音控制入口

核心文件：

- `src/swing_control/app/voice_control.py`
- `src/swing_control/asr/microphone.py`
- `src/swing_control/asr/transcriber.py`
- `model/run_swing_voice.sh`

可展示命令：

```bash
./model/run_swing_voice.sh --check-env
./model/run_swing_voice.sh --no-log
```

建议会议中如果环境嘈杂，不现场录音，改用提前录制视频或展示命令流程。

### 3.7 真机执行，可选

核心文件：

- `src/swing_control/flight/swing_action_executor.py`
- `src/swing_control/app/execute_actions.py`
- `model/run_swing_actions.sh`
- `model/run_swing_instruction.sh`
- `model/fix_mt7925_bluetooth.sh`

当前定位：

```text
真机执行不是主验收依赖，只作为安全条件允许时的补充验证。
```

如果现场没有足够安全空间或蓝牙不稳定，建议只展示 dry-run、MATLAB/Simulink 和真机连接准备流程。

## 4. 自动化测试与交付状态

本次会议前已刷新测试：

```text
PYTHONPATH=src pytest -q
72 passed
```

覆盖范围：

- 动作校验。
- 中文解析和规则兜底。
- 地图区域识别。
- A* 路径规划。
- 禁飞区绕行。
- 路径平滑。
- 风扰动模型。
- 交付报告生成。

当前自动生成的交付报告：

```text
data/reports/latest_report.md
```

本会议版报告：

```text
data/reports/evening_meeting_demo_report.md
```

## 5. 建议会议演示流程

### 第一步：讲项目背景，约 1 分钟

要点：

- 山区农业使用无人机存在门槛。
- 传统遥控器和专业飞手成本高。
- 目标是让农户用自然语言表达任务，例如“飞到果园上方悬停两秒再降落”。
- 系统必须安全，不能让大模型直接控制真机。

### 第二步：展示项目总流程，约 1 分钟

展示文件：

```text
README.md
```

重点说明：

```text
中文/语音 -> 动作 JSON -> 地图规划 -> 安全校验 -> MATLAB/Simulink 仿真 -> 真机可选
```

### 第三步：运行地图规划 demo，约 2 分钟

命令：

```bash
make map-demo
```

讲解输出：

- 识别目标区域为果园。
- A* 路径规划成功。
- 生成 11 步动作。
- 校验结果通过。
- dry-run 预览显示对应 pyparrot 调用。

### 第四步：展示动作 JSON，约 1 分钟

文件：

```text
data/processed/instructions/map_last_actions.json
```

说明：

- JSON 是模型和飞控之间的安全中间层。
- 每个动作都有明确工具名和参数。
- 后续安全校验只接受这个结构。

### 第五步：展示地图和禁飞区，约 1 分钟

文件：

```text
data/maps/site_map.json
```

讲解：

- 果园、玉米地、水渠是语义区域。
- 房屋、电线杆是禁飞区。
- 指令中的“果园”会映射到局部坐标。
- 路径规划会绕开禁飞区。

### 第六步：展示 MATLAB 仿真结果，约 2 分钟

优先展示：

```text
data/simulation/latest_figure.png
data/simulation/latest_result.json
```

讲解：

- `ok=true` 表示仿真通过。
- `safetyErrors=[]` 表示未触碰地图边界或禁飞区。
- `finalPose=[3,2,0]` 表示最终降落到目标区域附近。
- `airborne=false` 表示流程结束时无人机不是悬空状态。

### 第七步：展示 Simulink 动态模型，约 1 到 2 分钟

展示文件：

```text
simulink/swing_language_control_sim.slx
```

如果无法现场运行：

- 打开模型截图。
- 播放提前录制的 Simulink 运行视频。
- 展示 `MATLAB_SIMULINK_OPERATION_MANUAL.md` 中的运行步骤。

### 第八步：展示测试结果和安全边界，约 1 分钟

命令：

```bash
PYTHONPATH=src pytest -q
```

讲解：

- 72 个测试全部通过。
- 重点测试动作校验和路径规划。
- 真机执行前还需要人工确认。

## 6. 现场演示备用命令

文本 dry-run：

```bash
PYTHONPATH=src python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" --dry-run
```

地图路径规划：

```bash
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到果园上方悬停两秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json
```

生成交付报告：

```bash
PYTHONPATH=src python -m swing_control.app.generate_report \
  --instruction "飞到果园上方悬停两秒再降落" \
  --output data/reports/latest_report.md
```

运行测试：

```bash
PYTHONPATH=src pytest -q
```

MATLAB 仿真：

```matlab
cd('/home/abc/桌面/LLM-CONTROL_LOWAIR/matlab')
simulate_swing_actions('../data/processed/instructions/map_last_actions.json')
```

Windows MATLAB/Simulink 操作入口：

```text
MATLAB_SIMULINK_OPERATION_MANUAL.md
```

## 7. 晚上会议前还需要补充的材料

### 7.1 必补材料

1. 终端运行截图：`make map-demo`

用途：

```text
证明自然语言地图指令能够生成动作 JSON，且校验通过。
```

建议截图内容包含：

- 输入命令。
- “地图路径规划：成功”。
- “目标区域：果园”。
- “A* 路径规划成功，5 个航点”。
- “校验结果：通过”。
- dry-run 动作预览。

2. 测试通过截图：`PYTHONPATH=src pytest -q`

用途：

```text
证明核心代码经过自动化测试验证。
```

建议截图内容包含：

```text
72 passed
```

3. MATLAB 轨迹图截图或直接展示图片

已有文件：

```text
data/simulation/latest_figure.png
```

用途：

```text
展示飞行轨迹、地图区域、禁飞区和仿真结果。
```

4. MATLAB 仿真结果截图

已有文件：

```text
data/simulation/latest_result.json
```

建议截图突出：

```text
"ok": true
"safetyErrors": []
"airborne": false
"totalTime": 18.4
```

5. Simulink 模型截图

文件：

```text
simulink/swing_language_control_sim.slx
```

用途：

```text
证明不只是脚本仿真，也有动态模型表达。
```

建议截图内容：

- 模型整体框图。
- Scope 或 XY Graph。
- safeFlag 相关输出。

### 7.2 强烈建议补充材料

1. MATLAB 仿真视频，建议 20 到 40 秒

建议内容：

```text
打开 MATLAB -> 运行 simulate_swing_actions -> 出现三维轨迹图 -> 终端显示 PASS
```

文件建议保存为：

```text
assets/matlab_simulation_demo.mp4
```

2. Simulink 运行视频，建议 20 到 40 秒

建议内容：

```text
打开 swing_language_control_sim.slx -> 运行 sim -> Scope/XY Graph 出现轨迹变化
```

文件建议保存为：

```text
assets/simulink_dynamic_demo.mp4
```

3. 语音控制短视频，建议 15 到 30 秒

建议内容：

```text
说出“飞到果园上方悬停两秒再降落” -> 终端显示识别文本 -> 生成动作预览
```

文件建议保存为：

```text
assets/voice_control_demo.mp4
```

如果会议现场环境嘈杂，不建议现场录语音，直接播放提前录制视频。

4. 真机连接或真机起降视频，可选

建议内容：

```text
展示 Parrot Swing 连接、起飞、悬停、降落中的一小段。
```

注意：

```text
真机展示必须在空旷、低高度、有人看护的环境中进行；不建议在会议室现场飞行。
```

文件建议保存为：

```text
assets/real_drone_optional_demo.mp4
```

### 7.3 可选补充材料

1. 项目结构截图

建议展示：

```text
src/swing_control/
matlab/
simulink/
data/maps/
data/simulation/
tests/
```

用途：

```text
让老师或评委快速看到工程完整性。
```

2. 申报书摘要截图

文件：

```text
三下乡项目申请.docx
```

用途：

```text
把技术 demo 和山区农业应用背景连接起来。
```

3. 安全文档截图

文件：

```text
SAFETY.md
```

用途：

```text
证明项目没有忽视低空飞行安全。
```

## 8. 当前材料完整度评估

| 材料 | 当前状态 | 晚会可用性 | 建议 |
|---|---|---|---|
| 中文指令解析 | 已实现 | 可现场演示 | 保留文本 dry-run 备用 |
| 地图路径规划 | 已实现 | 强烈建议现场演示 | 使用 `make map-demo` |
| 动作安全校验 | 已实现 | 可现场演示 | 强调模型不能直控真机 |
| 自动化测试 | 72 passed | 可截图展示 | 会议前再跑一次 |
| MATLAB 轨迹图片 | 已存在 | 可直接展示 | 补一张清晰截图 |
| MATLAB 仿真结果 JSON | 已存在 | 可展示 | 截出 PASS 结论 |
| MATLAB 仿真视频 | 未见现成 mp4 | 建议补充 | 录制 20 到 40 秒 |
| Simulink 模型 | `.slx` 已存在 | 可展示 | 补模型截图或运行视频 |
| 语音控制 | 入口已实现 | 建议视频展示 | 现场不稳定时不要硬录 |
| 真机执行 | 已实现接口 | 可选 | 不建议会议室现场飞 |

## 9. 当前风险与应对

### 风险 1：Ollama 模型现场输出不稳定

应对：

- 地图指令会优先进入规则化路径规划流程。
- 保留 `map_last_actions.json` 作为稳定演示结果。
- 现场优先演示 `make map-demo`。

### 风险 2：MATLAB/Simulink 环境不在当前 Ubuntu shell 中

应对：

- 当前已有 MATLAB 导出结果文件。
- 会议前在 Windows MATLAB GUI 中录制仿真视频。
- 现场无法运行时展示 `latest_figure.png` 和 `latest_result.json`。

### 风险 3：语音识别受现场噪声影响

应对：

- 准备语音控制录屏。
- 现场只讲流程或使用文本输入替代。

### 风险 4：真机蓝牙连接不稳定或场地不安全

应对：

- 真机只作为可选展示。
- 主验收依赖 dry-run、地图规划、安全校验和仿真。
- 如需展示真机，提前录制视频，不建议会议室内飞行。

## 10. 建议会议讲稿提纲

开场：

```text
我们的项目目标是让山区农业场景中的无人机能够理解自然语言指令，降低普通农户使用无人机的门槛。
```

技术主线：

```text
系统收到中文或语音指令后，不会直接控制无人机，而是先转成结构化动作 JSON，再结合地图做路径规划和禁飞区绕行，最后经过安全校验和仿真验证。
```

演示指令：

```text
飞到果园上方悬停两秒再降落。
```

演示结果：

```text
系统识别目标为果园，通过 A* 规划出绕开房屋和电线杆的路径，生成 11 步动作，安全校验通过，MATLAB 仿真结果 PASS。
```

安全说明：

```text
大模型只负责辅助理解指令，真正下发到无人机前必须通过动作白名单、参数范围、起降顺序和人工确认。
```

结尾：

```text
当前原型已经完成从自然语言到可验证飞行任务的闭环。后续重点是接入真实 GIS/DEM 地图、完善定位闭环，并在更真实的山区农业场景中测试。
```

## 11. 后续开发建议

近期优先级：

1. 补齐 MATLAB 仿真视频和 Simulink 运行视频。
2. 在 Windows MATLAB/Simulink 中完成一次完整实测并保存截图。
3. 增加 `SwingActionExecutor` 的 fake/mock 测试，避免测试依赖真实蓝牙。
4. 优化中文模型 prompt，提高复杂口语指令稳定性。
5. 支持 GeoJSON、DEM 或真实 GIS 地图数据。
6. 加入返航路径、低电量策略和定位误差补偿。

## 12. 会议最终结论

当前项目已经具备可演示的完整工程闭环：

```text
自然语言输入 -> 地图路径规划 -> 安全校验 -> dry-run 预览 -> MATLAB 仿真 PASS -> Simulink 模型展示
```

晚上会议可以稳定展示 Python 侧全流程和已有 MATLAB 仿真结果。会议前最需要补充的是运行截图、MATLAB 仿真视频、Simulink 模型截图或视频；真机视频可作为加分项，但不建议作为主线依赖。
