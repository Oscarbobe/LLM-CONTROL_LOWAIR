# 项目运行环境说明

本文档分为两部分：一部分是当前 Parrot Swing 自动化脚本的最小可运行环境，另一部分是自然语言无人机控制产品原型的扩展开发环境。

## 1. 最小运行环境

用于运行当前文件夹中的自动化脚本：

```bash
./model/run_swing_direct_flight.sh
```

### 硬件环境

- Linux 电脑或树莓派
- Parrot Swing 无人机
- 支持 BLE 的蓝牙适配器
- 无人机电池、备用螺旋桨、防撞圈
- 空旷、安全的飞行测试区域

### 系统环境

- Ubuntu / Debian 系 Linux 系统
- `bash`
- `sudo`
- `systemd`
- BlueZ 蓝牙工具链

需要的系统命令：

```bash
bluetoothctl
hciconfig
rfkill
lsusb
systemctl
modprobe
timeout
```

可安装常用系统依赖：

```bash
sudo apt update
sudo apt install -y bluetooth bluez bluez-tools wireless-tools usbutils rfkill python3-pip
```

### Python 环境

当前机器已验证可用：

```bash
/home/abc/miniconda3/bin/python
```

检查命令：

```bash
/home/abc/miniconda3/bin/python -c "from pyparrot.Minidrone import Swing; print('Swing OK')"
```

必须具备：

- Python 3
- `pyparrot`
- `bluepy`
- `untangle`
- `zeroconf`
- `opencv-python`
- `numpy`

安装普通依赖：

```bash
pip install -r requirements.txt
```

如果使用当前 conda Python，建议显式指定：

```bash
/home/abc/miniconda3/bin/python -m pip install -r requirements.txt
```

注意：`pyparrot` 是无人机控制核心库。如果 `pip install pyparrot` 不可用，应使用已经跑通的本地 `pyparrot` 环境，或从已有源码目录安装：

```bash
cd /path/to/pyparrot
pip install -e .
```

## 2. 自然语言控制扩展环境

用于后续实现“语音输入 -> 指令解析 -> 地图匹配 -> 路径规划 -> 飞控执行”的完整产品原型。

### 语音识别与自然语言处理

- `SpeechRecognition`
- `openai-whisper` 或其他离线 ASR 模型
- `transformers`
- `torch`
- `jieba`
- `pydantic`

### 地图与路径规划

- `geopandas`
- `shapely`
- `pyproj`
- `networkx`
- `matplotlib`

### 数据处理与可视化

- `pandas`
- `scipy`
- `PyYAML`
- `rich`
- `pytest`

扩展依赖可按实际机器性能逐步安装，不要求一次性全部安装。

大语言模型建议单独安装到 Python 3.11 环境，详见 [LLM_INSTALL.md](LLM_INSTALL.md)。

## 3. 推荐目录使用方式

- `data/raw/audio/`：原始语音采集文件
- `data/raw/text/`：原始文本指令
- `data/processed/instructions/`：清洗和结构化后的指令数据
- `data/maps/`：山区地图、地块边界、障碍物坐标
- `data/logs/`：飞行测试日志、识别日志、异常日志
- `configs/default.yaml`：默认无人机、路径规划和安全限制配置

## 4. 常用验证命令

验证自动化脚本语法：

```bash
bash -n model/run_swing_direct_flight.sh
bash -n model/fix_mt7925_bluetooth.sh
```

验证 Python demo：

```bash
/home/abc/miniconda3/bin/python model/demoSwingDirectFlight.py --help
```

验证项目配置依赖：

```bash
/home/abc/miniconda3/bin/python -c "import yaml; yaml.safe_load(open('configs/default.yaml', encoding='utf-8')); print('yaml ok')"
```

验证蓝牙控制器：

```bash
bluetoothctl show
hciconfig -a
```

验证 Swing 连接：

```bash
sudo /home/abc/miniconda3/bin/python model/demoSwingDirectFlight.py --addr E0:14:89:09:3D:CB --connect-only
```
