# 🤖 智慧环卫 BI 数据分析 Agent (Smart Sanitation BI Agent)

## 📖 项目背景

本项目源自真实的**“智慧城市环卫综合调度管控 SaaS 平台”**业务需求。在企业日常运营中，文职人员与管理层往往需要频繁查询多维度的数据报表（如项目数量分布、预算金额对比、企业性质占比等）。传统的固定报表开发周期长，且无法满足灵活多变的下钻分析需求。

本项目旨在构建一个基于大语言模型（LLM）的智能 BI 助手。它能够精准理解自然语言意图，将其转化为符合企业级红线规范的 SQL 语句，查询 MySQL 数据库，并自动按需生成动态 ECharts 可视化图表，极大降低了非技术人员的数据获取门槛。

## ✨ 核心特性 (Features)

目前项目已完成核心链路的开发，具备以下工业级特性：

- **🧠 底层状态机编排 (LangGraph State Machine)**
  - 摒弃了高层黑盒封装，基于 `StateGraph` 手写底层节点（Nodes）与条件边（Conditional Edges），实现对 Agent 工作流的完全掌控。
- **💾 混合记忆引擎 (Hybrid Memory System)**
  - **短期记忆**：精准保留最近两轮的原始 SQL 与 JSON 数据结果，确保上下文微调的绝对准确。
  - **长期记忆**：定制 `summarize_node`，当对话超长时自动触发物理裁剪，将历史对话提炼为高密度的业务摘要注入全局提示词。彻底解决多轮对话导致的 Token 爆炸与“大模型失忆”问题。
- **🛡️ 企业级 SQL 护栏 (Guardrails)**
  - 在 Prompt 与解析层设置强约束：强制附加 `DELETED = 0` 逻辑删除条件、限制 `LIMIT` 数量、禁止危险的 `SELECT *` 与函数索引导致的全表扫描，保障生产数据库安全。
- **📊 智能可视化编排 (Tool Calling)**
  - 通过自定义 Tool 向前端输出标准的 `chart_json` 协议，根据数据特征智能选择柱状图 (bar)、折线图 (line) 或饼图 (pie)。
- **⚡ 全链路流式响应 (SSE Streaming)**
  - 基于 FastAPI 的 `StreamingResponse` 实现 Server-Sent Events 流式输出，前端打字机效果实时渲染，提供极致的丝滑交互体验。

## 🛠️ 技术栈 (Tech Stack)

- **大模型基座**: 阿里云 Qwen-Plus (通义千问)
- **AI 编排框架**: LangChain, LangGraph
- **RAG 向量引擎**: HuggingFace (`bge-small-zh-v1.5`), ChromaDB
- **后端 API**: FastAPI, Uvicorn, PyMySQL
- **前端展现**: 原生 HTML5 / JavaScript (Fetch API), Apache ECharts

## 🚀 快速开始 (Quick Start)

### 1. 环境准备

Bash

```
# 克隆项目
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件，填入你的配置：

Ini, TOML

```
DASHSCOPE_API_KEY=你的阿里云大模型秘钥

# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=sanitation_db
```

### 3. 启动服务

Bash

```
# 启动 FastAPI 流式后端服务
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

服务启动后，在浏览器直接双击打开项目中的 `index.html` 即可开始多轮对话分析。

## 🗺️ 未来规划 (Roadmap)

本项目正处于持续迭代中，为进一步适配大型互联网公司的复杂架构，计划进行以下升级：

- [ ] **多智能体架构演进 (Multi-Agent)**: 引入 Supervisor 模式，将当前单体 Agent 拆分为 `Router Agent` (路由)、`SQL Coder Agent` (查库) 与 `Data Analyst Agent` (制图)，实现职责解耦。
- [ ] **高阶 RAG 增强 (Advanced RAG)**: 引入 BGE-Reranker 重排模型，并构建 Few-Shot SQL 历史向量库，提升复杂业务表关联查询的成功率。
- [ ] **持久化会话管理 (Persistence)**: 将基于内存的 `MemorySaver` 替换为 PostgreSQL 或 Redis 存储，支持跨设备的长线历史记录追踪。
- [ ] **微服务网关对接 (Java Integration)**: 梳理接口鉴权规范，为后续接入基于 Spring Boot / RuoYi 等 Java 核心网关做好前置准备。
- [ ] **可观测性 (Observability)**: 接入 LangSmith，实现端到端的 Token 消耗监控与链路追踪。

## 🤝 贡献与交流

欢迎提交 Issue 和 Pull Request！如果你对 AI Agent 开发或后端架构设计感兴趣，也欢迎随时交流。
