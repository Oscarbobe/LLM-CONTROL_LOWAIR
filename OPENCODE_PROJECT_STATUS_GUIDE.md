# OpenCode 项目现状与后续实践指导

本文档用于让 OpenCode 快速了解当前 `LLM-CONTROL_LOWAIR` 项目的真实状态，并指导后续继续开发。

当前项目定位建议：

```text
自然语言 / 语音输入
→ 动作 JSON
→ 地图路径规划
→ 安全校验
→ MATLAB/Simulink 仿真验证
→ 真机执行作为可选验证
```

后续开发应优先完善 MATLAB/Simulink 仿真链路，尽量减少对真机、蓝牙和现场飞行环境的依赖。

## 一、当前已经实现的内容

### 1. 中文指令到动作 JSON

已有文件：

```text
src/swing_control/nlp/instruction_parser.py
src/swing_control/app/parse_instruction.py
src/swing_control/app/run_instruction.py
src/swing_control/app/interactive_control.py
```

当前能力：

```text
支持输入中文指令
支持调用 Ollama 本地模型
支持规则兜底解析
支持把中文指令转换为动作 JSON
支持 dry-run 输出动作预览
```

可运行命令：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src python -m swing_control.app.parse_instruction "起飞后悬停2秒再降落" --dry-run
```

注意：

```text
当前本地模型 qwen3.5:4b 对简单指令有时会输出 error。
项目目前主要依靠规则兜底保证基础指令可运行。
后续需要增强提示词和规则解析稳定性。
```

### 2. 地图目标规划

已有文件：

```text
data/maps/site_map.json
src/swing_control/mapping/site_map.py
src/swing_control/planning/route_planner.py
src/swing_control/app/map_route.py
```

当前能力：

```text
读取本地地图 JSON
识别果园、玉米地、水渠等目标区域
识别房屋、电线杆等禁飞区
检查目标点是否越界
检查目标点是否位于禁飞区
路径接近禁飞区时加入简化绕行航点
生成 Swing 动作 JSON
```

可运行命令：

```bash
PYTHONPATH=src python -m swing_control.app.map_route "飞到果园上方悬停两秒再降落"
```

当前验证结果：

```text
该命令可以成功输出地图路线、动作 JSON 和 dry-run 动作预览。
```

### 3. 安全校验

已有文件：

```text
src/swing_control/safety/action_validator.py
src/swing_control/safety/manual_confirmation.py
```

当前能力：

```text
动作白名单校验
参数类型校验
参数范围校验
起飞/运动/降落顺序校验
最大动作数量限制
最大运动时间限制
真机执行前人工确认
```

核心约束：

```text
duration_s: 0.2 到 5 秒
speed: 1 到 30
动作数量上限: 12
累计运动时间上限: 20 秒
真机执行前需要输入“确认执行”
```

### 4. 语音控制

已有文件：

```text
src/swing_control/asr/microphone.py
src/swing_control/asr/transcriber.py
src/swing_control/app/voice_control.py
model/run_swing_voice.sh
```

当前能力：

```text
麦克风录音
openai-whisper 转文字
中文识别结果归一化
接入同一套中文控制链路
保存动作 JSON
```

可运行命令：

```bash
./model/run_swing_voice.sh --check-env
./model/run_swing_voice.sh --no-log
```

注意：

```text
语音展示受环境噪声影响。
如果用于现场展示，应把语音作为加分项，而不是主展示链路。
```

### 5. 真机执行

已有文件：

```text
model/run_swing_direct_flight.sh
model/run_swing_actions.sh
model/run_swing_instruction.sh
model/run_swing_interactive.sh
model/swing_bluetooth_common.sh
model/fix_mt7925_bluetooth.sh
src/swing_control/flight/swing_action_executor.py
src/swing_control/app/execute_actions.py
```

当前能力：

```text
蓝牙恢复
扫描 Parrot Swing
连接测试
pyparrot 执行动作 JSON
异常时尝试 safe_land
执行日志保存
```

建议：

```text
后续展示尽量不要依赖真机。
真机只作为可选验证，证明系统可以接真实无人机。
```

### 6. MATLAB 脚本仿真雏形

已有文件：

```text
matlab/simulate_swing_actions.m
matlab/applySwingAction.m
matlab/checkMapSafety.m
matlab/plotSwingSimulation.m
matlab_simulink.md
```

当前能力：

```text
MATLAB 读取动作 JSON
MATLAB 读取地图 JSON
模拟无人机位置变化
绘制三维轨迹
检查地图边界
检查圆形禁飞区
输出 PASS/FAIL
```

推荐运行方式：

```matlab
cd('/home/abc/桌面/LLM-CONTROL_LOWAIR/matlab')
simulate_swing_actions
```

注意：

```text
当前 MATLAB 脚本尚未在本机 MATLAB GUI 中实际确认运行结果。
命令行中未检测到 matlab 或 octave 命令。
后续应从 MATLAB 图形界面打开项目目录运行。
```

## 二、当前最主要缺口

## 1. MATLAB 仿真闭环还不完整 — ✅ 已基本完成

> 2026-08-08 更新：matlab/README.md、matlab/actionsToTimeline.m、matlab/exportSimulationResult.m 已新增，
> simulate_swing_actions.m 已集成自动导出。当前环境未安装 MATLAB GUI，尚未实际验证运行。

当前已有脚本，但还缺：

```text
matlab/README.md              ✅ 已新增
data/simulation/              ✅ 导出逻辑已就绪
matlab/exportSimulationResult.m  ✅ 已新增
matlab/actionsToTimeline.m    ✅ 已新增
```

需要实现：

```text
一键运行说明                   ✅ 已写入 matlab/README.md
动作 JSON 转时间序列            ✅ actionsToTimeline.m
轨迹 CSV 导出                  ✅ exportSimulationResult.m
安全结果 JSON 导出             ✅ exportSimulationResult.m
仿真图片 PNG 导出              ✅ exportSimulationResult.m
```

目标：

```text
不连接真机，仅通过动作 JSON 和地图 JSON 完成完整仿真展示。
```

验收标准：

```text
MATLAB 能打开轨迹图
图中显示起飞点、目标区域、禁飞区、飞行轨迹
命令行输出 PASS 或 FAIL
data/simulation/ 下生成结果文件
```

⚠️ 待办：在装有 MATLAB 的环境中实际运行验证。

## 2. Simulink 还没有实际模型 — ✅ 已基本完成

> 2026-08-08 更新：simulink/ 目录已创建，包含 build_swing_simulink_model.m、actionsToVelocityCmd.m、README.md。
> 当前环境未安装 MATLAB/Simulink，尚未实际生成 .slx 文件。

当前没有：

```text
simulink/                              ✅ 已创建
simulink/swing_language_control_sim.slx  ⚠️ 需在 MATLAB 中运行 build_swing_simulink_model.m 生成
simulink/build_swing_simulink_model.m    ✅ 已新增
simulink/README.md                       ✅ 已新增
```

需要实现：

```text
动作时间序列输入             ✅ actionsToVelocityCmd.m (动作 JSON → [t, vx, vy, vz])
速度命令 vx/vy/vz/yaw       ✅ From Workspace + Demux
三轴积分器                   ✅ 3x Integrator blocks
x/y/z 位置输出               ✅ Mux → Scope XYZ
安全检查模块                 ✅ MATLAB Function block (Safety Check)
Scope 或 XY Graph 可视化     ✅ Scope XYZ + XY Graph
```

目标：

```text
把 MATLAB 脚本仿真升级为 Simulink 动态模型展示。
```

验收标准：

```text
运行 Simulink 模型后能看到 x/y/z 曲线
能看到二维或三维轨迹
安全信号 safeFlag 正常路线为 1
危险路线进入禁飞区时 safeFlag 变为 0
```

## 3. 地图路线命令缺少保存动作文件参数 — ✅ 已修复

`map_route.py` 已增加 `--save-actions` 参数。

当前命令：

```bash
PYTHONPATH=src python -m swing_control.app.map_route "飞到果园上方悬停两秒再降落"
```

主要是在终端打印动作 JSON。

建议修改：

```text
src/swing_control/app/map_route.py
```

增加参数：

```text
--save-actions data/processed/instructions/map_last_actions.json
```

目标命令：

```bash
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到果园上方悬停两秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json
```

MATLAB 读取：

```matlab
simulate_swing_actions('../data/processed/instructions/map_last_actions.json')
```

验收标准：

```text
命令运行后能生成 map_last_actions.json
MATLAB 可以直接读取该文件仿真
```

## 4. 自动化测试缺失

当前 `tests/` 目录基本为空，只有：

```text
tests/README.md
```

需要新增：

```text
tests/test_action_validator.py
tests/test_instruction_parser.py
tests/test_route_planner.py
tests/test_map_route_cli.py
tests/test_matlab_export_contract.py
```

测试内容：

```text
动作参数越界会失败
没有起飞就运动会失败
起飞后没有降落会失败
地图目标能正确识别
禁飞区路径能触发警告
生成的动作 JSON 可以被 MATLAB 合约读取
```

环境缺口：

```text
pytest 当前未安装
PyYAML 当前未安装
```

建议安装：

```bash
python -m pip install pytest PyYAML
```

验收标准：

```bash
PYTHONPATH=src pytest
```

全部测试通过。

## 5. 大模型解析稳定性不足

当前问题：

```text
qwen3.5:4b 有时会对简单飞行指令输出 {"error":"输入参数错误"}
项目目前主要靠规则兜底保证可运行
```

需要改进：

```text
增强 SYSTEM_PROMPT
增加更多中文示例
地图指令优先走规则/地图匹配
大模型输出错误时自动进入更强规则兜底
拒绝危险指令时输出明确原因
```

建议修改：

```text
src/swing_control/nlp/instruction_parser.py
```

目标支持指令：

```text
起飞后悬停两秒再降落
向前飞一秒
飞到果园上方悬停两秒再降落
巡视玉米地
飞到水渠旁边悬停一秒再降落
避开房屋飞到果园
返回起飞点并降落
```

验收标准：

```text
上述指令 dry-run 全部通过
动作 JSON 不出现未知 tool
参数不超出 action_validator 范围
```

## 6. 文档状态需要同步

当前部分文档可能仍有旧状态描述，例如：

```text
README.md 中可能仍写着语音控制未完成
部分 docs 文档可能没有同步 MATLAB 仿真方向
```

建议更新：

```text
README.md
TECHNICAL_DOCUMENTATION.md
docs/CURRENT_PROJECT_STATUS_AND_LOGIC.md
docs/MAP_CONTROL_USAGE.md
docs/VOICE_CONTROL_USAGE.md
matlab_simulink.md
```

目标：

```text
文档统一说明当前项目主线是 MATLAB/Simulink 仿真验证，真机是可选验证。
```

验收标准：

```text
README 中能直接看到今晚展示路线
README 中不再出现“语音未实现”等过时内容
MATLAB 运行方式清晰可复现
```

## 7. 工程化配置不足

当前缺少：

```text
pyproject.toml
pytest.ini
Makefile
```

已经新增：

```text
.gitignore
```

建议新增：

```text
pyproject.toml
pytest.ini
Makefile
```

目标：

```text
统一测试命令
统一格式检查
统一本地运行入口
```

建议 Makefile 命令：

```text
make map-demo
make text-demo
make voice-check
make test
```

验收标准：

```text
新人可以通过 README 和 Makefile 快速运行项目。
```

## 三、建议后续开发优先级

### 第一优先级：今晚/近期可展示

```text
1. ✅ 补 matlab/README.md
2. ⚠️ 从 MATLAB GUI 中实际运行 simulate_swing_actions（当前环境未安装 MATLAB，待验证）
3. ✅ 给 map_route.py 增加 --save-actions
4. ✅ 新增 data/simulation 结果输出（exportSimulationResult.m）
5. ✅ MATLAB 保存轨迹 CSV、结果 JSON、仿真 PNG
```

目标：

```text
形成稳定的“中文指令 → 动作 JSON → MATLAB 仿真图 → 安全结论”闭环。
```

### 第二优先级：项目可复现

```text
1. 更新 README.md
2. 更新 TECHNICAL_DOCUMENTATION.md
3. 补 pytest 测试
4. 补 pytest.ini 或 pyproject.toml
5. 补 Makefile
```

目标：

```text
别人拉到项目后可以按文档复现，不依赖口头解释。
```

### 第三优先级：Simulink 动态模型

```text
1. ✅ 动作 JSON 转时间序列 (actionsToVelocityCmd.m)
2. ✅ 创建 Simulink 三轴积分器模型 (build_swing_simulink_model.m)
3. ✅ 添加安全检查模块 (MATLAB Function block)
4. ✅ 添加 Scope/XY Graph (Scope XYZ + XY Graph)
5. ✅ 输出 safeFlag (Display + Stop Simulation)
```

目标：

```text
答辩或展示时可以展示真正的 Simulink 动态仿真。
```

⚠️ 待办：在装有 MATLAB/Simulink 的环境中运行 build_swing_simulink_model.m 生成 .slx 文件并验证。

### 第四优先级：算法增强 — ✅ 已完成

```text
1. ✅ 路径规划从简单绕行升级为 A*（path_planner.py）
2. ✅ 支持多个禁飞区全局规划（A* 网格同时处理所有禁飞区）
3. ✅ 支持轨迹平滑（trajectory_smoother.py）
4. ✅ 支持风扰动和位置误差模型（wind_model.py + applyWindDisturbance.m）
5. ✅ 支持返航点和备用降落点（route_planner.py return_to_home）
```

目标：

```text
项目从演示原型升级为更完整的仿真验证平台。
```

### 第五优先级：真机验证

```text
1. 只做短距离起飞、悬停、降落
2. 只证明动作 JSON 可以映射到 pyparrot
3. 不把复杂地图任务放到真机现场展示
```

目标：

```text
证明具备真机接口，但项目主链路仍以仿真为主。
```

## 四、推荐展示流程

### 主展示

```text
中文输入
→ 地图目标识别
→ 动作 JSON
→ 安全校验
→ MATLAB 仿真轨迹
→ PASS/FAIL 安全结论
```

### 推荐命令

先生成动作：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
./model/run_swing_interactive.sh --no-log
```

输入：

```text
飞到果园上方悬停两秒再降落
```

再打开 MATLAB：

```matlab
cd('/home/abc/桌面/LLM-CONTROL_LOWAIR/matlab')
simulate_swing_actions
```

讲解重点：

```text
蓝色线：飞行轨迹
绿色点/区域：目标区域
红色圆：禁飞区
PASS：未越界、未进入禁飞区、最终完成降落
```

## 五、给 OpenCode 的建议实现任务

可以按下面顺序交给 OpenCode：

```text
任务 1：✅ 已完成
为项目补齐 MATLAB 仿真闭环。新增 matlab/README.md、matlab/actionsToTimeline.m、matlab/exportSimulationResult.m，并让 simulate_swing_actions.m 在仿真结束后导出 data/simulation/latest_trajectory.csv、latest_result.json、latest_figure.png。

任务 2：✅ 已完成
修改 src/swing_control/app/map_route.py，增加 --save-actions 参数。地图规划成功后把动作 JSON 保存到指定路径，默认不改变现有终端输出。

任务 3：
补充 tests/test_action_validator.py、tests/test_route_planner.py、tests/test_instruction_parser.py，保证核心 dry-run 链路可自动测试。

任务 4：
更新 README.md 和 TECHNICAL_DOCUMENTATION.md，把项目主线改成“自然语言无人机控制的 MATLAB/Simulink 仿真验证平台，真机为可选验证”。

任务 5：
新增 pyproject.toml、pytest.ini、Makefile，提供 make map-demo、make text-demo、make voice-check、make test 等入口。
```

## 六、最终目标

本项目最终应达到：

```text
用户可以输入或说出中文飞行任务
系统把自然语言转成结构化动作 JSON
系统根据地图生成相对航线
系统提前校验动作安全
系统在 MATLAB/Simulink 中仿真飞行轨迹
系统输出安全结论和仿真结果
真机执行只作为可选验证
```

一句话定位：

```text
本项目应优先建设为“自然语言无人机控制的仿真验证平台”，而不是只依赖真机的遥控脚本。
```
