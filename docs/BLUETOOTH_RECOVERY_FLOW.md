# 真机蓝牙控制器恢复流程

本项目已参照 `/home/abc/桌面/LowAir-GS/pyparrot` 的 pyparrot 自动化连接方式，把 MT7925 蓝牙恢复逻辑接入本项目 `model/` 入口脚本。

## 1. 恢复逻辑

```text
检测/准备蓝牙
  -> 调用 model/fix_mt7925_bluetooth.sh
  -> 针对 0489:e111 写入 btusb new_id
  -> 禁用目标 USB 设备 autosuspend
  -> 重载 btusb / btmtk
  -> rfkill unblock bluetooth
  -> 启动 bluetooth.service
  -> 尝试拉起 hci0/hci1
  -> bluetoothctl show 验证控制器可用
```

如果扫描 Swing 失败，`run_swing_direct_flight.sh` 和 `run_swing_instruction.sh --execute` 会再执行一次蓝牙恢复，然后重新扫描一次。

## 2. 推荐真机命令

中文指令真机执行：

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute
```

直接飞行 demo：

```bash
./model/run_swing_direct_flight.sh
```

动作 JSON 真机执行：

```bash
./model/run_swing_actions.sh --addr E0:14:89:09:3D:CB
```

## 3. 常用恢复参数

默认目标蓝牙 USB 设备：

```text
0489:e111
```

如果设备 ID 不同：

```bash
./model/run_swing_instruction.sh "起飞后悬停2秒再降落" --execute --bluetooth-device VID:PID
```

如果日志提示固件初始化失败，例如 `Failed to set up firmware (-110)`，再尝试：

```bash
sudo ./model/fix_mt7925_bluetooth.sh --update-firmware
```

或者通过入口脚本传入：

```bash
./model/run_swing_direct_flight.sh --update-bluetooth-firmware
```

如果希望开机自动修复：

```bash
sudo ./model/fix_mt7925_bluetooth.sh --install-persistent
```

或：

```bash
./model/run_swing_direct_flight.sh --install-bluetooth-fix
```

## 4. 判断是否恢复成功

运行：

```bash
bluetoothctl show
```

正常应看到控制器信息，并包含：

```text
Powered: yes
```

如果仍然显示：

```text
No default controller available
```

说明 Linux 还没有识别到可用 HCI 控制器，需要重新插拔蓝牙设备、执行固件更新，或者更换 Linux 兼容 USB 蓝牙适配器。
