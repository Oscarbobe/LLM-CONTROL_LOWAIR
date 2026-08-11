# 地图能力使用教程

本项目已经打通最小地图能力：中文指令可以引用地图中的命名区域，系统会把目标区域转换为 Swing 可执行的相对飞行动作。

## 1. 地图文件

默认地图：

```text
data/maps/site_map.json
```

当前包含：

```text
起飞点
果园
玉米地
水渠
房屋禁飞区
电线杆禁飞区
飞行边界
基础速度/悬停/起降参数
```

坐标系：

```text
x 正方向：向前
x 负方向：向后
y 正方向：向右
y 负方向：向左
z：高度
单位：米
```

注意：Parrot Swing 当前没有定位闭环，项目会把地图坐标近似转换为 `fly_forward/fly_right/...` 这类相对动作。

## 2. 可用地图指令

```text
飞到果园上方悬停两秒再降落
巡视玉米地
飞到水渠旁边悬停一秒
飞到果树区
飞到农田
飞到渠边
```

## 3. 单独测试地图规划

```bash
cd /home/abc/桌面/LLM-CONTROL_LOWAIR
PYTHONPATH=src /home/abc/miniconda3/bin/python -m swing_control.app.map_route "飞到果园上方悬停两秒再降落"
```

输出会包含：

```text
地图路径规划
目标区域
地图警告
动作 JSON
校验结果
Dry-run 动作序列
```

## 4. 在交互控制中使用

文本交互：

```bash
./model/run_swing_interactive.sh
```

语音交互：

```bash
./model/run_swing_voice.sh --record-seconds 5
```

真机文本执行：

```bash
./model/run_swing_interactive.sh --execute
```

真机语音执行：

```bash
./model/run_swing_voice.sh --execute --record-seconds 5
```

真机模式仍会要求输入：

```text
确认执行
```

## 5. 修改地图

新增区域时，在 `areas` 中加入：

```json
{
  "name": "菜地",
  "aliases": ["蔬菜地", "菜园"],
  "center": {"x": 2, "y": -2, "z": 1.5},
  "radius_m": 1.0
}
```

新增禁飞区时，在 `no_fly_zones` 中加入：

```json
{
  "name": "人群区域",
  "center": {"x": 0, "y": 3, "z": 0},
  "radius_m": 1.0,
  "buffer_m": 0.5
}
```

## 6. 相关代码

```text
src/swing_control/mapping/site_map.py
src/swing_control/planning/route_planner.py
src/swing_control/app/map_route.py
src/swing_control/nlp/instruction_parser.py
```

核心逻辑：

```text
site_map.py -> 加载地图、匹配区域、检查禁飞区
route_planner.py -> 目标区域转航点、航点转动作 JSON
map_route.py -> 单独测试地图规划
instruction_parser.py -> 解析兜底时自动调用地图规划
```

## 7. 当前限制

- 这是局部演示地图，不是 GPS/GIS 真地图。
- 当前动作是相对飞行，不是闭环定位。
- 障碍物避让是基于地图圆形禁飞区的简化绕行。
- 没有实时定位反馈，真机测试时必须在小范围、安全区域内进行。
