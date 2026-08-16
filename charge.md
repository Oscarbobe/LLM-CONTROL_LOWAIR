# OpenCode 后续任务书：Windows Streamlit 中展示 MATLAB 仿真演示

本文档用于交给 OpenCode，在 Windows 系统中继续完善 Streamlit 展示面板，使其能够展示 MATLAB/Simulink 仿真结果。实现方式可以是跳转链接、嵌入图片窗口，或在 Streamlit 页面中直接展示仿真输出。

## 1. 当前项目状态

项目根目录：

```text
LLM-CONTROL_LOWAIR
```

当前已经具备：

- `demo_streamlit.py`：Streamlit 功能展示面板。
- `data\processed\instructions\map_last_actions.json`：地图规划动作 JSON。
- `matlab\simulate_swing_actions.m`：MATLAB 脚本仿真入口。
- `simulink\swing_language_control_sim.slx`：Simulink 模型。
- `data\simulation\latest_figure.png`：MATLAB 仿真轨迹图输出。
- `data\simulation\latest_result.json`：MATLAB 仿真结果 JSON。
- `data\simulation\latest_trajectory.csv`：MATLAB 仿真轨迹数据。

当前 Streamlit 面板已有页面：

- 总览
- 文本控制
- 地图规划
- 交付报告
- 环境检查

## 2. 本次任务目标

在 `demo_streamlit.py` 中新增或完善一个页面：

```text
MATLAB 仿真演示
```

该页面用于在 Windows 展示 MATLAB/Simulink 仿真结果。

最低目标：

- Streamlit 中能显示 `data\simulation\latest_figure.png`。
- Streamlit 中能读取并展示 `data\simulation\latest_result.json`。
- Streamlit 中能读取并展示 `data\simulation\latest_trajectory.csv`。
- 页面提供打开 MATLAB 操作手册的入口。

进阶目标：

- 页面提供一键生成动作 JSON 的按钮。
- 页面提供调用 MATLAB 脚本的按钮。
- 页面提供打开 Simulink `.slx` 模型的按钮或路径提示。

## 3. 推荐实现方式

### 3.1 优先实现：展示已有 MATLAB 输出

优先不要直接从 Streamlit 调 MATLAB，而是先展示已经导出的结果文件。

需要读取：

```text
data\simulation\latest_figure.png
data\simulation\latest_result.json
data\simulation\latest_trajectory.csv
```

页面展示内容：

- 仿真轨迹图：`st.image(...)`
- 仿真结论：PASS/FAIL
- 最终位姿：`finalPose`
- 总飞行时间：`totalTime`
- 错误信息：`safetyErrors`
- 轨迹数据表格：`st.dataframe(...)`
- 轨迹曲线：`st.line_chart(...)`

如果文件不存在，页面要提示：

```text
还没有 MATLAB 仿真输出，请先在 MATLAB 中运行 simulate_swing_actions。
```

### 3.2 可选实现：提供跳转或打开文件路径

Streamlit 可以展示路径和命令，让用户手动打开 MATLAB：

```matlab
projectRoot = 'C:\...\LLM-CONTROL_LOWAIR';
cd(projectRoot);
addpath(fullfile(projectRoot, 'matlab'));
actionFile = fullfile('data', 'processed', 'instructions', 'map_last_actions.json');
result = simulate_swing_actions(actionFile);
```

还可以展示 Simulink 打开命令：

```matlab
open_system(fullfile(projectRoot, 'simulink', 'swing_language_control_sim.slx'));
```

### 3.3 谨慎实现：从 Streamlit 直接调用 MATLAB

如果 Windows 已配置 `matlab` 命令到 PATH，可以在 Streamlit 中用 `subprocess.run(...)` 调用 MATLAB。

建议命令形式：

```powershell
matlab -batch "projectRoot='C:\...\LLM-CONTROL_LOWAIR'; cd(projectRoot); addpath(fullfile(projectRoot,'matlab')); simulate_swing_actions(fullfile('data','processed','instructions','map_last_actions.json'));"
```

注意：

- 该功能可能耗时较长，必须用 `st.spinner(...)`。
- 若 MATLAB 未加入 PATH，不应报崩溃，应给出手动运行说明。
- 不要在 Linux/Ubuntu 上默认调用 MATLAB。
- 不要让 Streamlit 自动控制真实无人机。

## 4. 建议代码结构

在 `demo_streamlit.py` 中新增常量：

```python
SIM_FIGURE = ROOT_DIR / "data" / "simulation" / "latest_figure.png"
SIM_RESULT = ROOT_DIR / "data" / "simulation" / "latest_result.json"
SIM_TRAJECTORY = ROOT_DIR / "data" / "simulation" / "latest_trajectory.csv"
MATLAB_MANUAL = ROOT_DIR / "MATLAB_SIMULINK_OPERATION_MANUAL.md"
SIMULINK_MODEL = ROOT_DIR / "simulink" / "swing_language_control_sim.slx"
```

新增函数：

```python
def _matlab_tab() -> None:
    ...
```

并将主页面 tabs 改为：

```python
tabs = st.tabs(["总览", "文本控制", "地图规划", "MATLAB 仿真", "交付报告", "环境检查"])
```

## 5. 页面功能要求

`MATLAB 仿真` 页面至少包含：

1. 文件状态检查

显示以下文件是否存在：

- `latest_figure.png`
- `latest_result.json`
- `latest_trajectory.csv`
- `swing_language_control_sim.slx`

2. 仿真图展示

```python
if SIM_FIGURE.exists():
    st.image(str(SIM_FIGURE), caption="MATLAB 仿真轨迹图")
```

3. 仿真结果展示

读取 JSON：

```python
result = json.loads(SIM_RESULT.read_text(encoding="utf-8"))
```

展示：

- `ok`
- `finalPose`
- `totalTime`
- `safetyErrors`

4. 轨迹数据展示

```python
df = pd.read_csv(SIM_TRAJECTORY)
st.dataframe(df, width="stretch")
st.line_chart(df, x="time", y=["x", "y", "z"])
```

如果 CSV 字段名不同，要做兼容处理。

5. MATLAB 操作命令展示

用 `st.code(..., language="matlab")` 显示可复制的 MATLAB 命令。

6. Simulink 模型入口

显示模型路径：

```text
simulink\swing_language_control_sim.slx
```

并给出 MATLAB 打开命令：

```matlab
open_system(fullfile(projectRoot, 'simulink', 'swing_language_control_sim.slx'));
```

## 6. 验收标准

完成后在 Windows 上验证：

```powershell
streamlit run demo_streamlit.py
```

浏览器打开：

```text
http://localhost:8501
```

验收通过条件：

- 页面中出现 `MATLAB 仿真` 标签页。
- 如果 `latest_figure.png` 存在，页面能显示轨迹图。
- 如果 `latest_result.json` 存在，页面能显示 PASS/FAIL、最终位姿、总时间。
- 如果 `latest_trajectory.csv` 存在，页面能显示轨迹表格和 x/y/z 曲线。
- 如果文件不存在，页面给出清晰提示，而不是报错。
- 页面能展示 MATLAB 脚本仿真命令和 Simulink 打开命令。
- 不影响原有“文本控制”“地图规划”“交付报告”“环境检查”页面。

## 7. 禁止事项

- 不要在 Streamlit 页面中直接执行真机飞行。
- 不要绕过 `action_validator`。
- 不要把 Windows 上的 `bluepy` 安装失败当作展示失败。
- 不要删除 Ubuntu 真机脚本。
- 不要改动 MATLAB/Simulink 模型文件，除非确实需要修复仿真展示。

## 8. 推荐提交说明

```text
feat: add MATLAB simulation view to Streamlit demo

- add MATLAB simulation tab to demo_streamlit.py
- show latest MATLAB figure/result/trajectory outputs
- provide MATLAB and Simulink commands for Windows demo
- handle missing simulation files gracefully
```
