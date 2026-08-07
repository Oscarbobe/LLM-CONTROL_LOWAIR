# 当前项目缺口与后续完善清单

本文档用于说明：当前项目还缺什么、哪些功能优先放到 MATLAB/Simulink 仿真中完成、每项工作的实现方式以及目标要求。

当前建议路线：

```text
优先做 MATLAB 仿真闭环
→ 再做 Simulink 可视化模型
→ 最后才考虑真机飞行验证
```

原因是：本项目的核心目的不是单纯让真机飞起来，而是展示“自然语言/语音指令如何变成安全、可解释、可验证的无人机控制流程”。MATLAB/Simulink 更适合展示路径、安全边界、禁飞区和控制逻辑，风险也比真机低。

## 一、当前项目已经具备的能力

### 1. 中文指令控制链路

当前已经能做到：

```text
中文输入
→ instruction_parser 解析
→ 生成动作 JSON
→ action_validator 校验
→ dry-run 输出动作序列
→ 保存动作文件
```

相关文件：

```text
src/swing_control/nlp/instruction_parser.py
src/swing_control/app/interactive_control.py
src/swing_control/app/run_instruction.py
src/swing_control/app/dry_run_actions.py
```

当前作用：

```text
把“飞到果园上方悬停两秒再降落”这类中文指令转成结构化动作。
```

### 2. 语音输入链路

当前已经能做到：

```text
麦克风录音
→ openai-whisper 语音识别
→ 中文文本归一化
→ 进入同一套中文控制链路
```

相关文件：

```text
src/swing_control/asr/microphone.py
src/swing_control/asr/transcriber.py
src/swing_control/app/voice_control.py
model/run_swing_voice.sh
```

当前作用：

```text
可以用说话代替键盘输入，但展示时受环境噪声影响，建议作为加分项。
```

### 3. 地图目标识别与路径规划

当前已经能做到：

```text
读取 data/maps/site_map.json
识别果园、玉米地、水渠等区域
识别房屋、电线杆等禁飞区
生成到目标点的相对动作序列
路径接近禁飞区时加入简化绕行航点
```

相关文件：

```text
data/maps/site_map.json
src/swing_control/mapping/site_map.py
src/swing_control/planning/route_planner.py
src/swing_control/app/map_route.py
```

当前作用：

```text
把“飞到某个区域”转成“起飞、前后左右移动、悬停、降落”的动作序列。
```

### 4. 动作安全校验

当前已经能做到：

```text
动作白名单校验
参数范围校验
起飞/运动/降落顺序校验
最大动作数量限制
最大运动时间限制
真机执行前人工确认
```

相关文件：

```text
src/swing_control/safety/action_validator.py
src/swing_control/safety/manual_confirmation.py
```

当前作用：

```text
防止大语言模型或用户输入产生明显危险动作。
```

### 5. 真机执行接口

当前已经能做到：

```text
蓝牙恢复
扫描 Swing
连接测试
pyparrot 执行动作 JSON
异常时尝试 safe_land
保存日志
```

相关文件：

```text
model/run_swing_direct_flight.sh
model/run_swing_actions.sh
model/run_swing_instruction.sh
model/run_swing_interactive.sh
model/swing_bluetooth_common.sh
model/fix_mt7925_bluetooth.sh
src/swing_control/flight/swing_action_executor.py
src/swing_control/logging_utils.py
```

当前作用：

```text
可以连接真机并执行基础动作。
```

但是后续展示建议不要把真机作为主线，真机只做“可选连接验证”。

### 6. MATLAB 脚本仿真雏形

当前已经新增：

```text
matlab/simulate_swing_actions.m
matlab/applySwingAction.m
matlab/checkMapSafety.m
matlab/plotSwingSimulation.m
matlab_simulink.md
```

当前作用：

```text
MATLAB 可以读取动作 JSON 和地图 JSON，模拟无人机位置变化，绘制轨迹，并检查边界和禁飞区。
```

当前还需要在 MATLAB 软件里实际打开运行一次，确认图形显示和路径读取没有问题。

## 二、今晚展示前最需要补的内容

### 任务 1：把 MATLAB 脚本仿真跑通

内容：

```text
使用 Python 生成动作 JSON
MATLAB 读取动作 JSON
MATLAB 读取地图 JSON
MATLAB 绘制三维轨迹
MATLAB 输出安全检查结果
```

方式：

先在终端生成动作：

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_interactive.sh --no-log
```

输入：

```text
飞到果园上方悬停两秒再降落
```

再打开 MATLAB，运行：

```matlab
cd('/home/abc/桌面/SWING_CONTROL/matlab')
simulate_swing_actions
```

目标要求：

```text
MATLAB 能显示一张地图轨迹图
图中能看到起飞点、目标区域、禁飞区、飞行轨迹
命令行能输出 PASS 或安全风险提示
```

验收标准：

```text
不连接无人机
不使用蓝牙
不调用 pyparrot
只靠动作 JSON 和地图 JSON 完成仿真
```

### 任务 2：补 MATLAB 使用说明

内容：

```text
在 matlab/README.md 中写清楚 MATLAB 演示步骤
说明先运行哪个 Python 命令
说明 MATLAB 打开哪个目录
说明运行哪个函数
说明怎么看结果
```

方式：

新增：

```text
matlab/README.md
```

目标要求：

```text
上台展示时不用临时想命令
按 README 的 3 步操作即可复现
```

### 任务 3：给地图路线命令增加保存动作文件能力

当前情况：

```text
python -m swing_control.app.map_route "飞到果园上方悬停两秒再降落"
```

目前主要是在终端打印动作 JSON，不够方便 MATLAB 直接读取。

建议补充：

```text
--save-actions data/processed/instructions/map_last_actions.json
```

方式：

修改：

```text
src/swing_control/app/map_route.py
```

新增参数：

```text
--save-actions
```

目标要求：

```text
地图规划命令可以直接生成 MATLAB 仿真输入文件
```

理想命令：

```bash
PYTHONPATH=src python -m swing_control.app.map_route \
  "飞到果园上方悬停两秒再降落" \
  --save-actions data/processed/instructions/map_last_actions.json
```

然后 MATLAB 可以直接读：

```matlab
simulate_swing_actions('../data/processed/instructions/map_last_actions.json')
```

### 任务 4：准备固定展示指令

内容：

准备 3 条稳定指令：

```text
飞到果园上方悬停两秒再降落
巡视玉米地
飞到水渠旁边悬停一秒再降落
```

方式：

分别运行 dry-run，确认都能生成动作 JSON：

```bash
PYTHONPATH=src python -m swing_control.app.map_route "飞到果园上方悬停两秒再降落"
PYTHONPATH=src python -m swing_control.app.map_route "巡视玉米地"
PYTHONPATH=src python -m swing_control.app.map_route "飞到水渠旁边悬停一秒再降落"
```

目标要求：

```text
至少有 1 条路线稳定通过
至少有 1 条路线能体现绕开禁飞区
至少有 1 条路线能体现不同目标区域
```

## 三、后续完整项目还需要做的事情

## 1. MATLAB 脚本仿真完善

### 1.1 当前缺口

当前 MATLAB 脚本只是第一版简化仿真，还缺：

```text
没有保存仿真结果文件
没有导出轨迹 CSV
没有导出仿真图片
没有生成仿真报告
没有把安全错误保存到日志
没有把动作时间序列单独导出
```

### 1.2 实现方式

建议新增：

```text
matlab/exportSimulationResult.m
matlab/actionsToTimeline.m
data/simulation/
```

输出：

```text
data/simulation/latest_trajectory.csv
data/simulation/latest_result.json
data/simulation/latest_figure.png
```

### 1.3 目标要求

每次 MATLAB 仿真后自动生成：

```text
轨迹点表
安全验证结果
最终位置
总飞行时间
仿真截图
```

验收标准：

```text
MATLAB 命令行显示 PASS/FAIL
根目录 data/simulation 下有可提交的结果文件
```

## 2. Simulink 模型搭建

### 2.1 当前缺口

当前只有 MATLAB 脚本，没有真正的 Simulink `.slx` 模型。

### 2.2 实现方式

建议建立：

```text
simulink/swing_language_control_sim.slx
simulink/build_swing_simulink_model.m
simulink/README.md
```

Simulink 模型结构：

```text
动作时间序列输入
→ 动作解码模块
→ vx/vy/vz/yaw 指令
→ 三轴积分器
→ x/y/z 位姿输出
→ 安全检查模块
→ Scope/XY Graph/To Workspace
```

### 2.3 目标要求

Simulink 中至少展示：

```text
x 位置曲线
y 位置曲线
z 高度曲线
二维平面轨迹
安全报警信号
```

验收标准：

```text
运行模型后能看到无人机从起飞点移动到目标点再降落
进入禁飞区时 safeFlag 变为 0
正常路线 safeFlag 始终为 1
```

## 3. 动作 JSON 到时间序列转换

### 3.1 当前缺口

Python 输出的是离散动作：

```json
[
  {"tool": "takeoff", "parameters": {"duration_s": 5}},
  {"tool": "fly_forward", "parameters": {"duration_s": 3, "speed": 20}},
  {"tool": "land", "parameters": {"duration_s": 5}}
]
```

Simulink 更适合读取时间序列：

```text
t, vx, vy, vz, yaw, mode
0, 0, 0, 0.3, 0, takeoff
5, 1, 0, 0, 0, fly_forward
8, 0, 0, -0.3, 0, land
```

### 3.2 实现方式

建议新增：

```text
matlab/actionsToTimeline.m
```

功能：

```text
读取动作 JSON
计算每个动作开始时间和结束时间
转换成 vx/vy/vz/yaw 命令
输出 timetable 或 CSV
```

### 3.3 目标要求

生成文件：

```text
data/simulation/latest_action_timeline.csv
```

字段：

```text
start_time_s
end_time_s
tool
vx_mps
vy_mps
vz_mps
yaw_dps
```

验收标准：

```text
Simulink 可以直接读取该 CSV 或 timetable 进行仿真
```

## 4. 地图安全验证升级

### 4.1 当前缺口

当前地图安全是简化版：

```text
目标点是否越界
目标点是否在禁飞区
轴向路径是否接近一个禁飞区
简单插入绕行点
```

还缺：

```text
整条轨迹的连续碰撞检测
多个禁飞区同时存在时的全局路径规划
边界附近的安全缓冲
起飞区和降落区安全检查
动态障碍物
```

### 4.2 实现方式

优先在 MATLAB 仿真里完成：

```text
对轨迹每 0.1 秒采样
每个采样点检查边界
每个采样点检查禁飞区
生成风险点列表
在图上标红风险点
```

后续在 Python 路径规划里升级：

```text
把场地网格化
用 A* 搜索或 RRT 规划路径
路径平滑
再转换为 Swing 动作 JSON
```

### 4.3 目标要求

仿真验证必须能回答：

```text
这条路线有没有越界
有没有进入禁飞区
风险发生在第几秒
风险点坐标是多少
是哪一个禁飞区导致风险
```

验收标准：

```text
MATLAB 输出风险列表
图上能看到风险位置
正常路线输出 PASS
危险路线输出 FAIL
```

## 5. 场地地图数据完善

### 5.1 当前缺口

当前地图还是演示数据：

```text
果园、玉米地、水渠、房屋、电线杆
坐标是手动设定的示例坐标
```

如果要用于真实项目或答辩展示，需要让地图数据更像一个真实山区农田场景。

### 5.2 实现方式

完善：

```text
data/maps/site_map.json
```

建议增加：

```text
山坡
作业区
返航点
备用降落点
水塘
人群区域
树木密集区
道路
```

每个区域至少包含：

```text
name
aliases
center
radius_m
```

每个禁飞区至少包含：

```text
name
center
radius_m
buffer_m
reason
```

### 5.3 目标要求

地图要能支撑这些指令：

```text
飞到果园上方悬停两秒再降落
巡视玉米地
飞到水渠旁边悬停一秒再降落
飞到山坡观察点
避开房屋飞到备用降落点
```

验收标准：

```text
每个指令都能匹配到地图区域
每个目标区域都在地图边界内
每个禁飞区都有安全缓冲
MATLAB 图中能看懂场地布局
```

## 6. 自然语言解析稳定性提升

### 6.1 当前缺口

当前项目可以用 Ollama 和规则解析，但仍存在：

```text
大模型可能输出 error
复杂中文指令解析不稳定
同义词覆盖不够
多目标任务支持不完整
巡视类指令还不够丰富
```

### 6.2 实现方式

优先采用“规则优先 + 大模型辅助”的方式。

建议完善：

```text
src/swing_control/nlp/instruction_parser.py
```

新增：

```text
地图区域同义词优先匹配
动作关键词规则库
巡视任务模板
返航任务模板
异常指令拒绝模板
```

示例：

```text
巡视玉米地
→ 起飞
→ 到玉米地左侧
→ 横向移动
→ 悬停
→ 返回或降落
```

### 6.3 目标要求

至少稳定支持：

```text
起飞后悬停两秒再降落
向前飞一秒
飞到果园上方悬停两秒再降落
巡视玉米地
飞到水渠旁边
避开房屋飞到果园
返回起飞点并降落
```

验收标准：

```text
以上指令 dry-run 全部通过
动作 JSON 格式稳定
不会生成未知 tool
不会生成超出安全范围的参数
```

## 7. 语音展示稳定性提升

### 7.1 当前缺口

语音控制已经能走通，但现场展示有风险：

```text
环境噪声会影响识别
中文同音词可能识别错
短语停顿可能被拆错
麦克风设备可能变化
```

### 7.2 实现方式

建议增加：

```text
固定展示指令
识别结果二次确认
常见错词替换表
语音输入失败时自动退回键盘输入
```

相关文件：

```text
src/swing_control/app/voice_control.py
src/swing_control/asr/transcriber.py
```

### 7.3 目标要求

语音链路展示时做到：

```text
识别到文字后先打印出来
用户确认文字正确后再生成动作
识别失败不影响主展示
```

验收标准：

```text
至少一条固定语音指令可以成功转成动作 JSON
识别失败时不会退出整个程序
```

## 8. 日志与结果报告完善

### 8.1 当前缺口

当前 Python 已有 JSONL 日志，但 MATLAB 仿真还没有统一日志。

### 8.2 实现方式

建议新增：

```text
data/simulation/
```

保存：

```text
simulation_run_时间.json
simulation_trajectory_时间.csv
simulation_figure_时间.png
```

MATLAB 中保存：

```matlab
writematrix(trajectory, "data/simulation/latest_trajectory.csv")
saveas(gcf, "data/simulation/latest_figure.png")
```

Python 中可保存：

```text
输入指令
解析结果
动作 JSON
地图目标
安全警告
```

### 8.3 目标要求

每次展示后都有材料可提交：

```text
一份动作 JSON
一份轨迹 CSV
一张仿真图
一份安全结果 JSON
```

验收标准：

```text
老师或评委不运行代码，也能通过结果文件看懂项目过程
```

## 9. 自动化测试

### 9.1 当前缺口

当前缺少正式测试文件，后续改代码容易破坏已有链路。

### 9.2 实现方式

建议新增：

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
生成的动作 JSON 能被 MATLAB 读取
```

### 9.3 目标要求

运行：

```bash
pytest
```

能验证核心链路没有损坏。

验收标准：

```text
所有测试通过
每个核心模块至少有一个测试
```

## 10. 真机链路降级为可选验证

### 10.1 当前问题

真机展示存在不可控因素：

```text
蓝牙控制器可能异常
无人机电池可能不足
现场空间可能不安全
飞行姿态可能受干扰
没有实时定位闭环
```

### 10.2 推荐方式

真机不作为主展示。

真机只展示：

```text
蓝牙扫描成功
连接成功
动作预览后需要输入“确认执行”
短距离起飞悬停降落
```

不建议现场展示：

```text
飞到果园
巡视玉米地
绕禁飞区
复杂连续动作
```

这些应该放在 MATLAB/Simulink 中展示。

### 10.3 目标要求

真机链路只证明：

```text
项目具备连接真实设备的接口
动作 JSON 可以映射到 pyparrot
系统有人工确认和异常降落机制
```

验收标准：

```text
即使真机不飞，项目主展示仍然完整
```

## 四、建议的最终项目结构

建议后续完善为：

```text
SWING_CONTROL/
├── README.md
├── TECHNICAL_DOCUMENTATION.md
├── wrong.md
├── matlab_simulink.md
├── requirements.txt
├── environment.yml
├── configs/
│   └── default.yaml
├── data/
│   ├── maps/
│   │   └── site_map.json
│   ├── processed/
│   │   └── instructions/
│   ├── logs/
│   └── simulation/
│       ├── latest_action_timeline.csv
│       ├── latest_trajectory.csv
│       ├── latest_result.json
│       └── latest_figure.png
├── docs/
├── matlab/
│   ├── README.md
│   ├── simulate_swing_actions.m
│   ├── applySwingAction.m
│   ├── checkMapSafety.m
│   ├── plotSwingSimulation.m
│   ├── actionsToTimeline.m
│   └── exportSimulationResult.m
├── simulink/
│   ├── README.md
│   ├── build_swing_simulink_model.m
│   └── swing_language_control_sim.slx
├── model/
├── src/
│   └── swing_control/
└── tests/
```

## 五、推荐开发顺序

### 第一优先级：今晚可展示

```text
1. 用中文交互生成动作 JSON
2. 用 MATLAB 脚本读取动作 JSON
3. 绘制轨迹图
4. 检查禁飞区和边界
5. 输出 PASS/FAIL
```

目标：

```text
今晚能稳定展示完整链路，不依赖真机。
```

### 第二优先级：项目完整度

```text
1. map_route.py 支持保存动作文件
2. MATLAB 支持导出结果文件
3. 补 matlab/README.md
4. 补测试文件
```

目标：

```text
项目可以被别人按文档复现。
```

### 第三优先级：Simulink 展示

```text
1. 动作 JSON 转时间序列
2. 建立 Simulink 三轴积分器模型
3. 加入安全检查模块
4. 加入 Scope/XY Graph 展示
```

目标：

```text
答辩时能展示动态系统仿真，而不是只有脚本图。
```

### 第四优先级：算法增强

```text
1. 路径规划从简单绕行升级为 A* 或 RRT
2. 加入多禁飞区全局规划
3. 加入轨迹平滑
4. 加入风扰动和误差模型
```

目标：

```text
让项目从演示原型升级为更像工程系统的仿真平台。
```

### 第五优先级：真机验证

```text
1. 只做短距离起飞悬停降落
2. 只验证 pyparrot 接口
3. 不把复杂地图任务放到真机上
```

目标：

```text
证明系统可以接真实无人机，但项目主体仍以仿真验证为主。
```

## 六、今晚展示推荐方案

### 展示主线

```text
中文输入
→ 动作 JSON
→ 地图规划
→ 安全校验
→ MATLAB 仿真
→ 输出轨迹和 PASS/FAIL
```

### 展示命令

第一步，生成动作：

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_interactive.sh --no-log
```

输入：

```text
飞到果园上方悬停两秒再降落
```

第二步，MATLAB 仿真：

```matlab
cd('/home/abc/桌面/SWING_CONTROL/matlab')
simulate_swing_actions
```

第三步，讲解结果：

```text
蓝色线是飞行轨迹
绿色点是目标区域
红色圆是禁飞区
PASS 表示没有越界、没有进入禁飞区、最终完成降落
```

### 展示时不要依赖的内容

```text
不要依赖真机飞行
不要依赖复杂语音识别
不要现场临时改地图
不要现场下载模型
不要现场调蓝牙
```

## 七、最终目标要求

项目最终应该达到：

```text
用户可以输入或说出中文飞行任务
系统能把自然语言转成结构化动作 JSON
系统能根据地图生成相对航线
系统能提前校验动作安全
系统能在 MATLAB/Simulink 中仿真飞行轨迹
系统能输出安全结论和仿真结果
真机执行只作为可选验证
```

用一句话概括：

```text
本项目最终应成为一个“自然语言无人机控制的仿真验证平台”，而不是单纯的真机遥控脚本。
```
