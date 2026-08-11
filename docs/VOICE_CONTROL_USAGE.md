# 麦克风语音控制使用教程

本项目已经实现麦克风说话控制链路：

```text
按 Enter 开始录音
  -> arecord/ffmpeg 保存 wav 到 data/raw/audio/
  -> openai-whisper 转成中文文本
  -> Ollama/规则兜底解析成动作 JSON
  -> action_validator 安全校验
  -> dry-run 输出 pyparrot 预览
  -> 真机模式输入“确认执行”
  -> SwingActionExecutor 调用 pyparrot 飞行
```

## 1. 环境自检

先运行：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
./model/run_swing_voice.sh --check-env
```

当前本机已检查通过：

```text
arecord: OK
ffmpeg: OK
ollama: OK
whisper 命令: OK
Python whisper: OK
torch cuda: OK
麦克风设备: ALC257 Analog
```

## 2. 语音 dry-run

先不要连接无人机，只测试“说话 -> 识别 -> 动作预览”：

```bash
./model/run_swing_voice.sh
```

进入后会看到：

```text
按 Enter 录音>
```

按 Enter 后，在 4 秒内说：

```text
起飞后悬停两秒再降落
```

程序会输出：

```text
识别文本
动作 JSON
校验结果
Dry-run 动作序列
pyparrot 预览
```

退出：

```text
q
```

## 3. 调整录音时长

如果一句话说不完，可以延长录音：

```bash
./model/run_swing_voice.sh --record-seconds 5
```

如果环境嘈杂，可以先说短句：

```text
向前飞一秒
右转一秒
起飞后悬停两秒再降落
```

## 4. 选择 Whisper 模型

默认模型：

```text
base
```

首次使用某个 Whisper 模型时，程序可能会自动下载模型文件。

更快但准确率低：

```bash
./model/run_swing_voice.sh --asr-model tiny
```

更稳但更慢：

```bash
./model/run_swing_voice.sh --asr-model small
```

## 5. 真机语音执行

确认 dry-run 识别稳定后，再运行真机模式：

```bash
./model/run_swing_voice.sh --execute
```

已知 Swing 地址时：

```bash
./model/run_swing_voice.sh --execute --addr E0:14:89:09:3D:CB
```

真机模式会先执行：

```text
蓝牙恢复
  -> 扫描 Swing
  -> 连接测试
  -> 进入语音控制循环
```

每条语音指令都会先输出动作预览，必须输入：

```text
确认执行
```

输入其他内容会取消本条飞行动作。

## 6. 麦克风设备

当前检测到：

```text
card 1: PCH [HDA Intel PCH], device 0: ALC257 Analog
```

默认使用：

```text
default
```

如果默认设备录不到音，可以指定 ALSA 设备：

```bash
./model/run_swing_voice.sh --audio-device hw:1,0 --record-seconds 5
```

也可以先查看设备：

```bash
arecord -l
pactl list short sources
```

## 7. 常见问题

### 7.1 提示没有 Whisper

安装：

```bash
python -m pip install openai-whisper
```

检查：

```bash
/home/abc/miniconda3/bin/python -c "import whisper; print(whisper.__version__)"
```

### 7.2 第一次运行很慢

Whisper 首次使用模型时会下载模型文件，等下载完成后再试。

### 7.3 提示没有识别到有效文本

如果看到：

```text
ASR 已可用，但本段录音没有识别到有效文本
```

说明 Whisper 已经能运行，但这一段录音里没有清楚的人声。可以尝试：

```bash
./model/run_swing_voice.sh --record-seconds 5
```

并靠近麦克风说短句。

### 7.4 识别不准

可以尝试：

```bash
./model/run_swing_voice.sh --record-seconds 5 --asr-model small
```

说话时尽量使用短句：

```text
起飞后悬停两秒再降落
向前飞一秒
左转一秒
```

程序会对常见 Whisper 识别差异做归一化，例如：

```text
起飛 -> 起飞
玄廳 / 玄停 -> 悬停
兩秒 -> 两秒
```

### 7.5 真机模式下麦克风异常

真机模式可能涉及 sudo。脚本已保留 `HOME`、`XDG_RUNTIME_DIR`、`PULSE_SERVER`，但如果麦克风仍异常，可以先确认普通用户 dry-run 正常：

```bash
./model/run_swing_voice.sh --record-seconds 3
```

如果普通用户可以直接连接 BLE，也可以尝试：

```bash
RUN_WITH_SUDO=0 ./model/run_swing_voice.sh --execute --addr E0:14:89:09:3D:CB
```

### 7.6 只想测试录音和识别，不飞

使用 dry-run：

```bash
./model/run_swing_voice.sh --record-seconds 4 --asr-model tiny
```

不加 `--execute` 就不会连接无人机。
