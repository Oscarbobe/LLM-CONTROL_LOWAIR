#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

DEFAULT_TEXT_INSTRUCTION="起飞后悬停2秒再降落"
DEFAULT_MAP_INSTRUCTION="飞到果园上方悬停两秒再降落"
REPORT_PATH="data/reports/latest_report.md"
ACTION_PATH="data/processed/instructions/map_last_actions.json"

print_help() {
  cat <<'EOF'
用法：
  ./run_demo_menu.sh
  ./run_demo_menu.sh --help

菜单功能：
  1. 检查 Ubuntu 环境
  2. 完整验收链路
  3. 文本指令 dry-run
  4. 地图规划并保存动作 JSON
  5. 生成交付报告
  6. 查看交付报告
  7. 语音控制环境检查
  8. 进入语音 dry-run
  9. 生成发布包
 10. 启动 Streamlit 功能展示面板
  0. 退出
EOF
}

pause() {
  echo
  read -r -p "按 Enter 返回菜单..." _
}

run_text_demo() {
  local instruction
  read -r -p "请输入中文飞行指令 [${DEFAULT_TEXT_INSTRUCTION}]：" instruction
  instruction="${instruction:-$DEFAULT_TEXT_INSTRUCTION}"
  PYTHONPATH=src python -m swing_control.app.parse_instruction "$instruction" --dry-run --no-log
}

run_map_demo() {
  local instruction
  read -r -p "请输入地图目标指令 [${DEFAULT_MAP_INSTRUCTION}]：" instruction
  instruction="${instruction:-$DEFAULT_MAP_INSTRUCTION}"
  PYTHONPATH=src python -m swing_control.app.map_route "$instruction" --save-actions "$ACTION_PATH"
}

generate_report() {
  local instruction
  read -r -p "报告中的输入指令 [${DEFAULT_MAP_INSTRUCTION}]：" instruction
  instruction="${instruction:-$DEFAULT_MAP_INSTRUCTION}"
  PYTHONPATH=src python -m swing_control.app.generate_report \
    --instruction "$instruction" \
    --output "$REPORT_PATH"
}

view_report() {
  if [[ ! -f "$REPORT_PATH" ]]; then
    echo "报告不存在：$REPORT_PATH"
    echo "请先选择 5 生成交付报告。"
    return
  fi

  if command -v less >/dev/null 2>&1; then
    less "$REPORT_PATH"
  else
    sed -n '1,220p' "$REPORT_PATH"
  fi
}

package_release() {
  local version
  read -r -p "发布包版本名，留空使用时间戳：" version
  if [[ -n "$version" ]]; then
    ./scripts/package_release.sh "$version"
  else
    ./scripts/package_release.sh
  fi
}

show_menu() {
  clear 2>/dev/null || true
  cat <<'EOF'
========================================
 LLM-CONTROL_LOWAIR 演示菜单
========================================
 1. 检查 Ubuntu 环境
 2. 完整验收链路
 3. 文本指令 dry-run
 4. 地图规划并保存动作 JSON
 5. 生成交付报告
 6. 查看交付报告
 7. 语音控制环境检查
 8. 进入语音 dry-run
 9. 生成发布包
10. 启动 Streamlit 功能展示面板
 0. 退出
----------------------------------------
EOF
}

main() {
  case "${1:-}" in
    --help|-h|help)
      print_help
      return 0
      ;;
    "")
      ;;
    *)
      echo "未知参数：$1"
      print_help
      return 2
      ;;
  esac

  while true; do
    show_menu
    read -r -p "请选择功能：" choice
    echo

    case "$choice" in
      1)
        make check-env
        pause
        ;;
      2)
        ./scripts/verify_delivery.sh
        pause
        ;;
      3)
        run_text_demo
        pause
        ;;
      4)
        run_map_demo
        pause
        ;;
      5)
        generate_report
        pause
        ;;
      6)
        view_report
        pause
        ;;
      7)
        ./model/run_swing_voice.sh --check-env
        pause
        ;;
      8)
        ./model/run_swing_voice.sh --no-log
        pause
        ;;
      9)
        package_release
        pause
        ;;
      10)
        ./scripts/run_streamlit_demo.sh
        pause
        ;;
      0|q|Q)
        echo "已退出演示菜单。"
        return 0
        ;;
      *)
        echo "无效选择：$choice"
        pause
        ;;
    esac
  done
}

main "$@"
