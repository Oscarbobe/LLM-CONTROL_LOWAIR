#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

MODE="${1:-quick}"

case "$MODE" in
  quick)
    echo "[1/4] Ubuntu 环境检查"
    make check-env

    echo "[2/4] 文本指令 dry-run"
    make text-demo

    echo "[3/4] 地图规划 demo"
    make map-demo

    echo "[4/4] 生成交付报告"
    make report

    echo "演示完成：data/reports/latest_report.md"
    ;;
  --full|full)
    ./scripts/verify_delivery.sh
    ;;
  --voice|voice)
    ./model/run_swing_voice.sh --check-env
    ./model/run_swing_voice.sh --no-log
    ;;
  --menu|menu)
    ./run_demo_menu.sh
    ;;
  --streamlit|streamlit)
    ./scripts/run_streamlit_demo.sh
    ;;
  --help|-h|help)
    echo "用法："
    echo "  ./run_demo.sh          快速演示：环境检查、文本 dry-run、地图规划、报告生成"
    echo "  ./run_demo.sh --full   完整验收：环境检查、测试、dry-run、地图规划、报告生成"
    echo "  ./run_demo.sh --voice  语音 dry-run 入口"
    echo "  ./run_demo.sh --menu   打开交互式 Shell 演示菜单"
    echo "  ./run_demo.sh --streamlit 启动 Streamlit 功能展示面板"
    ;;
  *)
    echo "未知参数：$MODE"
    echo "运行 ./run_demo.sh --help 查看用法。"
    exit 2
    ;;
esac
