# Backroom Agent

Backroom Agent 是一个基于 LangGraph 的后室（The Backrooms）文字冒险游戏系统。它结合了即兴叙事、RAG（检索增强生成）和游戏状态管理，提供沉浸式的后室探索体验。

## 项目架构

项目由三个主要部分组成：

1.  **Agent Core (`backroom_agent/`)**: 也就是 "Game Master" 逻辑。使用 LangGraph 构建，包含主 Agent 和多个专门的 Subagent（Level, Event, Suggestion）。
2.  **Backend (`backend/`)**: 一个轻量级的 FastAPI 服务，为前端提供 HTTP 接口来流式传输 Agent 的响应。
3.  **Frontend (`frontend/`)**: 基于 React + Vite 的复古终端风格用户界面。

## 快速开始

### WSL 用户（推荐）

如果你使用 Windows Subsystem for Linux (WSL)，请参考 [WSL 配置指南](docs/wsl-setup.md) 进行设置。

**快速步骤**：
1. 在 PowerShell（管理员）中运行：`.\scripts\fix-wsl.ps1` 修复 WSL
2. 在 WSL 中运行：`bash scripts/setup-wsl.sh` 设置环境
3. 在 WSL 中运行：`bash scripts/start-wsl.sh` 启动项目

### 1. 环境准备

确保已安装：
- Python 3.12+
- Node.js (v18+)
- Docker Desktop（用于运行 Redis）

### 2. 启动 Redis

```bash
# 使用 Docker Compose 启动 Redis 服务
docker-compose up -d

# 验证 Redis 是否正常运行
docker-compose ps
# 或者使用 redis-cli 测试连接（如果已安装 redis-cli）
# redis-cli ping  # 应该返回 PONG
```

Redis 将在 `localhost:6379` 运行，无需密码。

### 3. 后端设置

```bash
# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # MacOS/Linux
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key (如 OPENAI_API_KEY, ANTHROPIC_API_KEY 等)
```

### 4. 运行后端

```bash
# 启动 API 服务 (默认端口 8000)
python backend/main.py
```

### 5. 前端设置与运行

新建一个终端窗口：

```bash
cd frontend
npm install
npm run dev
```

打开浏览器访问 `http://localhost:5173` 即可开始游戏。

## 开发与调试

### 独立运行 Agent

你可以使用 `scripts/` 目录下的脚本单独测试各个 Agent 模块，无需启动整个 Web 服务。

*   **测试主 DM 流程**:
    ```bash
    python scripts/run_agent.py
    ```

*   **测试 Level Agent (关卡生成/物品提取)**:
    此 Agent 会自动搜索后室 Wiki，提取关卡信息和物品，并生成 JSON 数据到 `data/level/`。
    ```bash
    # 自动搜索并处理 Level 3
    python scripts/run_level_agent.py "Level 3"
    ```

*   **测试 Event Agent (随机事件)**:
    ```bash
    python scripts/run_event_subagent.py
    ```

*   **测试 Suggestion Agent (行动建议)**:
    ```bash
    python scripts/run_suggestion_subagent.py
    ```

## 项目结构

```
BackroomAgent/
├── backend/                # FastAPI 后端
├── backroom_agent/         # LangGraph 核心逻辑
│   ├── prompts/            # 主 Agent Prompts (.prompt)
│   ├── subagents/          # 子 Agent (Level, Event, Suggestion)
│   │   ├── level/
│   │   │   └── prompts/    # Level Agent Prompts
│   │   └── ...
│   ├── tools/              # 工具函数 (Wiki Search, Item Extraction)
│   └── utils/              # 通用工具
├── data/                   # 游戏数据 (Levels, Items)
├── frontend/               # React 前端
├── scripts/                # 调试与运行脚本
└── tests/                  # 单元测试
```

## 数据协议

前后端通信及游戏状态结构严格遵循 [PROTOCOL.md](PROTOCOL.md)。任何状态字段的修改（如新增属性、状态）都需要同步更新：
1.  `PROTOCOL.md`
2.  `backend/protocol.py` (Pydantic Models)
3.  `frontend/src/types.ts` (TypeScript Interfaces)
