# BackroomAgent

一个最小可运行的 LangGraph Python 项目骨架。

## Quickstart

1) 创建虚拟环境并安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) （可选）配置环境变量

```bash
cp .env.example .env
```

如果你配置了 `OPENAI_API_KEY`，会使用 OpenAI；否则会自动使用 Fake 模型，确保项目无需外部凭证也能跑通。

3) 运行

```bash
python -m backroom_agent
```

也可以指定一次性输入：

```bash
PROMPT="你好，LangGraph" python -m backroom_agent
```

## 代码结构

- Graph 定义：src/backroom_agent/graph.py
- 入口：src/backroom_agent/__main__.py
