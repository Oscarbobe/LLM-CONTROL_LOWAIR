# MATLAB/Simulink 操作手册（Windows）

本文档适用于当前项目在 **Windows 10/11 + PowerShell + MATLAB/Simulink** 环境下的仿真验证。文中的命令均以项目根目录为起点，不依赖旧版文档中的 Linux 路径、Shell 脚本或 `make`。

项目处理链路如下：

```text
中文指令 → Python 生成动作 JSON → MATLAB 脚本轨迹仿真
         → Simulink 动态仿真 → 安全结论与结果文件
```

> 仿真流程不会连接或控制真实无人机。Windows 下的真机蓝牙控制不属于本文范围；项目 `model/*.sh` 中的脚本是 Linux 脚本，不应在 PowerShell 中直接运行。

## 1. 项目与环境准备

### 1.1 当前项目目录

本机当前项目根目录为：

```text
C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR
```

路径中包含中文和连字符，PowerShell 与 MATLAB 中都应使用引号。若项目以后被移动，只需将下文的 `$projectRoot` 或 `projectRoot` 改为新位置。

### 1.2 软件要求

- Windows 10 或 Windows 11（64 位）
- Python 3.10 或更高版本
- MATLAB R2019b 或更高版本
- Simulink（仅运行第 4 节时需要）

MATLAB 脚本使用 `jsondecode`、`jsonencode`、`writematrix` 等函数。建议使用较新的 MATLAB 版本，并在 MATLAB 中运行：

```matlab
ver
license('test', 'Simulink')
```

第二条返回 `1` 表示当前许可证可使用 Simulink；返回 `0` 时仍可运行第 3 节的 MATLAB 脚本仿真。

### 1.3 准备 Python 环境（首次运行）

打开 PowerShell，执行：

```powershell
$projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR'
Set-Location -LiteralPath $projectRoot
python --version
```

本机当前 `python` 命令检测到的是 Python 3.9.13，而项目元数据要求 Python 3.10 及以上。建议新建 3.10+ 环境，不要把 3.9 当作正式运行环境；即使部分命令暂时能够执行，也不能保证所有依赖兼容。

若 `python` 不可用，可尝试 Windows Python Launcher：

```powershell
py -3.10 --version
```

本项目提供 Conda 环境文件。已安装 Miniconda/Anaconda 时，推荐：

```powershell
conda env create -f .\environment.yml
conda activate swing-control
python -m pip install -e .
```

若不使用 Conda，可创建虚拟环境：

```powershell
py -3.10 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

只生成地图动作 JSON 时，项目自身代码即可完成主要流程。`requirements.txt` 还包含语音、蓝牙和图像相关依赖，其中 `bluepy` 主要面向 Linux；如果 Windows 安装完整依赖失败，不影响本文的 MATLAB/Simulink 仿真主线。

## 2. 在 PowerShell 中生成动作 JSON

### 2.1 推荐命令

在项目根目录运行：

```powershell
$projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR'
Set-Location -LiteralPath $projectRoot
$env:PYTHONPATH = (Join-Path $projectRoot 'src')
python -m swing_control.app.map_route `
  '飞到果园上方悬停两秒再降落' `
  --save-actions '.\data\processed\instructions\map_last_actions.json'
```

PowerShell 的续行符是反引号 `` ` ``，并且必须是该行最后一个字符。也可以写成单行：

```powershell
python -m swing_control.app.map_route '飞到果园上方悬停两秒再降落' --save-actions '.\data\processed\instructions\map_last_actions.json'
```

若当前使用 `py` 而不是 `python`，将命令开头替换为 `py -3.10 -m`。

成功后应存在：

```text
data\processed\instructions\map_last_actions.json
```

可用 PowerShell 验证：

```powershell
Test-Path -LiteralPath '.\data\processed\instructions\map_last_actions.json'
Get-Content -Raw -Encoding UTF8 '.\data\processed\instructions\map_last_actions.json'
```

当前仓库已经带有示例 `map_last_actions.json`，因此只想验证 MATLAB 时可以直接进入下一节；重新生成文件则用于验证完整链路。

> 不建议在原生 Windows PowerShell 中执行 `make map-demo`。当前 `Makefile` 使用 Unix 风格的 `PYTHONPATH=src` 语法，项目中的 `.sh` 启动脚本也面向 Linux。

## 3. MATLAB 脚本仿真（优先验证）

### 3.1 设置项目路径

启动 MATLAB，在命令窗口执行：

```matlab
projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR';
assert(isfolder(projectRoot), '项目目录不存在，请修改 projectRoot。');
cd(projectRoot);
addpath(fullfile(projectRoot, 'matlab'));
```

使用 `fullfile` 可以自动生成适用于 Windows 的路径，避免手工混用 `/` 和 `\`。

### 3.2 运行仿真

推荐传入相对于项目根目录的动作文件：

```matlab
actionFile = fullfile('data', 'processed', 'instructions', 'map_last_actions.json');
result = simulate_swing_actions(actionFile);
```

也可以使用绝对路径，但当前函数对相对路径的处理最稳定。若直接运行：

```matlab
result = simulate_swing_actions;
```

则默认读取：

```text
data\processed\instructions\interactive_last_actions.json
```

正常情况下，命令窗口会显示动作文件、地图文件、动作序列、最终位姿、总时间及 `PASS` 或 `FAIL`。同时会弹出三维轨迹图：

- 蓝线：仿真轨迹
- 黑点：起飞点
- 绿色标记：任务目标区域
- 红色虚线/阴影：禁飞区及安全缓冲范围

### 3.3 检查导出结果

仿真完成后检查：

```matlab
outputDir = fullfile(projectRoot, 'data', 'simulation');
dir(outputDir)
trajectory = readmatrix(fullfile(outputDir, 'latest_trajectory.csv'));
resultJson = jsondecode(fileread(fullfile(outputDir, 'latest_result.json')));
imshow(fullfile(outputDir, 'latest_figure.png'))
```

预期生成：

| 文件 | 内容 |
|---|---|
| `data\simulation\latest_trajectory.csv` | `time, x, y, z, heading` 时间序列 |
| `data\simulation\latest_result.json` | 安全结论、错误、最终位姿等 |
| `data\simulation\latest_figure.png` | 三维轨迹图 |

脚本返回值 `result` 中常用字段包括：

```matlab
result.ok
result.finalPose
result.finalHeadingDeg
result.safetyErrors
result.trajectory
```

`result.ok == true` 表示轨迹没有越界或进入禁飞区，动作结束时也已经降落。

### 3.4 MATLAB 文件职责

| 文件 | 作用 |
|---|---|
| `matlab\simulate_swing_actions.m` | 读取 JSON、执行仿真、汇总结果 |
| `matlab\applySwingAction.m` | 将动作转换为位姿变化 |
| `matlab\checkMapSafety.m` | 检查边界与禁飞区 |
| `matlab\plotSwingSimulation.m` | 绘制三维地图和轨迹 |
| `matlab\actionsToTimeline.m` | 将动作序列转换为时间序列 |
| `matlab\applyWindDisturbance.m` | 模拟风扰动 |
| `matlab\exportSimulationResult.m` | 导出 CSV、JSON 和 PNG |

## 4. Simulink 动态仿真

先确认第 3 节能够运行，再执行本节。仓库当前已经包含 `simulink\swing_language_control_sim.slx`；`build_swing_simulink_model.m` 用于在模型缺失、损坏或需要重新生成时重建 `.slx`。

### 4.1 加入脚本路径并生成输入变量

在同一个 MATLAB 会话中执行：

```matlab
projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR';
cd(projectRoot);
addpath(fullfile(projectRoot, 'simulink'));

actionFile = fullfile('data', 'processed', 'instructions', 'map_last_actions.json');
actionsToVelocityCmd(actionFile);
whos velCmd siteMap simDuration
```

`actionsToVelocityCmd` 会在 MATLAB 基础工作区创建：

- `velCmd`：`[time, vx, vy, vz]` 速度命令
- `siteMap`：地图结构体
- `simDuration`：仿真停止时间

必须先创建这三个变量，因为构建出的模型会引用它们。

### 4.2 打开或重建模型

优先打开仓库中已有模型：

```matlab
modelName = 'swing_language_control_sim';
open_system(fullfile(projectRoot, 'simulink', 'swing_language_control_sim.slx'));
```

如果模型文件不存在，或需要根据脚本重新生成模型，再运行：

```matlab
cd(fullfile(projectRoot, 'simulink'));
build_swing_simulink_model;
```

预期生成：

```text
simulink\swing_language_control_sim.slx
```

再次运行构建脚本会关闭未保存的同名已加载模型，并重新生成它，因此若手工修改过模型，请先另存或提交修改。

### 4.3 打开并运行模型

```matlab
modelName = 'swing_language_control_sim';
simOut = sim(modelName);
```

模型的数据流为：

```text
velCmd → Demux(vx, vy, vz) → 三轴 Integrator → x/y/z
                                      ├→ Scope XYZ / XY Graph
                                      └→ Safety Check → safeFlag
```

运行后检查：

- `Scope XYZ`：位置随时间变化
- `XY Graph`：x-y 平面轨迹
- `Display safeFlag`：安全时为 `1`
- 轨迹不安全时，`NOT → Stop if Unsafe` 会停止仿真

模型由构建脚本自动保存；如手工调整后需要再次保存，可运行：

```matlab
save_system(modelName);
```

关闭模型：

```matlab
close_system(modelName, 0);
```

## 5. 一次性完整操作清单

1. 在 PowerShell 中进入项目根目录。
2. 设置 `$env:PYTHONPATH`，运行 `swing_control.app.map_route` 生成动作 JSON。
3. 在 MATLAB 中设置 `projectRoot`，并把 `matlab` 目录加入路径。
4. 运行 `simulate_swing_actions(actionFile)`。
5. 确认命令窗口结论、三维轨迹图以及 `data\simulation` 下的三个导出文件。
6. 把 `simulink` 目录加入 MATLAB 路径。
7. 先运行 `actionsToVelocityCmd(actionFile)`，确认工作区变量齐全。
8. 打开已有 `swing_language_control_sim.slx`；如果缺失或需要重建，再运行 `build_swing_simulink_model`。
9. 打开并运行模型，查看 Scope、XY Graph 与 `safeFlag`。

## 6. 验收标准

### MATLAB 脚本仿真

- 能读取 `map_last_actions.json` 与 `site_map.json`
- 能打印动作序列和最终位姿
- 能显示三维轨迹图
- 能给出 `PASS` 或 `FAIL`
- 能生成 CSV、JSON、PNG 三个结果文件

### Simulink 动态仿真

- `simulink\swing_language_control_sim.slx` 已存在，必要时可重建
- 工作区存在 `velCmd`、`siteMap`、`simDuration`
- 模型能正常更新并运行
- Scope 和 XY Graph 中有轨迹
- 正常路线的 `safeFlag` 保持为 `1`

## 7. Windows 常见问题

### 7.1 PowerShell 提示无法运行 Activate.ps1

只为当前 PowerShell 进程临时放开策略：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

无需修改系统级执行策略。

### 7.2 Python 提示 `No module named swing_control`

确认当前目录是项目根目录，然后执行以下任一方案：

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
```

或在已激活的虚拟环境中安装项目：

```powershell
python -m pip install -e .
```

### 7.3 PowerShell 中文显示乱码

Windows Terminal/新版 PowerShell 通常可直接显示 UTF-8。旧控制台可尝试：

```powershell
chcp 65001
```

本机现有 Python 3.9 安装的某些 `.pth` 文件不是 UTF-8 编码，强制设置 `PYTHONUTF8=1` 可能导致 Python 在启动阶段报 `UnicodeDecodeError`，因此本文不设置该变量。优先使用 Python 3.10+ 的独立 Conda 或虚拟环境。

### 7.4 MATLAB 找不到函数

不要依赖“当前文件夹”面板的偶然状态，显式加入路径：

```matlab
addpath(fullfile(projectRoot, 'matlab'));
addpath(fullfile(projectRoot, 'simulink'));
which simulate_swing_actions
which actionsToVelocityCmd
```

### 7.5 MATLAB 找不到动作或地图 JSON

检查：

```matlab
isfile(fullfile(projectRoot, 'data', 'processed', 'instructions', 'map_last_actions.json'))
isfile(fullfile(projectRoot, 'data', 'maps', 'site_map.json'))
```

两项都应返回逻辑值 `1`。相对动作路径应从项目根目录开始写成 `data\...`，不要在本手册的调用方式中写成 `..\data\...`。

### 7.6 Simulink 提示 `velCmd`、`siteMap` 或 `simDuration` 未定义

在运行模型前重新执行：

```matlab
actionsToVelocityCmd(fullfile('data', 'processed', 'instructions', 'map_last_actions.json'));
```

然后用 `whos velCmd siteMap simDuration` 确认变量位于基础工作区。

### 7.7 无法创建或更新 `.slx` 文件

检查 `simulink` 目录是否可写、文件是否被另一个 MATLAB 会话占用，并确认当前目录：

```matlab
cd(fullfile(projectRoot, 'simulink'));
fileattrib(pwd)
```

### 7.8 仿真结果为 FAIL

查看 `result.safetyErrors`，常见原因包括越过地图边界、进入禁飞区、最终仍处于空中或没有回到地面高度：

```matlab
disp(result.safetyErrors)
disp(result.finalPose)
disp(result.airborne)
```

这类结果代表安全检查发现问题，不一定是 MATLAB 运行故障。

## 8. 建议保留的成果

```text
data\processed\instructions\map_last_actions.json
data\simulation\latest_trajectory.csv
data\simulation\latest_result.json
data\simulation\latest_figure.png
simulink\swing_language_control_sim.slx
```

这些文件依次证明：中文指令已转换为动作序列、动作已形成可分析轨迹、安全检查已有结论、轨迹已经可视化，以及 Simulink 动态模型已经成功生成。
