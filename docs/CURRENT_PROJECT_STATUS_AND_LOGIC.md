# 当前项目缺口与完整项目逻辑

## 1. 当前已经完成的部分

### 1.1 自动化飞控脚本

位置：

```text
model/
├── run_swing_direct_flight.sh
├── run_swing_actions.sh
├── run_swing_instruction.sh
├── run_swing_interactive.sh
├── swing_bluetooth_common.sh
├── demoSwingDirectFlight.py
└── fix_mt7925_bluetooth.sh
```

能力：

- 修复或启用蓝牙
- 参照 LowAir-GS 的 MT7925/pyparrot 方式恢复真机蓝牙控制器
- 扫描 Parrot Swing
- 连接测试
- 执行基础飞行动作
- 执行语义规划动作 JSON
- 从中文指令进入真机操作：蓝牙准备、自动扫描、连接测试、动作预览、人工确认、pyparrot 执行
- 连续中文交互控制：反复输入中文指令、动作预览、人工确认、可选真机执行
- 麦克风语音控制：录音、Whisper 转文字、动作预览、人工确认、可选真机执行

### 1.2 自然语言解析入口

位置：

```text
src/swing_control/nlp/instruction_parser.py
src/swing_control/app/parse_instruction.py
src/swing_control/app/run_instruction.py
src/swing_control/app/interactive_control.py
src/swing_control/app/voice_control.py
src/swing_control/asr/microphone.py
src/swing_control/asr/transcriber.py
```

能力：

- 调用 Ollama
- 将中文指令解析为 Swing 动作 JSON
- 支持 dry-run 校验和动作预览
- 支持连续交互式输入中文指令
- 支持麦克风语音输入转中文文本后进入同一控制链路

当前限制：

- Ollama 已安装，且本机已有 `qwen3.5:4b`。

### 1.3 动作安全校验

位置：

```text
src/swing_control/safety/action_validator.py
```

能力：

- 工具白名单校验
- 参数类型校验
- 参数范围校验
- 动作顺序校验
- 起飞/运动/模式切换人工确认标记

### 1.4 dry-run 动作预演

位置：

```text
src/swing_control/planning/action_planner.py
src/swing_control/app/dry_run_actions.py
```

能力：

- 不连接无人机
- 输出每一步动作说明
- 输出对应 `pyparrot` 调用预览

### 1.4.1 地图目标规划

位置：

```text
data/maps/site_map.json
src/swing_control/mapping/site_map.py
src/swing_control/planning/route_planner.py
src/swing_control/app/map_route.py
```

能力：

- 加载本地演示地图
- 匹配果园、玉米地、水渠等命名区域和别名
- 检查地图边界
- 检查房屋、电线杆等圆形禁飞区
- 将目标区域转换为 Swing 相对动作序列
- 在路径接近禁飞区时加入简化绕行航点
- 自动接入中文/语音交互解析兜底

### 1.5 用户确认

位置：

```text
src/swing_control/safety/manual_confirmation.py
```

能力：

- 执行真机动作前要求输入固定短语：

```text
确认执行
```

- 输入其他内容或 `q` 会取消执行。

### 1.6 pyparrot 真机执行器

位置：

```text
src/swing_control/flight/swing_action_executor.py
src/swing_control/app/execute_actions.py
```

能力：

- 连接 Parrot Swing
- 执行动作 JSON
- 映射到 `pyparrot` 方法
- 异常时尝试 `safe_land(5)`
- 最后断开连接

### 1.7 日志记录

位置：

```text
src/swing_control/logging_utils.py
data/logs/
```

能力：

- 保存 `.jsonl` 日志
- 记录动作加载、校验、规划、确认、执行、异常、结束状态

## 2. 当前还缺少的部分

### 2.1 推荐中文模型未下载

当前本机已有：

```text
qwen3.5:4b
```

项目已将它设为默认模型。若后续想使用更偏中文指令的推荐模型，可执行：


```bash
ollama pull qwen2.5:3b
```

下载后测试：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" \
  --model qwen3.5:4b \
  --dry-run
```

### 2.2 Python 大模型/数据处理依赖未完全安装

当前 base 环境缺少：

```text
PyYAML
ollama
torch
transformers
whisper
speech_recognition
jieba
pandas
scipy
networkx
```

说明：当前 Ollama 调用不强依赖 Python `ollama` 包，但后续扩展会用到这些依赖。

建议使用：

```bash
conda activate swing-control-llm
python -m pip install jieba pydantic rich SpeechRecognition transformers accelerate sentencepiece openai-whisper ollama pandas scipy networkx PyYAML
```

### 2.3 语音识别模块未实现

当前只有目录：

```text
src/swing_control/asr/
```

还缺：

```text
麦克风录音
音频文件转文字
Whisper 或其他 ASR 模型调用
语音识别结果接入 instruction_parser
```

### 2.4 地图与区域匹配已实现最小版本

当前已有：

```text
data/maps/site_map.json
src/swing_control/mapping/site_map.py
data/maps/
```

已支持：

```text
果园、玉米地、水渠等语义区域数据
目标区域名称到局部坐标的匹配
房屋、电线杆等简化禁飞区数据
```

### 2.5 真实路径规划已实现简化版本

当前已加入：

```text
src/swing_control/planning/route_planner.py
```

它可以把地图目标转换为 Swing 相对动作序列，并在路径接近禁飞区时加入绕行航点。

仍然不是真正 GPS/GIS 闭环路径规划。

还缺：

```text
真实 GPS/GIS 坐标
实时定位反馈
复杂障碍物避让
返航路径
任务边界约束
```

### 2.6 测试集和评估脚本未实现

当前还没有完整测试集。

还缺：

```text
L1/L2/L3/EDGE 指令测试集
JSON 格式正确率统计
工具选择准确率统计
参数合法率统计
安全拦截成功率统计
响应时间统计
```

### 2.7 真机飞行未现场验证

代码已具备执行入口，但还缺现场验证：

```text
蓝牙控制器可用性
Swing 是否能稳定连接
动作 JSON 是否能完整执行
异常降落是否可用
日志是否完整记录真实飞行
```

## 3. 完整项目逻辑

完整项目应分为三条链路：文本链路、语音链路、真机执行链路。

## 4. 文本控制链路

```text
用户输入中文指令
  -> parse_instruction.py
  -> Ollama / qwen3.5:4b
  -> instruction_parser 输出动作 JSON
  -> action_validator 校验动作
  -> action_planner 输出 dry-run 预览
  -> data/logs 保存解析和校验日志
```

示例命令：

```bash
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.parse_instruction \
  "起飞后悬停2秒再降落" \
  --model qwen3.5:4b \
  --dry-run
```

## 5. 语音控制链路

```text
用户语音
  -> asr 模块录音或读取音频
  -> Whisper 转文字
  -> instruction_parser 解析文字
  -> action_validator 校验
  -> action_planner dry-run
  -> 用户确认
  -> swing_action_executor 真机执行
  -> data/logs 保存完整日志
```

当前状态：语音链路还没实现。

## 6. 真机执行链路

```text
动作 JSON 文件
  -> run_swing_actions.sh
  -> fix_mt7925_bluetooth.sh 准备蓝牙
  -> execute_actions.py
  -> action_validator 校验
  -> action_planner 预览
  -> manual_confirmation 输入“确认执行”
  -> SwingActionExecutor 连接 Parrot Swing
  -> pyparrot 执行动作
  -> 异常时 safe_land(5)
  -> disconnect
  -> data/logs 保存日志
```

示例命令：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
./model/run_swing_actions.sh --addr E0:14:89:09:3D:CB
```

## 7. 当前最小可演示闭环

当前本机已有 `qwen3.5:4b`，可以直接演示：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落"
```

这会执行：

```text
中文指令
  -> Ollama 生成动作 JSON
  -> 校验
  -> dry-run 预览
  -> 日志保存
```

需要真机时：

```text
动作 JSON
  -> 蓝牙准备
  -> 用户确认
  -> pyparrot 执行
  -> 日志保存
```

## 8. 推荐下一步开发顺序

1. 使用本机 `qwen3.5:4b` 跑通中文指令解析；如效果不稳，再下载 `qwen2.5:3b` 对比。
2. 建立 20 条中文指令测试集，覆盖基础、组合、危险、超范围指令。
3. 实现 `evaluation/dry_run_benchmark.py`，统计解析准确率。
4. 现场测试 `run_swing_actions.sh` 的真机执行。
5. 实现 ASR 语音输入模块。
6. 再做地图区域匹配和路径规划。
