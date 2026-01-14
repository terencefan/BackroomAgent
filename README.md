# Backroom Agent

Backroom Agent 是一个基于 LangGraph 的后室（The Backrooms）文字冒险游戏系统。它结合了即兴叙事、RAG（检索增强生成）和游戏状态管理，提供沉浸式的后室探索体验。

## 项目架构

项目由三个主要部分组成：

1.  **Agent Core (`backroom_agent/`)**: 也就是 "Game Master" 逻辑。使用 LangGraph 构建，包含主 Agent 和多个专门的 Subagent（Level, Event, Suggestion）。
2.  **Backend (`backroom_agent/server.py`)**: 一个轻量级的 FastAPI 服务，为前端提供 SSE（Server-Sent Events）流式接口。
3.  **Frontend (`frontend/`)**: 基于 React + Vite 的复古终端风格用户界面。

## 设计思路

### SSE 长连接优化

项目采用 SSE（Server-Sent Events）流式协议，核心优化思路是**减少数据传输和 LLM token 消耗**：

- **init 事件**：建立连接时发送完整上下文（重建会话）
  - 创建新会话或重置已有会话（清空消息历史）
  - 发送完整上下文（此时消息历史为空，只有初始游戏状态）
  - 处理 init 事件，保存产生的消息到会话

- **message 事件**：只发送增量数据，消息历史由服务器端维护
  - 复用已有会话（使用会话中的消息历史）
  - 只发送 `player_input` + `game_state`（增量），**不包含消息历史**
  - 使用历史消息 + 新消息构建完整上下文
  - 处理 message 事件，保存新消息到会话

**优势**：
1. **减少数据传输**：不再每次发送完整上下文
2. **降低 LLM token 消耗**：后端维护消息历史，只发送增量
3. **更好的用户体验**：SSE 流式响应减少延迟
4. **支持断线重连**：Redis 持久化支持恢复会话

### 会话管理策略

采用**内存 + Redis 混合存储**模式：

- **内存缓存**：活跃会话的快速访问（`SessionManager._memory_cache`）
- **Redis 持久化**：会话数据持久化，支持重启恢复（`SessionStorage`）
- **混合模式**：优先从内存读取，miss 时从 Redis 加载并缓存到内存

**会话生命周期**：
- **创建/重置**：init 事件时（总是创建新会话或重置已有会话，清空消息历史）
- **复用**：message 事件时（使用已有会话的消息历史）
- **更新**：每次事件交互后（保存新消息和游戏状态）
- **过期**：24 小时无活动后自动清理（Redis TTL）

### 前端 DungeonMaster 连接

前端使用 "DungeonMaster" 作为连接管理的业务命名（符合游戏主题），底层使用浏览器原生 API：

- **技术实现**：使用 `fetch` API 接收 SSE 流（`text/event-stream`）
- **业务命名**：代码中命名为 `DungeonMaster` 相关（如 `streamRequestSSE`）
- **连接管理**：每次请求建立新的 SSE 连接（POST 请求返回 SSE 流）

详细的协议说明请参考 [PROTOCOL.md](PROTOCOL.md)，系统架构请参考 [docs/architecture.md](docs/architecture.md)。

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
# 编辑 .env 填入你的 API Key (如 DEEPSEEK_API_KEY, DOUBAO_API_KEY 等)

### 4. 运行后端

```bash
# 启动 API 服务 (默认端口 8000)
python -m backroom_agent.server
# 或者
python backroom_agent/__main__.py
```

### 5. 前端设置与运行

新建一个终端窗口：

```bash
cd frontend
npm install
npm run dev
```

打开浏览器访问 `http://localhost:5173` 即可开始游戏。

## 开发指南

详细的开发信息请参考 [DEVELOP.md](DEVELOP.md)，包括：

- 项目结构说明
- 开发与调试方法
- 代码格式化规范
- Git Hooks 配置
- 数据协议更新流程
- 会话管理实现细节
- 常见问题排查
