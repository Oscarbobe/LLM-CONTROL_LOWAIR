# Mapping 地图模块

职责：管理山区地图、地块边界、障碍物、禁飞区和安全降落点。

数据建议存放在 `data/maps/`。

当前实现：

```text
site_map.py
```

默认地图：

```text
data/maps/site_map.json
```

能力：

- 加载本地 JSON 地图
- 匹配命名区域和别名
- 检查目标是否在地图边界内
- 检查目标是否落入禁飞区
