# Ubuntu 交付安装与最终验收

本文档用于在一台新的 Ubuntu 机器上安装、检查、运行并生成交付报告。项目推荐使用 Python 3.11。

## 1. 推荐环境

推荐 Python 版本：

```text
Python 3.11
```

项目已提供：

- `.python-version`：给 pyenv/asdf 等工具识别 Python 主版本。
- `environment-delivery.yml`：Ubuntu 交付环境，固定 `python=3.11`。
- `environment-llm.yml`：包含 PyTorch/CUDA 的大模型环境，可在需要 GPU 时使用。
- `requirements.txt`：pip 依赖清单。

## 2. Conda 安装方式

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
conda env create -f environment-delivery.yml
conda activate llm-control-lowair
```

如果环境已经存在：

```bash
conda env update -f environment-delivery.yml --prune
conda activate llm-control-lowair
```

## 3. pip 安装方式

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pytest
```

## 4. Ollama 模型准备

需要先安装 Ollama，然后拉取项目默认模型：

```bash
ollama pull qwen3.5:4b
```

检查：

```bash
ollama list
```

应能看到 `qwen3.5:4b`。

## 5. 一键安装辅助

在已经准备好 Python 环境后，可运行：

```bash
./scripts/install_ubuntu_deps.sh
```

该脚本会安装 `requirements.txt`、`pytest`，并在检测到 `ollama` 时拉取 `qwen3.5:4b`。

## 6. 最终验收命令

安装完成后，执行：

```bash
make check-env
make delivery-check
```

验收通过的标准：

- Ubuntu 环境检查全部必需项通过。
- 自动化测试显示 `72 passed`。
- 文本 dry-run 能输出动作 JSON。
- 地图规划能生成 `data/processed/instructions/map_last_actions.json`。
- 交付报告能生成 `data/reports/latest_report.md`。

也可以运行演示入口：

```bash
./run_demo.sh
```

如果演示人员不熟悉命令行，使用交互式 Shell 菜单：

```bash
./run_demo_menu.sh
```

菜单包含环境检查、完整验收、文本 dry-run、地图规划、报告生成、报告查看、语音入口和发布包生成。

如果需要浏览器界面的功能展示面板：

```bash
make streamlit
```

然后打开：

```text
http://127.0.0.1:8501
```

如果需要完整验收链路：

```bash
./run_demo.sh --full
```

## 7. 发布包生成

生成交付压缩包：

```bash
./scripts/package_release.sh
```

输出目录：

```text
dist/
```

脚本会排除 `.git`、缓存、日志、录音、运行报告和临时文件，只保留源码、配置、文档、示例和脚本。
