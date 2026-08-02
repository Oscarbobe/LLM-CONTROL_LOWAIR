# Parrot Swing 控制流程说明

本文档记录在本文件夹中使用 `pyparrot` 控制 Parrot Swing 飞机的流程。Swing 使用 BLE 蓝牙连接，不使用 WiFi。

当前已记录的 Swing 地址：

```text
E0:14:89:09:3D:CB
```

## 1. 准备

需要：

- Parrot Swing 飞机，电量充足
- Linux 电脑或树莓派
- 可用的 BLE 蓝牙适配器
- 已安装 `pyparrot` 的 Python 环境
- 空旷、安全的测试区域

进入本文件夹：

```bash
cd /home/abc/桌面/SWING_CONTROL
```

确认 Python 环境可用：

```bash
/home/abc/miniconda3/bin/python -c "from pyparrot.Minidrone import Swing; print('Swing OK')"
```

看到 `Swing OK` 即可继续。也可以用环境变量指定其他 Python：

```bash
PYTHON_BIN=/path/to/python ./model/run_swing_direct_flight.sh --help
```

## 2. 一键自动运行

推荐直接使用自动化脚本：

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_direct_flight.sh
```

这个脚本会自动执行：

1. 尝试启用蓝牙
2. 扫描 Swing 地址
3. 写入 Swing 地址到本地 [demoSwingDirectFlight.py](/home/abc/桌面/SWING_CONTROL/model/demoSwingDirectFlight.py:1)
4. 运行只连接、不起飞的测试
5. 连接成功后，等待你按回车确认，再运行飞行示例

如果你已经知道 Swing 地址，可以跳过扫描：

```bash
cd /home/abc/桌面/SWING_CONTROL
./model/run_swing_direct_flight.sh --addr E0:14:89:09:3D:CB
```

或：

```bash
cd /home/abc/桌面/SWING_CONTROL
SWING_ADDR=E0:14:89:09:3D:CB ./model/run_swing_direct_flight.sh
```

飞行示例开始前会停在确认提示：

```text
确认 Swing 在空旷安全区域，准备起飞后按 Enter；输入 q 后回车取消：
```

确认安全后按 Enter，取消则输入 `q` 后回车。

## 3. 自动化脚本参数

查看帮助：

```bash
./model/run_swing_direct_flight.sh --help
```

常用参数：

```bash
./model/run_swing_direct_flight.sh --addr E0:14:89:09:3D:CB
./model/run_swing_direct_flight.sh --skip-bluetooth-fix
./model/run_swing_direct_flight.sh --no-sudo
```

常用环境变量：

```bash
PYTHON_BIN=/home/abc/miniconda3/bin/python
SWING_ADDR=E0:14:89:09:3D:CB
RUN_WITH_SUDO=0
FIX_SCRIPT=/path/to/fix_mt7925_bluetooth.sh
```

说明：

- 默认会优先使用 `/home/abc/miniconda3/bin/python`，否则查找 `python3` 或 `python`。
- BLE 扫描和连接通常需要权限，脚本默认通过 `sudo` 执行相关命令。
- 当前文件夹已包含 [fix_mt7925_bluetooth.sh](/home/abc/桌面/SWING_CONTROL/model/fix_mt7925_bluetooth.sh:1)。自动化脚本会在第 1 步自动调用它。

## 4. 手动流程：启用蓝牙

先尝试打开蓝牙：

```bash
bluetoothctl power on
bluetoothctl show
```

正常状态应包含：

```text
Powered: yes
```

如果系统提示没有默认控制器，或内置 MediaTek/MT7925 蓝牙初始化失败，可以手动运行本地蓝牙修复脚本：

```bash
cd /home/abc/桌面/SWING_CONTROL
sudo ./model/fix_mt7925_bluetooth.sh
```

脚本成功后会显示类似：

```text
Bluetooth controller looks usable.
```

成功后不要再手动重启 `bluetooth.service`，直接运行自动化脚本。

## 5. 手动流程：扫描 Swing 地址

打开 Swing 飞机电源，然后扫描：

```bash
cd /home/abc/桌面/SWING_CONTROL
sudo /home/abc/miniconda3/bin/python -m pyparrot.scripts.findMinidrone
```

看到类似输出后记录地址：

```text
FOUND A SWING!
Device E0:14:89:09:3D:CB (random), RSSI=-60 dB
```

如果需要使用系统工具扫描：

```bash
bluetoothctl
power on
scan on
```

看到名字包含 `Swing` 的设备后，记录它的 MAC 地址。

## 6. 手动流程：只测试连接

本地飞行 demo 支持只连接、不起飞：

```bash
cd /home/abc/桌面/SWING_CONTROL
sudo /home/abc/miniconda3/bin/python model/demoSwingDirectFlight.py --addr E0:14:89:09:3D:CB --connect-only
```

成功时应看到：

```text
connected: True
disconnect
```

如果普通用户已经有 BLE 权限，可以不加 `sudo`：

```bash
/home/abc/miniconda3/bin/python model/demoSwingDirectFlight.py --addr E0:14:89:09:3D:CB --connect-only
```

## 7. 手动流程：运行飞行示例

确认飞机在安全区域，周围无人、无玻璃和易碎物后运行：

```bash
cd /home/abc/桌面/SWING_CONTROL
sudo /home/abc/miniconda3/bin/python model/demoSwingDirectFlight.py --addr E0:14:89:09:3D:CB
```

这个示例会依次执行：

1. 连接 Swing
2. 请求状态
3. 安全起飞
4. 左右移动、左右转向
5. 切换到 `plane_forward` 模式
6. 切回 `quadricopter` 模式
7. 安全降落
8. 断开连接

## 8. 自定义控制脚本模板

可以基于下面结构写自己的控制脚本：

```python
from pyparrot.Minidrone import Swing

swing = Swing("E0:14:89:09:3D:CB")

print("trying to connect")
success = swing.connect(num_retries=3)
print("connected:", success)

if success:
    try:
        swing.smart_sleep(2)
        swing.ask_for_state_update()
        swing.smart_sleep(2)

        print("takeoff")
        swing.safe_takeoff(5)

        print("plane forward")
        swing.set_flying_mode("plane_forward")
        swing.smart_sleep(1)

        print("quadricopter")
        swing.set_flying_mode("quadricopter")

        print("landing")
        swing.safe_land(5)
        swing.smart_sleep(5)
    finally:
        print("disconnect")
        swing.disconnect()
```

常用动作：

```python
swing.safe_takeoff(5)
swing.safe_land(5)
swing.fly_direct(roll=0, pitch=0, yaw=0, vertical_movement=20, duration=1)
swing.set_flying_mode("plane_forward")
swing.set_flying_mode("quadricopter")
swing.set_plane_gear_box("gear_1")
swing.set_plane_gear_box("gear_2")
swing.set_plane_gear_box("gear_3")
```

## 9. 安全建议

- 第一次测试先跑 `--connect-only`，再跑完整飞行示例。
- 飞行前确认 Swing 电量充足。
- 保持飞机周围空旷。
- 不要在人、玻璃、易碎物、狭小空间附近测试。
- 如果连接或飞行状态不稳定，优先降落。
- 不要一开始就测试复杂路线或高速模式。

## 10. 问题记录与排查

### 10.1 No module named pyparrot

现象：

```text
ModuleNotFoundError: No module named 'pyparrot'
```

原因：正在使用的 Python 环境没有安装 `pyparrot`。

解决：先确认本机哪个 Python 能导入 `pyparrot`：

```bash
/home/abc/miniconda3/bin/python -c "from pyparrot.Minidrone import Swing; print('Swing OK')"
```

如果需要使用其他 Python：

```bash
cd /home/abc/桌面/SWING_CONTROL
PYTHON_BIN=/path/to/python ./model/run_swing_direct_flight.sh --addr E0:14:89:09:3D:CB
```

### 10.2 Permission Denied

现象：

```text
bluepy.btle.BTLEManagementError: Permission Denied
```

原因：BLE 扫描或连接需要更高权限。

解决：

```bash
sudo /home/abc/miniconda3/bin/python -m pyparrot.scripts.findMinidrone
sudo /home/abc/miniconda3/bin/python model/demoSwingDirectFlight.py --addr E0:14:89:09:3D:CB --connect-only
```

自动化脚本默认会使用 `sudo`。如果你已经配置好普通用户 BLE 权限，可以用：

```bash
RUN_WITH_SUDO=0 ./model/run_swing_direct_flight.sh --addr E0:14:89:09:3D:CB
```

### 10.3 No default controller available

现象：

```text
No default controller available
```

或：

```text
Can't get device info: No such device
Set Powered for hci0 failed with status 0x11 (Invalid Index)
```

原因：系统没有可用蓝牙控制器，或内置 MediaTek/MT7925 蓝牙没有被 `btusb` 正确绑定。

解决：

```bash
bluetoothctl power on
bluetoothctl show
```

如果仍然失败，运行本地蓝牙修复脚本：

```bash
sudo ./model/fix_mt7925_bluetooth.sh
```

修复脚本成功后不要再手动重启 `bluetooth.service`，直接扫描或连接。

### 10.4 MT7925 固件初始化失败

曾观察到的内核日志：

```text
Bluetooth: hci0: Execution of wmt command timed out
Bluetooth: hci0: Failed to send wmt patch dwnld (-110)
Bluetooth: hci0: Failed to set up firmware (-110)
```

原因：内置 MediaTek/MT7925 蓝牙驱动或固件初始化失败。

可尝试更新固件：

```bash
sudo /path/to/fix_mt7925_bluetooth.sh --update-firmware
sudo reboot
```

如果仍然不稳定，建议使用 Linux 兼容的外置 USB 蓝牙适配器。

### 10.5 scanend Rejected

现象：

```text
bluepy.btle.BTLEManagementError: Failed to execute management command 'scanend'
```

处理：如果前面已经输出 `FOUND A SWING!` 和设备地址，可以先记录地址继续连接测试。否则重新打开蓝牙后再扫描。

### 10.6 project has no attribute myclass

现象：

```text
AttributeError: 'project' has no attribute 'myclass'
```

原因：新版 `untangle` 把 XML 标签 `<class>` 暴露为 `class_`，旧版 `pyparrot` 代码访问的是 `myclass`。

处理：需要在当前 Python 环境中的 `pyparrot` 包里做兼容修复，或改用已修复的 `pyparrot` 环境。先确认当前环境：

```bash
/home/abc/miniconda3/bin/python -c "import pyparrot, inspect; print(pyparrot.__file__)"
```
