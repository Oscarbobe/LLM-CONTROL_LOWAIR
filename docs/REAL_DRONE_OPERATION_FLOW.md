# 无人机实际操作流程

本项目现在把 `model/` 里的直接飞行脚本模式接入到了自然语言控制流程中。推荐入口是：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute
```

## 1. 外层自动化流程

```text
run_swing_instruction.sh --execute
  -> 检查 Python、Ollama、pyparrot
  -> 调用 fix_mt7925_bluetooth.sh 修复或启用蓝牙
  -> 按 LowAir-GS 的 MT7925 流程绑定 btusb、重载模块、解除 rfkill、验证 HCI
  -> 如果没有传 --addr，则用 pyparrot 和 bluetoothctl 扫描 Swing
  -> 如果扫描失败，再恢复蓝牙并重扫一次
  -> 调用 demoSwingDirectFlight.py --connect-only 做连接测试
  -> 调用 src/swing_control/app/run_instruction.py
```

已知地址时可以跳过扫描：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute --addr E0:14:89:09:3D:CB
```

## 2. Python 实际操作流程

```text
中文指令
  -> instruction_parser 调用 Ollama
  -> 生成动作 JSON
  -> 保存 data/processed/instructions/last_actions.json
  -> action_validator 校验动作合法性和顺序
  -> action_planner 输出 dry-run 动作序列
  -> manual_confirmation 要求输入“确认执行”
  -> SwingActionExecutor 连接 pyparrot
  -> 逐条调用 safe_takeoff / fly_direct / smart_sleep / safe_land
  -> 异常时尝试 safe_land(5)
  -> disconnect
  -> 写入 data/logs/*.jsonl
```

## 3. 当前实际可飞动作

```text
pre_flight_check -> 状态检查
takeoff -> 安全起飞
land -> 安全降落
hover -> 悬停
fly_forward / fly_backward -> 前后移动
fly_left / fly_right -> 左右移动
turn_left / turn_right -> 左右转向
fly_up / fly_down -> 上升下降
switch_plane_forward -> 固定翼前飞模式
switch_quadricopter -> 四旋翼模式
```

## 4. 安全确认

真机执行前必须输入：

```text
确认执行
```

输入其他内容会取消执行。第一次测试建议使用最短动作：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute
```
