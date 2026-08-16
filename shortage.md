# 项目 Markdown 完整性检查与当前短板

检查时间：2026-08-16

## 1. 检查结论

当前项目实际目录为：

```text
/home/abc/桌面/LLM-CONTROL_LOWAIR
```

本轮环境上下文中的 `/home/abc/桌面/SWING_CONTROL` 已不存在，后续运行和文档引用应继续使用 `LLM-CONTROL_LOWAIR`。

本轮已检查：

- Markdown 文件数量：44 个。
- 本地 Markdown 链接：未发现断链。
- 旧测试状态：未发现 `71 passed` 残留。
- 旧项目运行路径：未发现 `/home/abc/桌面/SWING_CONTROL` 残留。
- Ubuntu 环境检查：通过。
- 自动化测试：`72 passed`。

## 2. 文档完整性现状

项目文档已经覆盖以下大类：

- `README.md`：项目目标、主链路、快速运行方式、目录结构。
- `TECHNICAL_DOCUMENTATION.md`：完整技术逻辑、函数、模块和运行链路。
- `OPENCODE_PROJECT_STATUS_GUIDE.md`：给 OpenCode 的交接说明。
- `SAFETY.md`：真机和交付安全说明。
- `MATLAB_SIMULINK_OPERATION_MANUAL.md`：Windows MATLAB/Simulink 操作手册。
- `matlab/README.md`、`simulink/README.md`：仿真侧说明。
- `docs/`：动作校验、dry-run、日志、语音、地图、蓝牙、LLM、环境等专题文档。
- `model/SWING_CONTROL_GUIDE.md`：Parrot Swing 真机脚本运行说明。
- `examples/`：演示命令和语音样例口令。

整体判断：文档主链路完整，能支撑 Ubuntu 侧交付验证、后续 OpenCode 接手、Windows MATLAB/Simulink 操作和真机可选验证。

## 3. 当前短板

### 3.1 MATLAB/Simulink 实测仍是最大短板

项目已经包含 MATLAB 脚本、Simulink `.slx`、Windows 操作手册和已有仿真导出结果，但 Ubuntu 环境不能直接验证 MATLAB GUI 和 Simulink 动态模型。

还需要补齐：

- Windows MATLAB 中实际运行 `simulate_swing_actions(...)` 的截图或记录。
- Windows Simulink 中打开并运行 `swing_language_control_sim.slx` 的截图或记录。
- 仿真失败时的错误截图、版本号和修复记录。
- 一份最终展示用的 MATLAB/Simulink 验收记录。

目标要求：

- 能证明 `.m` 脚本和 `.slx` 模型不是只存在于文件中，而是在 Windows MATLAB/Simulink 中真实跑通过。
- 输出至少包含轨迹图、PASS/FAIL 结果、动作输入 JSON 和最终位置。

### 3.2 真实地图/GIS 能力仍是示范地图

当前 `data/maps/site_map.json` 是本地米制坐标示范地图，适合课堂展示和仿真验证，但还不是真实农业场景地图。

还需要补齐：

- 真实地块坐标来源，例如 GPS、RTK、人工测绘或地图平台导出。
- 经纬度到本地坐标系的转换说明。
- 地块边界、障碍物、禁飞区的采集流程。
- 地图版本管理和现场更新方式。

目标要求：

- 能把“果园、玉米地、水渠、房屋、电线杆”等示范区域替换为真实场景数据。
- 文档中说明真实地图如何采集、如何转换、如何放入 `data/maps/`。

### 3.3 真机验证仍依赖现场蓝牙和安全环境

真机 pyparrot 执行链路、蓝牙恢复脚本和人工确认已经具备，但真机运行结果仍依赖现场硬件状态。

还需要补齐：

- 固定一台演示电脑和一架 Swing 的蓝牙地址记录。
- 真机飞行前检查表。
- 真机执行日志样例。
- 蓝牙失败时的替代方案，例如 USB 蓝牙适配器。
- 演示现场安全边界说明。

目标要求：

- 真机不是主验收链路，但如果展示时连接真机，应能快速定位蓝牙、电量、权限和地址问题。
- 任何真机执行都必须先 dry-run，再人工输入 `确认执行`。

### 3.4 LLM 指令解析仍需要效果评测

当前 Ollama 模型为 `qwen3.5:4b`，并且项目有规则兜底解析。基础演示可用，但模型输出有时会返回无法理解，因此还缺少系统化评测。

还需要补齐：

- 中文指令测试集，例如 50 到 100 条常见口令。
- 每条指令的期望动作 JSON。
- 模型解析成功率、规则兜底比例、错误类型统计。
- 对危险指令、超范围指令、模糊指令的拒绝测试。

目标要求：

- 不只证明“某一句能跑”，还要证明“常见语音/文本指令稳定可控”。
- 评测结果应写入 `docs/` 或单独报告。

### 3.5 语音控制还缺少噪声和设备兼容测试

语音链路已经具备 `arecord/ffmpeg -> whisper -> 文本控制链路`，但还缺少在真实环境中的鲁棒性数据。

还需要补齐：

- 不同麦克风设备的录音测试。
- 安静环境、普通说话、背景噪声下的识别效果记录。
- Whisper 首次加载时间、单轮识别耗时。
- 识别失败时的用户提示和重试策略说明。

目标要求：

- 展示时能说明语音控制的适用条件和失败处理方式。
- 语音识别不稳定时，可退回文本输入演示。

### 3.6 交付包装已补齐基础入口，但还不是完整商业产品

Ubuntu 侧已经具备基础交付入口：

- `.python-version`：推荐 Python 3.11。
- `environment-delivery.yml`：Ubuntu 交付 Conda 环境。
- `docs/DELIVERY_INSTALL_ACCEPTANCE.md`：一键安装后的最终验收说明。
- `scripts/package_release.sh`：发布压缩包生成脚本。
- `run_demo.sh`：演示用入口脚本。
- `run_demo_menu.sh`：交互式 Shell 菜单，降低演示人员命令行操作成本。
- `demo_streamlit.py`：浏览器功能展示面板。
- `make demo`、`make menu`、`make streamlit`、`make package`：Makefile 统一入口。

但它仍不是完整商业产品形态。

还需要补齐：

- 用户手册和开发者手册分离。
- 更正式的产品级 Web 前端或桌面应用。
- 正式版本号、发布说明和验收签字模板。
- 新机器从零安装的外部复测记录。

目标要求：

- 新机器上能按文档从零安装、检查、运行、生成报告。
- 演示人员不用理解全部源码，也能按固定命令完成展示。

### 3.7 文档数量较多，后续维护容易重复

当前 Markdown 文件已经覆盖全面，但有多处文档重复描述环境、测试状态、运行路径和项目状态。

还需要补齐：

- 明确主文档入口：`README.md`、`TECHNICAL_DOCUMENTATION.md`、`OPENCODE_PROJECT_STATUS_GUIDE.md`。
- 明确专题文档只写细节，不重复写全局状态。
- 每次更新测试数量、模型名、路径时，同步检查全仓 Markdown。
- 可考虑增加一个文档检查脚本，自动扫描旧路径、旧测试数量和断链。

目标要求：

- 减少“一个地方更新，另一个地方过期”的风险。
- OpenCode 或后续维护者能快速判断哪个文档是权威入口。

## 4. 建议优先级

1. 先完成 Windows MATLAB/Simulink 实测记录。
2. 再补 LLM 指令解析评测集和语音噪声测试。
3. 然后完善真实地图/GIS 数据接入说明。
4. 最后做正式交付包装，例如发布包、演示入口和用户手册。

## 5. 当前可直接运行的验收命令

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
make check-env
PYTHONPATH=src python -m pytest -q
make delivery-check
make report
```

当前验证结果：

```text
Ubuntu 环境检查：通过
自动化测试：72 passed
本地 Markdown 链接：0 个断链
```
