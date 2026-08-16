.PHONY: test map-demo text-demo voice-check check-env report delivery-check demo menu streamlit package clean help

PYTHONPATH := PYTHONPATH=src

help:
	@echo "LLM-CONTROL_LOWAIR 项目命令"
	@echo ""
	@echo "  make test         运行所有测试"
	@echo "  make map-demo     地图指令 → 动作 JSON → 保存"
	@echo "  make text-demo    文本指令 dry-run"
	@echo "  make check-env    检查 Ubuntu 运行环境"
	@echo "  make report       生成 Ubuntu 交付报告"
	@echo "  make delivery-check 运行 Ubuntu 交付验证链路"
	@echo "  make demo         运行快速演示入口"
	@echo "  make menu         打开交互式 Shell 演示菜单"
	@echo "  make streamlit    启动 Streamlit 功能展示面板"
	@echo "  make package      生成发布压缩包"
	@echo "  make voice-check  检查语音环境"
	@echo "  make clean        清理缓存、日志、录音和报告"
	@echo ""

test:
	$(PYTHONPATH) pytest -v

map-demo:
	$(PYTHONPATH) python -m swing_control.app.map_route \
		"飞到果园上方悬停两秒再降落" \
		--save-actions data/processed/instructions/map_last_actions.json

text-demo:
	$(PYTHONPATH) python -m swing_control.app.parse_instruction \
		"起飞后悬停2秒再降落" --dry-run

check-env:
	./scripts/check_ubuntu_env.sh

report:
	$(PYTHONPATH) python -m swing_control.app.generate_report \
		--instruction "飞到果园上方悬停两秒再降落" \
		--output data/reports/latest_report.md

delivery-check:
	./scripts/verify_delivery.sh

demo:
	./run_demo.sh

menu:
	./run_demo_menu.sh

streamlit:
	./scripts/run_streamlit_demo.sh

package:
	./scripts/package_release.sh

voice-check:
	./model/run_swing_voice.sh --check-env

clean:
	find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" -o -name ".ruff_cache" \) -prune -exec rm -rf {} +
	find data/logs -type f -name "*.jsonl" -delete
	find data/raw/audio -type f \( -name "*.wav" -o -name "*.txt" \) -delete
	find data/reports -type f -name "*.md" -delete
