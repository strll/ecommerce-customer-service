# 电商客服系统开发助手

你是电商智能客服系统的开发助手，帮助开发者理解、维护和扩展这个项目。

## 项目概览

这是一个基于 **FastAPI + LangChain + MySQL** 的电商智能客服系统，使用 LLM（通义千问 qwen-plus）进行对话规划和回复生成。

### 技术栈
- **后端**: Python 3.12+, FastAPI, LangChain, SQLAlchemy (async + aiomysql), Pydantic v2, Jinja2
- **LLM**: 阿里云百炼 DashScope（OpenAI 兼容接口），模型 `qwen-plus`
- **前端**: Vue 3 + Vite
- **数据库**: MySQL 8
- **外部依赖**: 电商后台 API（`http://192.168.200.148:18081`）

### 目录结构

```
customer-service-backend/atguigu/
├── main.py              # 入口（uvicorn 启动）
├── api/                 # FastAPI 应用、依赖注入、schema
├── conf/                # 配置（从 .env 读取）
├── domain/              # 领域模型（DialogueState, Session, Turn, TaskContext 等）
├── infrastructure/      # LLM 客户端、HTTP 客户端、DB 引擎
├── models/              # SQLAlchemy ORM 模型
├── repository/          # 数据访问层（对话状态持久化）
├── service/             # 业务服务层（DialogueService）
├── routers/             # API 路由（chat_router）
├── engine/              # 核心对话引擎 + Builder 组装
├── plan/                # LLM 对话规划（TurnPlanner + TurnPlanValidator）
├── prompts/             # Jinja2 模板 + 历史消息构建
├── knowledge/           # 知识问答子系统
├── chitchat/            # 闲聊子系统
├── clarify/             # 意图澄清子系统
├── task/                # 业务任务流引擎
│   ├── command/         # 命令处理（StartFlow/SetSlots/ResumeFlow/CancelFlow）
│   ├── flow/            # 流程定义、加载器、执行器
│   └── action/          # 动作注册、运行器、内置/自定义动作
└── test/                # 测试目录
```

## 请求处理流程

```
HTTP POST /api/chat
  → chat_router.py: 请求转换为 UserMessage
  → dialogue_service.py: 加载 DialogueState，调用引擎
  → dialogue_engine.py: hand_dialogue()
    → 文本消息 → TurnPlanner (LLM) → TurnPlan (task/knowledge/chitchat)
    → TurnPlanValidator: 验证计划
    → 分发到对应 Handler:
       ├── TaskHandler → CommandProcessor → FlowExecutor → ActionRunner
       ├── KnowLedgeHandler → KnowledgeProvider → KnowledgeResponder (LLM)
       └── ChitChatHandler → ChitChatResponder (LLM)
  → dialogue_service.py: 保存状态到 MySQL
  → chat_router.py: ProcessResult → ChatResponse (JSON)
```

## 核心设计模式

### 1. 三轨道对话
每轮对话 LLM 规划器最多输出 3 条轨道，但最终只选取 1 条执行：
- **task**（业务操作）：启动流程、填写槽位、执行动作
- **knowledge**（知识问答）：查询商品、订单、退换货政策等
- **chitchat**（闲聊）：自由对话

### 2. YAML 驱动的流程引擎
业务流程定义在 `flow_config/` 目录：
- `user_flows.yml` — 用户业务流程（查订单、查物流、退款、推荐等）
- `system_flows.yml` — 系统内部流程（任务开始/中断/恢复/取消、信息收集）

### 3. 状态快照持久化
整个 `DialogueState` 序列化为 JSON 存到 MySQL `dialogue_states` 表（`ON DUPLICATE KEY UPDATE`）。

### 4. 命令模式
LLM 输出命令（StartFlow / SetSlots / ResumeFlow / CancelFlow），CommandProcessor 应用到状态上。

## 常用开发任务

### 运行项目
```bash
cd customer-service-backend
# 确保 .env 中配置了 DASHSCOPE_API_KEY 和数据库连接
uv run python -m atguigu.main
```

### 添加新的业务流程
1. 在 `flow_config/user_flows.yml` 中定义流程（steps、slots、links）
2. 如需新动作：在 `task/action/cutomer/` 下创建新的 Action 类
3. 在 `task/action/cutomer/` 的 `__init__.py` 中导出（auto-discover 会自动注册）

### 添加新的知识问答意图
1. 在 `knowledge/intents.py` 的 `KnowledgeIntentId` 中添加意图 ID
2. 创建对应的 `KnowledgeProvider` 实现
3. 在 `knowledge/registry.py` 中注册 provider

### 添加新的 Prompt 模板
在 `prompts/jinja2/` 目录下创建 `.jinja2` 文件，通过 `prompts/loader.py` 加载。

### 修改 LLM 模型
编辑 `infrastructure/llm.py`，修改 `model` 和 `base_url` 参数。

## 重要约定

- **命名风格**: 模块名用英文，注释和文档可以用中文
- **拼写注意**: 代码中存在拼写错误（`buitin` 应为 `builtin`，`cutomer` 应为 `customer`），新增代码时使用正确拼写，修改旧代码时顺便修正
- **异步优先**: 所有 I/O 操作使用 `async/await`
- **Pydantic v2**: 使用 `model_validate` 而非 `parse_obj`，使用 `model_dump` 而非 `dict`
- **状态可变**: `DialogueState` 的方法直接修改自身，不返回新对象