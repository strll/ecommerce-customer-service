# 电商客服系统 (E-Commerce Customer Service)

基于大语言模型（LLM）的智能电商客服聊天机器人，支持多轮对话、业务流程自动化、知识问答和闲聊天等功能。

## 项目简介

本项目是一个 AI 驱动的电商客服系统，采用前后端分离架构。后端使用 FastAPI + LangChain 集成阿里云通义千问（Qwen）大模型，通过对话引擎实现三轨道对话架构（任务流、知识问答、闲聊天）。前端使用 Vue 3 + Vite 构建现代化聊天界面。

### 核心功能

- **三轨道对话架构**：任务流处理（查订单、查物流、退款等）、知识问答（商品信息、平台规则等）、闲聊天
- **LLM 驱动对话规划**：每轮对话通过大模型进行意图识别和对话规划
- **YAML 可配置业务流程**：业务流通过 YAML 文件声明式定义，支持条件分支和槽位填充
- **多任务中断与恢复**：支持用户在对话中切换意图，暂停当前任务后可恢复
- **槽位填充机制**：多步骤流程通过文本输入、前端对象选择和 API 自动填充等方式收集信息
- **状态持久化**：完整对话状态序列化为 JSON 存储到 MySQL，支持跨会话连续对话
- **知识库检索**：可扩展的知识检索系统，支持 API、FAQ、RAG 等多种提供商
- **澄清引擎**：当意图不明确时，自动生成引导性问题帮助用户澄清

## 技术栈

### 后端

| 技术 | 说明 |
|------|------|
| Python 3.12+ | 运行环境 |
| FastAPI | REST API 框架 |
| Uvicorn | ASGI 服务器 |
| SQLAlchemy 2.0 (async) | ORM / 数据库访问 |
| MySQL + aiomysql | 数据库 |
| LangChain | LLM 集成框架 |
| Jinja2 | Prompt 模板引擎 |
| PyYAML | 流程配置解析 |
| httpx | 异步 HTTP 客户端 |
| Pydantic | 数据校验与配置管理 |
| 阿里云 DashScope | 大模型服务（Qwen-Plus） |

### 前端

| 技术 | 说明 |
|------|------|
| Vue 3 (Composition API) | 前端框架 |
| Vite | 构建工具 |
| Canvas API | 粒子背景动画 |

## 项目结构

```
ecommerce-customer-service/
├── customer-service-backend/         # Python FastAPI 后端
│   ├── pyproject.toml                # 项目配置与依赖
│   ├── .env                          # 环境变量
│   ├── flow_config/                  # YAML 业务流程定义
│   │   ├── user_flows.yml            # 面向用户的业务流
│   │   └── system_flows.yml          # 系统内部流程
│   └── atguigu/                      # 主应用包
│       ├── main.py                   # 入口文件
│       ├── api/                      # FastAPI 接口层
│       │   ├── app.py                # 应用创建与生命周期
│       │   ├── schema.py             # 请求/响应模型
│       │   ├── dependencies.py       # 依赖注入
│       │   └── router/
│       │       └── chat_router.py    # /api/chat 对话接口
│       ├── conf/                     # 配置管理
│       │   └── config.py             # Pydantic 配置
│       ├── domain/                   # 领域模型
│       │   ├── messages.py           # 消息模型
│       │   ├── state.py              # 对话状态模型
│       │   └── contexts.py           # 任务/系统上下文
│       ├── engine/                   # 对话引擎核心
│       │   ├── dialogue_engine.py    # 对话引擎
│       │   └── builder.py            # 引擎构建器
│       ├── infrastructure/           # 基础设施
│       │   ├── database.py           # 数据库连接
│       │   ├── http_client.py        # HTTP 客户端
│       │   └── llm.py                # LLM 初始化
│       ├── models/                   # SQLAlchemy ORM 模型
│       ├── repository/               # 数据仓库层
│       ├── service/                  # 业务服务层
│       ├── plan/                     # LLM 对话规划
│       │   ├── planner.py            # 规划器
│       │   ├── turn_plan.py          # 规划模型
│       │   └── turn_validator.py     # 规划校验器
│       ├── task/                     # 任务/流程执行
│       │   ├── handler.py            # 任务处理器
│       │   ├── command/              # 命令模式（修改状态）
│       │   ├── flow/                 # 流程定义与执行
│       │   └── action/               # 动作执行器
│       │       ├── buitin/           # 内置动作
│       │       └── cutomer/          # 业务动作
│       ├── knowledge/                # 知识问答轨道
│       ├── chitchat/                 # 闲聊天轨道
│       ├── clarify/                  # 澄清子系统
│       └── prompts/                  # Jinja2 Prompt 模板
│           └── jinja2/               # 各类模板文件
├── customer-service-frontend/        # Vue 3 前端
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       └── App.vue                   # 单页聊天应用
└── .claude/                          # Claude AI 配置
```

## 快速开始

### 环境要求

- Python >= 3.12
- MySQL 数据库
- Node.js（前端）
- 阿里云 DashScope API Key

### 后端部署

1. **克隆项目**

```bash
git clone <repo-url>
cd ecommerce-customer-service/customer-service-backend
```

2. **安装依赖**

推荐使用 [uv](https://github.com/astral-sh/uv) 包管理器：

```bash
uv sync
```

或使用 pip：

```bash
pip install -e .
```

3. **配置环境变量**

编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=mysql+aiomysql://user:password@host:3306/db_name

# LLM 配置
DASHSCOPE_API_KEY=your_api_key_here
LLM_MODEL=qwen-plus

# 电商 API 地址
COMMERCE_API_BASE_URL=http://your-commerce-api:18081
```

4. **启动服务**

```bash
python -m atguigu.main
```

或直接使用 uvicorn：

```bash
uvicorn atguigu.api.app:create_app --host 0.0.0.0 --port 8000
```

### 前端部署

```bash
cd customer-service-frontend
npm install
npm run dev
```

前端开发服务器默认运行在 `http://localhost:5173`，API 请求会自动代理到后端 `http://localhost:8000`。

## API 接口

### POST /api/chat

发送对话消息。

**请求体：**

```json
{
  "sender_id": "user_001",
  "message": {
    "type": "text",
    "content": "帮我查一下订单状态"
  }
}
```

**响应：**

```json
{
  "type": "text",
  "content": "您好，请提供您的订单号，我来帮您查询。"
}
```

支持 `text` 和 `object` 两种消息类型，`object` 类型用于前端点击卡片等交互场景。

### GET /api/chat/history

获取指定用户的对话历史。

**参数：** `sender_id` (string) - 用户标识

## 业务流程配置

业务流程通过 YAML 文件定义，位于 `flow_config/` 目录。示例：

```yaml
flows:
  - name: order_status
    description: 查询订单状态
    steps:
      - id: start
        type: start
      - id: collect_order_id
        type: collect
        slots:
          - name: order_id
            required: true
            prompt: "请提供您的订单号"
      - id: lookup
        type: action
        action: lookup_order_status
      - id: end
        type: end
```

目前支持的流程：欢迎引导、订单状态查询、物流查询、退款申请、相似商品推荐、人工转接。

## 系统架构

```
用户消息 → FastAPI → DialogueService
                        ↓
                  DialogueEngine
                   ↙    ↓    ↘
           Plan (LLM规划) → Task / Knowledge / Chitchat
                ↓
          TurnPlanValidator (校验)
                ↓
          TaskHandler (执行)
                ↓
          CommandProcessor (状态变更) + Action (动作执行)
                ↓
          响应返回用户
```

对话引擎采用三轨道架构：
- **任务轨道**（最高优先级）：处理业务流程（查订单、查物流、退款等）
- **知识轨道**：回答信息咨询（商品信息、政策规则等）
- **闲聊天轨道**（最低优先级）：自由对话

每轮对话通过 LLM 进行意图识别和规划，输出 `TurnPlan` 后经校验器验证再执行。

## 对话状态管理

系统维护完整的对话状态，包括：

- **Session**：一次完整的对话会话
- **Turn**：会话中的一轮对话
- **TaskContext**：当前任务上下文（流程、槽位、步骤）
- **FocusedObject**：用户当前聚焦的业务对象（订单、商品等）

状态通过 SQLAlchemy 持久化到 MySQL，支持跨会话恢复。
