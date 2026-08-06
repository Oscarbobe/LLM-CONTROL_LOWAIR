# MATLAB/Simulink 仿真步骤与原理说明

本文档说明如何在不连接 Parrot Swing 真机的情况下，使用 MATLAB/Simulink 对本项目的“语言交互控制、地图路径规划、安全验证、动作执行逻辑”进行仿真。

核心目标是：

```text
中文指令 / 语音指令
→ Python 项目解析为动作 JSON
→ 地图路径规划与安全校验
→ MATLAB/Simulink 读取动作 JSON
→ 仿真无人机轨迹
→ 判断是否越界、是否进入禁飞区、是否符合飞行逻辑
```

该仿真不需要真实无人机，也不需要蓝牙控制器。它用于验证项目逻辑、展示飞行路径、辅助论文/答辩说明。

## 一、当前项目与 MATLAB 仿真的关系

本项目当前已经完成的部分：

```text
用户输入中文指令
→ swing_control.nlp.instruction_parser 解析指令
→ swing_control.planning.route_planner 根据地图生成路线
→ swing_control.safety.action_validator 校验动作是否合法
→ dry-run 输出动作序列
→ 保存 JSON 文件
```

MATLAB/Simulink 需要接管的是最后一步：

```text
读取动作 JSON
→ 按动作逐步更新无人机仿真位置
→ 画出轨迹
→ 检查地图安全
```

也就是说，MATLAB 不是替代大语言模型，而是替代真实无人机执行器 `swing_action_executor`。

## 二、仿真前需要准备的环境

### 1. Python 项目环境

先确认本项目可以生成动作 JSON：

```bash
cd /home/abc/桌面/SWING_CONTROL
PYTHONPATH=src python -m swing_control.app.map_route "飞到果园上方悬停两秒再降落"
```

如果能看到：

```text
地图路径规划：成功
动作 JSON：
校验结果：通过
```

说明 Python 侧已经可以给 MATLAB 提供仿真输入。

### 2. MATLAB 环境

MATLAB 侧建议具备：

```text
MATLAB 基础环境
Simulink
JSON 读取能力 jsondecode
绘图能力 plot / plot3 / rectangle / viscircles
```

如果只做脚本仿真，MATLAB 基础环境即可。

如果要搭建 Simulink 方块模型，需要安装 Simulink。

### 3. 不需要的环境

MATLAB 仿真阶段不需要：

```text
Parrot Swing 真机
蓝牙连接
pyparrot 真机连接
sudo 蓝牙修复脚本
openai-whisper 语音识别
Ollama 本地大模型
```

但是如果想从“中文/语音”自动生成动作 JSON，则 Python 侧仍然需要 Ollama 或规则解析能力。

## 三、仿真使用的数据文件

### 1. 地图文件

当前地图文件：

```text
data/maps/site_map.json
```

它描述的是本地测试场地，坐标单位是米。

关键字段：

```text
origin              起飞点
flight              默认飞行参数
limits              地图边界
areas               目标区域
no_fly_zones        禁飞区
landing_points      可降落点
```

示例逻辑：

```text
起飞点 = (0, 0, 0)
果园 = (3, 2, 1.5)
房屋 = 禁飞圆形区域
电线杆 = 禁飞圆形区域
```

### 2. 动作文件

交互模式会保存最近一次动作序列：

```text
data/processed/instructions/interactive_last_actions.json
```

语音模式会保存最近一次语音动作序列：

```text
data/processed/instructions/voice_last_actions.json
```

地图路线测试命令默认只在终端打印动作 JSON。若要给 MATLAB 使用，可以先通过交互 dry-run 生成文件：

```bash
./model/run_swing_interactive.sh --no-log
```

输入：

```text
飞到果园上方悬停两秒再降落
```

退出后查看：

```bash
cat data/processed/instructions/interactive_last_actions.json
```

## 四、MATLAB 脚本仿真总体步骤

推荐先做脚本仿真，再做 Simulink 仿真。

脚本仿真流程：

```text
步骤 1：读取动作 JSON
步骤 2：读取地图 JSON
步骤 3：初始化无人机状态
步骤 4：逐条执行动作
步骤 5：根据动作更新位置
步骤 6：每一步检查安全
步骤 7：绘制轨迹
步骤 8：输出仿真结论
```

## 五、步骤 1：读取动作 JSON

MATLAB 示例：

```matlab
projectRoot = "/home/abc/桌面/SWING_CONTROL";
actionFile = fullfile(projectRoot, "data/processed/instructions/interactive_last_actions.json");

actionsText = fileread(actionFile);
actions = jsondecode(actionsText);
```

### 原理

Python 侧输出的动作 JSON 是整个控制链路的中间表示。

例如：

```json
[
  {"tool": "pre_flight_check", "parameters": {}},
  {"tool": "takeoff", "parameters": {"duration_s": 5}},
  {"tool": "fly_right", "parameters": {"duration_s": 3.1, "speed": 20}},
  {"tool": "fly_forward", "parameters": {"duration_s": 3.0, "speed": 20}},
  {"tool": "hover", "parameters": {"duration_s": 2}},
  {"tool": "land", "parameters": {"duration_s": 5}}
]
```

这里的 `tool` 代表动作类型，`parameters` 代表动作参数。

MATLAB 不需要理解中文，也不需要调用大语言模型。MATLAB 只需要按照动作 JSON 执行动力学近似仿真。

## 六、步骤 2：读取地图 JSON

MATLAB 示例：

```matlab
mapFile = fullfile(projectRoot, "data/maps/site_map.json");
mapText = fileread(mapFile);
siteMap = jsondecode(mapText);
```

### 原理

地图 JSON 是安全验证的依据。

地图采用本地坐标系：

```text
x 轴：前后方向
y 轴：左右方向
z 轴：高度方向
单位：米
```

当前 Python 路径规划中的动作方向约定是：

```text
fly_forward   x 增大
fly_backward  x 减小
fly_right     y 增大
fly_left      y 减小
fly_up        z 增大
fly_down      z 减小
```

因此 MATLAB 仿真也要使用同一套方向约定，否则仿真轨迹会和 Python 规划结果不一致。

## 七、步骤 3：初始化无人机状态

MATLAB 示例：

```matlab
pose = [siteMap.origin.x, siteMap.origin.y, siteMap.origin.z];
headingDeg = 0;
airborne = false;
trajectory = pose;
safetyErrors = strings(0);
```

### 原理

仿真状态至少包括：

```text
pose        无人机位置 [x, y, z]
headingDeg 机头朝向角，单位为度
airborne    是否已经起飞
trajectory 轨迹点记录
```

当前项目的地图路径规划主要使用“轴向平移”，还没有做复杂姿态动力学。因此第一版 MATLAB 仿真可以先把无人机看成一个点质量模型。

点质量模型的含义：

```text
不模拟电机转速
不模拟气流
不模拟姿态角变化
只模拟位置随动作变化
```

这种模型适合验证“路线是否合理、是否进入禁飞区、动作顺序是否正确”。

## 八、步骤 4：逐条执行动作

MATLAB 示例：

```matlab
for i = 1:numel(actions)
    action = actions(i);
    [pose, headingDeg, airborne] = applySwingAction(pose, headingDeg, airborne, action, siteMap);
    trajectory(end + 1, :) = pose;

    errors = checkMapSafety(pose, siteMap);
    if ~isempty(errors)
        safetyErrors = [safetyErrors; errors(:)];
    end
end
```

### 原理

Python 真机执行器 `swing_action_executor` 的作用是把动作 JSON 转换为 pyparrot 调用。

MATLAB 仿真执行器的作用是把动作 JSON 转换为位置变化。

两者是并列关系：

```text
真机执行：
action JSON → swing.fly_direct(...) → 真实飞机运动

MATLAB 仿真：
action JSON → pose = pose + delta → 虚拟轨迹变化
```

## 九、步骤 5：根据动作更新位置

MATLAB 函数示例：

```matlab
function [pose, headingDeg, airborne] = applySwingAction(pose, headingDeg, airborne, action, siteMap)
    tool = string(action.tool);
    params = action.parameters;
    mps = siteMap.flight.meters_per_second;
    safeHeight = siteMap.flight.safe_height_m;

    switch tool
        case "pre_flight_check"
            % 仿真中不改变位置，只代表检查流程存在。

        case "takeoff"
            airborne = true;
            pose(3) = safeHeight;

        case "land"
            pose(3) = siteMap.origin.z;
            airborne = false;

        case "hover"
            % 悬停不改变位置。

        case "fly_forward"
            distance = params.duration_s * mps;
            pose(1) = pose(1) + distance;

        case "fly_backward"
            distance = params.duration_s * mps;
            pose(1) = pose(1) - distance;

        case "fly_right"
            distance = params.duration_s * mps;
            pose(2) = pose(2) + distance;

        case "fly_left"
            distance = params.duration_s * mps;
            pose(2) = pose(2) - distance;

        case "fly_up"
            distance = params.duration_s * mps;
            pose(3) = pose(3) + distance;

        case "fly_down"
            distance = params.duration_s * mps;
            pose(3) = pose(3) - distance;

        case "turn_left"
            headingDeg = headingDeg - params.duration_s * params.yaw;

        case "turn_right"
            headingDeg = headingDeg + params.duration_s * params.yaw;
    end
end
```

### 原理

当前项目中的地图规划用的是简化运动模型：

```text
距离 = 飞行时间 × meters_per_second
```

其中 `meters_per_second` 来自：

```text
data/maps/site_map.json → flight.meters_per_second
```

例如：

```text
meters_per_second = 1
fly_forward duration_s = 3
则仿真中 x 增加 3 米
```

注意：`speed` 参数现在主要用于 pyparrot 真机控制强度，MATLAB 第一版仿真可以先使用 `meters_per_second` 统一换算距离。后续如果要更真实，可以把 `speed` 映射成速度：

```text
实际速度 = k × speed
距离 = 实际速度 × duration_s
```

其中 `k` 需要通过实验标定。

## 十、步骤 6：地图安全检查

MATLAB 函数示例：

```matlab
function errors = checkMapSafety(pose, siteMap)
    errors = strings(0);

    if pose(1) < siteMap.limits.min_x || pose(1) > siteMap.limits.max_x
        errors(end + 1) = "x 坐标超出地图边界";
    end

    if pose(2) < siteMap.limits.min_y || pose(2) > siteMap.limits.max_y
        errors(end + 1) = "y 坐标超出地图边界";
    end

    if pose(3) < siteMap.limits.min_z || pose(3) > siteMap.limits.max_z
        errors(end + 1) = "z 高度超出安全边界";
    end

    zones = siteMap.no_fly_zones;
    for i = 1:numel(zones)
        zone = zones(i);
        protectedRadius = zone.radius_m + zone.buffer_m;
        d = hypot(pose(1) - zone.center.x, pose(2) - zone.center.y);
        if d <= protectedRadius
            errors(end + 1) = "进入禁飞区：" + string(zone.name);
        end
    end
end
```

### 原理

地图安全验证主要包含三类：

```text
1. 边界验证：不能飞出 limits
2. 高度验证：不能低于 min_z，也不能高于 max_z
3. 禁飞区验证：不能进入 no_fly_zones
```

当前禁飞区被抽象为二维圆形区域：

```text
禁飞区中心 = (cx, cy)
禁飞保护半径 = radius_m + buffer_m
无人机位置 = (x, y)
距离 d = sqrt((x - cx)^2 + (y - cy)^2)

如果 d <= 禁飞保护半径，则判定为危险
```

这样做的优点是简单、稳定、容易可视化，适合小范围教学/项目演示。

## 十一、步骤 7：绘制地图和飞行轨迹

MATLAB 示例：

```matlab
figure;
hold on;
grid on;
axis equal;
xlabel("x / m");
ylabel("y / m");
zlabel("z / m");
title("Swing 地图路径安全仿真");

plot3(trajectory(:,1), trajectory(:,2), trajectory(:,3), "-o", "LineWidth", 2);

% 绘制目标区域
areas = siteMap.areas;
for i = 1:numel(areas)
    plot3(areas(i).center.x, areas(i).center.y, areas(i).center.z, "g*", "MarkerSize", 8);
    text(areas(i).center.x, areas(i).center.y, areas(i).center.z, string(areas(i).name));
end

% 绘制禁飞区
zones = siteMap.no_fly_zones;
theta = linspace(0, 2*pi, 100);
for i = 1:numel(zones)
    r = zones(i).radius_m + zones(i).buffer_m;
    x = zones(i).center.x + r * cos(theta);
    y = zones(i).center.y + r * sin(theta);
    z = zeros(size(theta));
    plot3(x, y, z, "r--", "LineWidth", 1.5);
    text(zones(i).center.x, zones(i).center.y, 0, string(zones(i).name));
end

view(3);
```

### 原理

可视化的目的不是追求物理级精确，而是让项目逻辑变得可见：

```text
起飞点在哪里
目标点在哪里
禁飞区在哪里
规划路线是否绕开危险区域
动作执行后轨迹是否和预期一致
```

在论文或答辩中，这一部分可以直接展示“自然语言控制不是直接让无人机乱飞，而是经过地图、安全校验和动作序列约束”。

## 十二、步骤 8：输出仿真结论

MATLAB 示例：

```matlab
if isempty(safetyErrors)
    disp("仿真结果：通过。路线未越界，未进入禁飞区。");
else
    disp("仿真结果：失败。发现以下安全问题：");
    disp(unique(safetyErrors));
end
```

### 原理

仿真结论应该给出明确判断：

```text
通过：动作序列可以进入下一步验证
失败：动作序列不能执行，需要修改地图、指令或路径规划
```

该结论对应真实项目中的“真机执行前安全门”。

## 十三、推荐 MATLAB 文件结构

建议在项目根目录新增：

```text
matlab/
├── simulate_swing_actions.m
├── applySwingAction.m
├── checkMapSafety.m
├── plotSwingSimulation.m
└── README.md
```

各文件作用：

```text
simulate_swing_actions.m
主入口。读取地图和动作 JSON，调用仿真函数，输出结果。

applySwingAction.m
动作执行模型。把 takeoff、fly_forward、hover、land 等动作转换为 pose 变化。

checkMapSafety.m
安全验证模型。检查边界、高度、禁飞区。

plotSwingSimulation.m
可视化模型。绘制地图、禁飞区、目标点和飞行轨迹。

README.md
MATLAB 仿真运行说明。
```

## 十四、Simulink 仿真搭建步骤

如果需要从 MATLAB 脚本升级到 Simulink，可以按下面方式搭建。

### 步骤 1：准备输入动作序列

方式一：在 MATLAB 中先读取 JSON，再送入 Simulink。

```matlab
actions = jsondecode(fileread("data/processed/instructions/interactive_last_actions.json"));
siteMap = jsondecode(fileread("data/maps/site_map.json"));
```

方式二：把动作序列转换为 timetable 或 timeseries。

示例字段：

```text
time
vx_cmd
vy_cmd
vz_cmd
yaw_cmd
mode
```

### 原理

Simulink 更适合处理连续时间系统。动作 JSON 是离散命令，所以需要先转换为按时间变化的控制输入。

例如：

```text
fly_forward 3 秒
→ t=0 到 t=3，vx_cmd = 1 m/s

hover 2 秒
→ t=3 到 t=5，vx_cmd = 0，vy_cmd = 0，vz_cmd = 0
```

### 步骤 2：建立无人机运动模型

Simulink 中可使用积分器模型：

```text
vx → Integrator → x
vy → Integrator → y
vz → Integrator → z
```

模型结构：

```text
动作指令
→ 速度命令生成模块
→ 三轴积分器
→ 位置输出 x,y,z
→ 安全检查模块
→ 可视化/报警
```

### 原理

运动学基础公式：

```text
x(t) = x(0) + ∫ vx(t) dt
y(t) = y(0) + ∫ vy(t) dt
z(t) = z(0) + ∫ vz(t) dt
```

这和 MATLAB 脚本中的：

```text
pose = pose + velocity × duration
```

是同一个原理，只是 Simulink 用连续时间积分器表达。

### 步骤 3：建立动作解码模块

可以使用 MATLAB Function Block。

输入：

```text
当前仿真时间 t
动作时间表 actionSchedule
```

输出：

```text
vx_cmd
vy_cmd
vz_cmd
yaw_cmd
airborne
```

动作映射：

```text
takeoff      vz_cmd > 0 或直接置 z=safe_height
land         vz_cmd < 0 或直接置 z=0
fly_forward  vx_cmd > 0
fly_backward vx_cmd < 0
fly_right    vy_cmd > 0
fly_left     vy_cmd < 0
hover        vx_cmd=0, vy_cmd=0, vz_cmd=0
```

### 原理

Simulink 本身不直接理解 JSON 中的字符串动作，因此要把动作先转换为数值命令。

例如：

```text
fly_forward → vx_cmd = +1
fly_left    → vy_cmd = -1
hover       → vx_cmd = 0, vy_cmd = 0, vz_cmd = 0
```

### 步骤 4：建立安全检查模块

可以使用 MATLAB Function Block 编写：

```text
输入：x, y, z, siteMap 参数
输出：safeFlag, errorCode
```

安全规则：

```text
x 是否在 [min_x, max_x]
y 是否在 [min_y, max_y]
z 是否在 [min_z, max_z]
当前位置是否进入禁飞区圆形范围
```

### 原理

安全检查模块相当于本项目 Python 侧 `action_validator` 和 `route_planner` 的仿真监控补充。

Python 侧是在执行前检查动作序列是否合理；Simulink 侧是在执行过程中检查位置状态是否安全。

二者关系：

```text
执行前安全：action_validator
执行中安全：Simulink safety monitor
```

### 步骤 5：建立可视化模块

可选方式：

```text
Scope 显示 x/y/z 曲线
XY Graph 显示平面轨迹
MATLAB Animation 显示三维轨迹
To Workspace 导出仿真数据
```

### 原理

Simulink 的优势是展示动态过程：

```text
动作什么时候开始
什么时候转向
什么时候悬停
什么时候接近禁飞区
什么时候降落
```

这比单纯打印 JSON 更适合演示控制链路。

## 十五、动作 JSON 到 Simulink 输入的转换原理

动作 JSON 是事件序列：

```text
第 1 步：takeoff 5 秒
第 2 步：fly_right 3.1 秒
第 3 步：fly_forward 3 秒
```

Simulink 需要的是时间序列：

```text
t = 0~5      takeoff
t = 5~8.1    fly_right
t = 8.1~11.1 fly_forward
```

转换方法：

```matlab
currentTime = 0;
for i = 1:numel(actions)
    duration = getActionDuration(actions(i));
    startTime(i) = currentTime;
    endTime(i) = currentTime + duration;
    currentTime = endTime(i);
end
```

核心原理：

```text
动作序列是离散逻辑
Simulink 是连续时间仿真
所以要用开始时间和结束时间把动作展开
```

## 十六、完整仿真验证标准

一次仿真建议输出这些结果：

```text
1. 是否成功读取动作 JSON
2. 是否成功读取地图 JSON
3. 动作数量
4. 总飞行时间
5. 起飞点
6. 目标点
7. 最终位置
8. 是否越界
9. 是否进入禁飞区
10. 是否完成降落
11. 结论：通过 / 失败
```

判定为通过的条件：

```text
动作序列格式正确
包含 takeoff 和 land
运动动作发生在起飞之后
降落之后没有继续运动
轨迹没有超过地图边界
轨迹没有进入禁飞区保护范围
最终高度回到起飞点高度
```

## 十七、与当前 Python 安全逻辑的对应关系

| Python 模块 | MATLAB/Simulink 对应功能 |
| --- | --- |
| `instruction_parser.py` | 不在 MATLAB 中实现，仍由 Python 负责 |
| `route_planner.py` | MATLAB 读取其输出结果并复现轨迹 |
| `site_map.py` | MATLAB 读取 `site_map.json` |
| `action_validator.py` | MATLAB 可二次验证动作顺序和参数 |
| `action_planner.py` | MATLAB 可参考其动作说明 |
| `swing_action_executor.py` | MATLAB 仿真执行器替代真机执行 |
| `logging_utils.py` | MATLAB 可额外保存仿真结果 |

## 十八、推荐演示流程

### 方式一：纯地图路线仿真

```bash
cd /home/abc/桌面/SWING_CONTROL
PYTHONPATH=src python -m swing_control.app.map_route "飞到果园上方悬停两秒再降落"
```

复制或保存动作 JSON 后，在 MATLAB 中运行：

```matlab
simulate_swing_actions
```

### 方式二：中文交互生成动作后仿真

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_interactive.sh --no-log
```

输入：

```text
飞到果园上方悬停两秒再降落
```

然后 MATLAB 读取：

```text
data/processed/instructions/interactive_last_actions.json
```

### 方式三：语音生成动作后仿真

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_voice.sh --no-log
```

说话：

```text
飞到果园上方悬停两秒再降落
```

然后 MATLAB 读取：

```text
data/processed/instructions/voice_last_actions.json
```

## 十九、论文/答辩可表述的技术逻辑

可以这样描述：

```text
本项目采用“语言理解 + 结构化动作序列 + 地图安全验证 + MATLAB/Simulink 仿真”的控制链路。

首先，系统将用户的中文自然语言指令解析为统一的动作 JSON。
其次，路径规划模块根据本地场地地图识别目标区域，并生成到目标点的相对运动序列。
然后，安全验证模块检查动作顺序、动作参数、起飞降落逻辑、最大运动时间等约束。
最后，MATLAB/Simulink 读取动作序列和地图文件，对无人机位置进行运动学仿真，验证路径是否越界、是否进入禁飞区，并可视化展示飞行轨迹。
```

该方案的意义：

```text
避免直接依赖真机测试
降低调试风险
使自然语言控制逻辑可视化
方便验证地图安全规则
方便论文展示完整控制链路
```

## 二十、后续可扩展方向

第一阶段：脚本仿真

```text
实现动作读取
实现位置更新
实现边界检查
实现禁飞区检查
实现轨迹绘图
```

第二阶段：Simulink 动态仿真

```text
动作 JSON 转时间序列
速度命令进入积分器
实时输出 x/y/z
安全模块实时报警
Scope/XY Graph 显示轨迹
```

第三阶段：更真实的无人机模型

```text
加入速度响应延迟
加入加速度限制
加入偏航角对前后左右方向的影响
加入随机误差
加入风扰动
加入电量模型
```

第四阶段：仿真到真机迁移

```text
MATLAB 仿真通过
→ Python dry-run 通过
→ 用户人工确认
→ pyparrot 真机执行
→ 日志保存
→ 对比仿真轨迹和真实飞行结果
```

## 二十一、当前阶段建议

目前最适合本项目的路线是：

```text
先完成 MATLAB 脚本仿真
再搭建 Simulink 简化运动学模型
最后再考虑真机地图安全飞行
```

原因：

```text
本项目已有语言解析和地图规划基础
真机没有实时定位闭环
MATLAB/Simulink 更适合展示路径、安全边界和禁飞区逻辑
仿真结果更容易用于论文、项目汇报和答辩
```

因此，MATLAB/Simulink 仿真在本项目中承担的是“真机执行前的虚拟验证平台”作用。
