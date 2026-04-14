# 🚀 环卫招标智能体（HWAgent）

> 基于 **LangGraph + RAG + Text-to-SQL** 的企业级数据分析智能体
>  面向「智慧环卫 / 招投标 BI」场景的自动化数据分析与可视化系统

------

## ✨ 项目亮点

- 🧠 **智能问数（NL2SQL）**：自然语言 → 自动生成高质量 SQL

- 📊 **自动图表生成**：支持柱状图 / 折线图 / 饼图自动推荐

- 🔍 

  RAG 检索增强

  ：

  - 业务知识增强（减少幻觉）
  - SQL Few-shot（提升复杂 JOIN 能力）

- 🔄 

  LangGraph 状态机

  ：

  - Agent + Tool 调用闭环
  - 自动错误重试
  - 上下文裁剪（防爆 token）

- 💾 

  记忆系统

  ：

  - 多轮对话隔离（thread_id）
  - 用户点赞 → SQL 进入“黄金库”持续优化

- ⚡ **流式输出（SSE）**：支持前端实时展示

- 🔒 **SQL 安全防护**：强约束只读查询，防止误操作数据库

------

## 🏗️ 系统架构

```
用户问题
   ↓
RAG增强（业务知识 + SQL案例）
   ↓
LangGraph Agent（决策）
   ↓
 ┌───────────────┬────────────────┐
 ↓               ↓                ↓
SQL生成      图表生成        文本分析
 ↓               ↓                ↓
数据库查询     ECharts配置      总结报告
        ↓
    流式返回前端
```

------

## 📂 项目结构

```
.
├── server.py          # FastAPI 服务入口（API层）
├── agent_app.py       # 核心智能体（LangGraph + RAG + Tools）
├── sql_guard.py       # SQL安全校验（只允许SELECT）
├── config.py          # 配置管理（环境变量）
├── knowledge.md       # 业务知识库（RAG数据源）
└── README.md
```

------

## ⚙️ 核心模块说明

### 1. 🧠 Agent 核心（agent_app.py）

- 基于 

  LangGraph

   构建状态机：

  - `agent`：LLM 推理 + 工具调用
  - `tools`：执行 SQL / 生成图表
  - `summarize`：上下文压缩

- 支持：

  - 自动 SQL 生成 + 重试
  - 工具调用路由
  - 长对话摘要

------

### 2. 🔍 RAG 检索增强

- 业务知识库
  - 来源：`knowledge.md`
  - 提供行业背景
- SQL Few-shot
  - 历史高质量 SQL
  - 提升复杂查询稳定性

------

### 3. 📊 工具系统（Tools）

#### ✅ SQL 查询工具

- 自动执行数据库查询
- 返回 JSON 数据
- 内置截断保护

#### ✅ 图表生成工具

- 自动生成前端可用配置（ECharts）
- 支持：
  - bar（对比）
  - line（趋势）
  - pie（占比）

------

### 4. 🔒 SQL 安全机制（sql_guard.py）

- 仅允许：
  - `SELECT`
  - `WITH ... SELECT`
- 禁止：
  - INSERT / UPDATE / DELETE / DROP 等

👉 企业级建议：

- 配合只读数据库账号
- 增加 SQL 审计中间层

------

### 5. 🌐 API 服务（FastAPI）

#### 核心接口

##### 🧾 流式问答

```
POST /api/ask
{
  "question": "北京2025年环卫项目有多少？",
  "session_id": "user_001"
}
```

👉 返回：SSE 流式数据

------

##### 👍 点赞反馈（强化学习）

```
POST /api/feedback/like
```

👉 将 SQL 写入向量库，形成数据飞轮

------

##### ❤️ 健康检查

```
GET /health
GET /ready
```

------

## 🚀 快速启动

### 1️⃣ 安装依赖

```
pip install -r requirements.txt
```

------

### 2️⃣ 配置环境变量

创建 `.env`：

```
# LLM
DASHSCOPE_API_KEY=your_key
LLM_BASE_URL=xxx
LLM_MODEL=xxx

# DB
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=xxx
DB_NAME=xxx

# RAG
LOCAL_RAG_DIR=./rag/local
SQL_RAG_DIR=./rag/sql
```

------

### 3️⃣ 启动服务

```
python server.py
```

或：

```
uvicorn server:app --host 0.0.0.0 --port 8000
```

------

## 🧪 示例能力

### 示例1：数据查询

> 北京今年的环卫项目有多少？

✔ 自动生成 SQL
 ✔ 自动 JOIN 城市表
 ✔ 自动过滤逻辑删除

------

### 示例2：趋势分析

> 最近三年环卫项目数量趋势

✔ 自动生成时间范围 SQL
 ✔ 自动生成折线图

------

### 示例3：占比分析

> 各项目类型占比

✔ 自动 CASE WHEN 映射中文
 ✔ 自动生成饼图

------

## 🧠 技术栈

- **LLM**：OpenAI / DashScope
- **Agent**：LangGraph
- **RAG**：Chroma + HuggingFace Embedding
- **后端**：FastAPI
- **数据库**：MySQL
- **向量数据库**：Chroma
- **流式协议**：SSE

------

## 🔥 项目特色（面试加分点）

- ✅ 完整 Agent 架构（非 toy demo）
- ✅ RAG + SQL 双增强
- ✅ 数据安全防护（生产意识）
- ✅ 流式输出（真实前端可接）
- ✅ 可持续学习（用户反馈闭环）
- ✅ 工程结构清晰（可扩展）

------

## 📈 可扩展方向

-  接入权限系统（多租户）
-  SQL 审计 & 限流
-  多数据源支持（ClickHouse / Hive）
-  前端 BI 面板（React + ECharts）
-  Agent 调度优化（多 Agent 协作）

------

## 🤝 贡献

欢迎提 Issue / PR，一起把这个项目打磨成 **真正可落地的企业级 Agent 系统** 🚀

------

## 📜 License

MIT License

------

## ⭐ Star History

如果这个项目对你有帮助，欢迎点个 ⭐！
