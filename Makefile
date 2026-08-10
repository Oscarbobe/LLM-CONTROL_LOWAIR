.PHONY: test map-demo text-demo voice-check help

PYTHONPATH := PYTHONPATH=src

help:
	@echo "SWING_CONTROL 项目命令"
	@echo ""
	@echo "  make test         运行所有测试"
	@echo "  make map-demo     地图指令 → 动作 JSON → 保存"
	@echo "  make text-demo    文本指令 dry-run"
	@echo "  make voice-check  检查语音环境"
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

voice-check:
	./model/run_swing_voice.sh --check-env