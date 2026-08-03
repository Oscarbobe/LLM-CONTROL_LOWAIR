# Planning 路径规划模块

职责：根据目标坐标、地形、障碍物和安全限制生成航点路径。

输出应包含起飞点、目标点、中间航点、返航点和降落点。

当前已实现：

```text
action_planner.py
route_planner.py
```

它负责把通过校验的 Swing 动作 JSON 转换成 dry-run 可读步骤和 `pyparrot` 调用预览。

`route_planner.py` 负责把地图目标区域转换成 Swing 相对动作序列，并对圆形禁飞区做简化绕行。
