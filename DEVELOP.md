# 开发指南

本文档包含 Backroom Agent 项目的开发相关信息，包括项目结构、调试方法、代码规范等。

## 项目结构

```
BackroomAgent/
├── backend/                # FastAPI 后端（已迁移到 backroom_agent/server.py）
├── backroom_agent/         # LangGraph 核心逻辑
│   ├── agent/              # 主 Agent 图结构
│   │   ├── graph.py        # LangGraph 定义
│   │   ├── handlers/      # 事件处理器（init, message）
│   │   └── nodes/          # 图节点实现
│   ├── prompts/             # 主 Agent Prompts (.prompt)
│   ├── subagents/          # 子 Agent (Level, Event, Suggestion)
│   │   ├── level/
│   │   │   └── prompts/    # Level Agent Prompts
│   │   └── ...
│   ├── tools/              # 工具函数 (Wiki Search, Item Extraction)
│   ├── utils/              # 通用工具
│   │   ├── session_manager.py  # 会话管理器
│   │   └── session_storage.py  # Redis 会话存储
│   └── server.py           # FastAPI 服务器
├── data/                   # 游戏数据 (Levels, Items)
├── frontend/               # React 前端
│   └── src/
│       ├── hooks/
│       │   └── useGameEngine.ts  # 游戏引擎 Hook（DungeonMaster）
│       └── types.ts        # TypeScript 类型定义
├── scripts/                # 调试与运行脚本
└── tests/                  # 单元测试
```

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

### 代码格式化

项目使用自动化代码格式化工具：

- **Python**: `black` (行长度 88) + `isort` (black 兼容模式) + `pyright` (类型检查)
- **Frontend**: ESLint (自动修复模式)

运行格式化：
```bash
make format
```

### Git Hooks

项目包含自动化的 Git hooks：

- **pre-commit**: 在每次提交前自动运行代码格式化（`make format`）
- **prepare-commit-msg**: 使用 LLM 自动生成 commit message（需要配置 `COMMIT_MSG_PROVIDER` 和对应的 API Key）

安装 hooks：
```bash
make install-hooks
```

### VS Code / Cursor 配置

项目包含 `.vscode/settings.json` 配置，支持：
- 保存时自动格式化（`formatOnSave`）
- 自动修复代码问题（`codeActionsOnSave`）

推荐安装的扩展（见 `.vscode/extensions.json`）：
- Python 扩展（Black Formatter, isort）
- ESLint 扩展

## 数据协议

前后端通信及游戏状态结构严格遵循 [PROTOCOL.md](PROTOCOL.md)。任何状态字段的修改（如新增属性、状态）都需要同步更新：

1.  `PROTOCOL.md` - 协议文档
2.  `backroom_agent/protocol.py` - Pydantic Models
3.  `frontend/src/types.ts` - TypeScript Interfaces

### 协议更新流程

1. 更新 `PROTOCOL.md` 描述新的数据结构或行为
2. 更新 `backroom_agent/protocol.py` 添加/修改 Pydantic 模型
3. 更新 `frontend/src/types.ts` 同步 TypeScript 类型
4. 运行 `make format` 格式化代码
5. 运行类型检查确保一致性

## 会话管理

### 会话生命周期

- **创建/重置**：init 事件时（总是创建新会话或重置已有会话，清空消息历史）
- **复用**：message 事件时（使用已有会话的消息历史）
- **更新**：每次事件交互后（保存新消息和游戏状态）
- **过期**：24 小时无活动后自动清理（Redis TTL）
- **清理**：显式断开连接或超时

### 存储策略

- **内存缓存**：活跃会话的快速访问（`SessionManager._memory_cache`）
- **Redis 持久化**：会话数据持久化，支持重启恢复（`SessionStorage`）
- **混合模式**：优先从内存读取，miss 时从 Redis 加载并缓存到内存

## 架构设计

详细的系统架构说明请参考 [docs/architecture.md](docs/architecture.md)，包括：

- 系统概览
- Backend Game Loop (LangGraph)
- Frontend Streaming & Logic Lock
- Frontend Queue Logic

## 测试

运行测试：
```bash
# Python 测试
pytest tests/

# 前端测试（如果配置了）
cd frontend && npm test
```

## 环境变量

项目使用 `.env` 文件管理环境变量，参考 `.env.example`：

- **LLM 配置**：
  - `DEEPSEEK_API_KEY` / `DOUBAO_API_KEY` - 各提供商的 API Key
  - `OPENAI_API_KEY` - 备用 API Key（向后兼容）
  - `COMMIT_MSG_PROVIDER` - Commit message 生成使用的提供商（默认：deepseek）

- **Redis 配置**：
  - `REDIS_HOST` - Redis 主机（默认：localhost）
  - `REDIS_PORT` - Redis 端口（默认：6379）
  - `REDIS_PASSWORD` - Redis 密码（可选）

- **LangSmith 配置**（可选）：
  - `LANGCHAIN_TRACING_V2` - 启用追踪
  - `LANGCHAIN_API_KEY` - LangSmith API Key
  - `LANGCHAIN_PROJECT` - 项目名称

## 常见问题

### Redis 连接失败

如果 Redis 未运行，会话管理会降级到仅内存模式（重启后丢失）。确保 Redis 服务正在运行：

```bash
docker-compose up -d
```

### 类型检查错误

运行 `make format` 会自动进行类型检查。如果遇到类型错误：

1. 检查 `pyright` 输出
2. 确保所有类型定义同步（protocol.py 和 types.ts）
3. 运行 `python -m pyright` 查看详细错误信息

### SSE 连接问题

如果前端无法接收 SSE 流：

1. 检查后端日志确认请求已接收
2. 检查浏览器控制台的网络请求
3. 确认响应头包含 `text/event-stream`
4. 检查 CORS 配置（开发环境允许所有来源）
