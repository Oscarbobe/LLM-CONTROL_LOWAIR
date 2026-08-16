# 晚间展示运行说明：Windows + Streamlit + MATLAB/Simulink

本文档用于晚间项目展示，目标是在 Windows 系统上演示 Streamlit 功能面板，并配合 MATLAB/Simulink 展示仿真结果。

## 1. 展示目标

展示链路：

```text
中文指令
  -> Streamlit 功能面板
  -> 动作 JSON
  -> 地图路径规划
  -> 安全校验与 dry-run
  -> MATLAB/Simulink 仿真结果展示
```

说明：

- Windows 侧主要用于功能展示和 MATLAB/Simulink 仿真。
- 真机蓝牙控制建议仍放在 Ubuntu 系统中验证。
- Windows 上不强制安装 `bluepy`，因为它主要面向 Linux 蓝牙。

## 2. 推荐 Windows 环境

推荐软件：

- Windows 10/11 64 位
- Python 3.10 或 Python 3.11
- MATLAB R2019b 或更高版本
- Simulink
- Ollama，可选，用于本地大语言模型解析

推荐 Python：

```text
Python 3.11
```

如果 Windows 当前没有 Python 3.10+，请先安装 Python 3.11，并勾选 “Add Python to PATH”。

## 3. 打开项目目录

PowerShell 中执行：

```powershell
$projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR'
Set-Location -LiteralPath $projectRoot
```

如果项目位置不同，只需要修改 `$projectRoot`。

## 4. 创建 Python 虚拟环境

推荐使用虚拟环境：

```powershell
py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

如果没有 `py -3.11`，可尝试：

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 5. 安装 Streamlit 展示依赖

Windows 展示主线不需要安装 Linux 蓝牙依赖 `bluepy`。建议先安装展示所需依赖：

```powershell
python -m pip install streamlit pandas numpy PyYAML networkx scipy ollama openai-whisper pytest
```

如果只展示地图规划、动作 JSON 和报告，不使用语音，可暂时不安装 `openai-whisper`：

```powershell
python -m pip install streamlit pandas numpy PyYAML networkx scipy ollama pytest
```

## 6. 启动 Streamlit 功能展示面板

在项目根目录执行：

```powershell
$env:PYTHONPATH = (Join-Path $projectRoot 'src')
streamlit run demo_streamlit.py
```

浏览器打开：

```text
http://localhost:8501
```

如果 8501 端口被占用：

```powershell
streamlit run demo_streamlit.py --server.port 8502
```

然后打开：

```text
http://localhost:8502
```

## 7. Streamlit 展示顺序

建议按以下顺序讲解：

1. 打开“总览”页面，说明项目链路。
2. 打开“文本控制”页面，输入：

```text
起飞后悬停2秒再降落
```

查看动作 JSON、安全校验和 dry-run 序列。

3. 打开“地图规划”页面，输入：

```text
飞到果园上方悬停两秒再降落
```

查看目标区域、航点、A* 绕行、禁飞区和动作 JSON。

4. 打开“交付报告”页面，生成并查看 Markdown 报告。
5. 打开“环境检查”页面，说明 Windows 展示环境和 Ubuntu 真机环境的分工。

## 8. 生成 MATLAB 输入动作 JSON

在 PowerShell 中执行：

```powershell
$env:PYTHONPATH = (Join-Path $projectRoot 'src')
python -m swing_control.app.map_route `
  '飞到果园上方悬停两秒再降落' `
  --save-actions '.\data\processed\instructions\map_last_actions.json'
```

成功后应生成：

```text
data\processed\instructions\map_last_actions.json
```

## 9. MATLAB 脚本仿真

打开 MATLAB，执行：

```matlab
projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR';
cd(projectRoot);
addpath(fullfile(projectRoot, 'matlab'));

actionFile = fullfile('data', 'processed', 'instructions', 'map_last_actions.json');
result = simulate_swing_actions(actionFile);
```

预期结果：

- MATLAB 弹出三维轨迹图。
- 命令窗口显示最终位姿和 PASS/FAIL。
- `data\simulation\latest_trajectory.csv` 被生成。
- `data\simulation\latest_result.json` 被生成。
- `data\simulation\latest_figure.png` 被生成。

## 10. Simulink 演示

在 MATLAB 中执行：

```matlab
projectRoot = 'C:\Users\Lenovo\Desktop\新建文件夹\飞行控制\LOW-AIR\LLM-CONTROL_LOWAIR';
cd(projectRoot);
addpath(fullfile(projectRoot, 'simulink'));

open_system(fullfile(projectRoot, 'simulink', 'swing_language_control_sim.slx'));
```

如果需要重新生成模型：

```matlab
build_swing_simulink_model
```

展示重点：

- 动作 JSON 已由 Streamlit/Python 生成。
- MATLAB 脚本能把动作转换为轨迹。
- Simulink 模型用于动态仿真展示。

## 11. 展示时的兜底方案

如果 Streamlit 无法启动：

```powershell
$env:PYTHONPATH = (Join-Path $projectRoot 'src')
python -m swing_control.app.map_route '飞到果园上方悬停两秒再降落' --save-actions '.\data\processed\instructions\map_last_actions.json'
```

如果 Ollama 不稳定：

- 项目会使用规则兜底解析常见指令。
- 可直接使用地图规划页面或 `map_route` 命令。

如果 MATLAB/Simulink 来不及实测：

- 使用 `data\simulation\latest_figure.png` 作为已有仿真结果截图展示。
- 使用 `MATLAB_SIMULINK_OPERATION_MANUAL.md` 说明完整 Windows 操作步骤。

## 12. 展示结论话术

可以这样总结：

```text
本项目已经实现自然语言到无人机动作 JSON 的转换，
并通过地图规划、安全校验和 dry-run 防止危险动作直接下发。
Windows 侧用于 Streamlit 可视化展示和 MATLAB/Simulink 仿真验证，
Ubuntu 侧保留真机蓝牙控制和语音控制能力。
```
