# NLP 指令解析模块

职责：将自然语言文本转换为结构化飞行任务。

示例：

```text
飞到那片玉米地上方巡视
```

转换为：

```text
intent=inspect, target=玉米地, action=巡航巡视
```

当前已实现：

```text
instruction_parser.py
```

它通过 Ollama 把中文指令解析为 Swing 动作 JSON。
