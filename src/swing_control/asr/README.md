# ASR 语音识别模块

职责：将农户语音输入转换为文本指令。

输入：麦克风音频或 `data/raw/audio/` 中的语音文件。

输出：文本指令。

当前实现：

```text
microphone.py -> 使用 arecord 或 ffmpeg 录制 wav
transcriber.py -> 使用 openai-whisper 或 whisper 命令转文字
```

语音控制入口：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
./model/run_swing_voice.sh
```

真机语音控制：

```bash
./model/run_swing_voice.sh --execute
```

依赖：

```bash
python -m pip install openai-whisper
```

如果本机有多个麦克风，可以指定设备：

```bash
./model/run_swing_voice.sh --audio-device default --record-seconds 5
```
