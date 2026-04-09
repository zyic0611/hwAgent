import os
import json
import decimal
import pymysql
import re
from datetime import datetime
from dotenv import load_dotenv

# 1. 核心导入
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.checkpoint.memory import MemorySaver

# LangGraph 底层状态机所需的依赖
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# 加载环境变量
load_dotenv()

# 初始化 RAG
print("⏳ 正在挂载本地外脑 (RAG 引擎)...")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")
vector_db = Chroma(persist_directory="./my_local_rag_db", embedding_function=embeddings)
retriever = vector_db.as_retriever(search_kwargs={"k": 5})
print("✅ 外脑挂载完毕！")


# ==========================================
# 2. 定义状态机数据结构
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    summary: str


# ==========================================
# 3. 核心大模型与 Prompt
# ==========================================
llm = ChatOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="qwen-plus",
    temperature=0
)

system_prompt = """
你是“环卫项目数据分析专家”。你负责编写 MySQL 语句获取数据，并为文职人员生成可读性强的报告。

【核心执行红线 (绝对不可违反)】
1. 逻辑删除：所有查询必须强制包含 `DELETED = 0` 条件。
2. 保护性能：严禁使用 `SELECT *`，仅查询必要字段；所有列表查询必须强制 `LIMIT 10`。
3. 地域查询：地名匹配必须使用 `LIKE '%地名%'`。严禁使用 `=` 等值匹配（例如：用户说“北京”，数据库可能是“北京市”）。
4. 时间查询：严禁在索引字段 Date 上使用函数（如 YEAR(Date)）。必须转换为范围查询，例如：`Date >= '2025-01-01' AND Date < '2026-01-01'`。

【数据库结构 (DDL)】
CREATE TABLE `t_projectinfo` (
  `Id` varchar(50) NOT NULL COMMENT '主键ID',
  `ProjectNo` varchar(255) COMMENT '项目编号',
  `ProjectName` varchar(255) COMMENT '项目名称',
  `Date` datetime COMMENT '发布日期/合同起算基准',
  `Provinces` varchar(50) COMMENT '省份代码',
  `City` varchar(50) COMMENT '城市代码',
  `County` varchar(50) COMMENT '区县代码',
  `ProjectType` varchar(20) COMMENT '项目类别(需查字典)',
  `BudgetAmount` decimal(13,2) COMMENT '预算金额(万元)',
  `ContractsCanBe` decimal(13,2) COMMENT '合同总额(万元)',
  `AnnualAmount` decimal(13,2) COMMENT '年化额(万元)',
  `BidWinningEnterprises` varchar(255) COMMENT '中标企业',
  `EnterprisesType` varchar(10) COMMENT '企业类别(需查字典)',
  `ProjectStatus` int COMMENT '1:招标, 2:中标, 3:废标',
  `DELETED` int COMMENT '0:有效, 1:删除'
) ENGINE=InnoDB;

【执行流程 (必须严格遵守)】
1. 分析意图生成 SQL。若报错则根据错误信息重试。
2. 可视化判断：若结果集包含分类字段和数值指标，且适合对比，必须调用 `generate_chart_config`。
   - 柱状图 (bar)：区域/企业的数据对比。
   - 折线图 (line)：时间趋势分析。
   - 饼图 (pie)：占比分析。
3. 最终回复：必须包含专业的文字解读。
   - 【图表隔离原则】：**只有在本轮**明确调用了 `generate_chart_config` 工具时，才在末尾输出 ```chart_json``` 代码块。如果本轮只是查询明细（未调用图表工具），**绝对禁止**伪造或重复历史记录中的图表代码！
"""


# ==========================================
# 4. 工具定义
# ==========================================
class BusinessEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super(BusinessEncoder, self).default(obj)


@tool
# 工具 查询数据库
def execute_sql_query(sql: str) -> str:
    """查询环卫项目数据库的真实数据，输入为合法 MySQL 语句。"""
    print(f"\n🔍 [Agent 执行 SQL]: {sql}")
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"), charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
            return json.dumps(result, cls=BusinessEncoder, ensure_ascii=False)
    except Exception as e:
        return f"执行报错: {str(e)}。请修正 SQL。"
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()


@tool
# 工具 画图
def generate_chart_config(data_json: str, chart_type: str, title: str, dimension_key: str, metric_key: str) -> str:
    """
    当用户需要通过图表查看数据对比、趋势或占比时，请调用此工具。
    参数说明 (绝对遵守)：
    - data_json: sql工具返回的真实数据JSON字符串
    - chart_type: 必须严格是 'bar'(柱状图), 'line'(折线图), 或 'pie'(饼图) 之一！不能是其他词。
    - title: 图表的标题
    - dimension_key: 作为X轴或分类维度的字段名
    - metric_key: 作为Y轴或统计指标的字段名
    """
    print(f"\n📊 [Agent 组装图表]: {title} ({chart_type})")
    try:
        data = json.loads(data_json)
        if not data: return "数据源为空"

        frontend_spec = {
            "title": title, "type": chart_type,
            "dimension": dimension_key, "metric": metric_key,
            "sourceData": data
        }
        formatted_json = json.dumps(frontend_spec, ensure_ascii=False)
        return f"\n```chart_json\n{formatted_json}\n```\n(系统强制指令：图表数据已就绪，你必须在你的最终回复文字末尾，原样完整地输出上面这段 chart_json 代码块！)"
    except Exception as e:
        return f"图表配置报错: {str(e)}"


tools = [execute_sql_query, generate_chart_config]


# ==========================================
# 5. 构建底层状态机 (Graph Nodes & Edges)
# ==========================================

#节点  大脑思考 拼接短期记忆and长期记忆给llm
def call_model(state: AgentState):
    summary = state.get("summary", "")
    sys_content = f"{system_prompt}\n\n【过去的长期记忆】: {summary}" if summary else system_prompt

    messages = [SystemMessage(content=sys_content)] + state["messages"]
    model_with_tools = llm.bind_tools(tools)
    response = model_with_tools.invoke(messages)

    return {"messages": [response]}


tool_node = ToolNode(tools=tools)

# 节点 当消息太多的时候 总结旧消息 删除旧消息 生成summary
def summarize_conversation(state: AgentState):
    summary = state.get("summary", "")
    messages = state["messages"]

    # 保留最后2条消息，压缩之前的
    messages_to_summarize = messages[:-2]

    # 🌟 核心修复：在让大模型写摘要前，用正则把旧消息里的图表代码强行抠掉，只留文字
    clean_history = []
    for m in messages_to_summarize:
        # 匹配并替换掉 chart_json 代码块，防止污染摘要
        clean_content = re.sub(r'```chart_json\s+(.*?)\s+```', '[此处图表已生成完毕，无需记录]', m.content,
                               flags=re.DOTALL)
        clean_history.append(f"{m.type}: {clean_content}")

    summary_prompt = f"这是之前的摘要: {summary}\n\n请结合以下最新对话更新摘要。" if summary else "请将以下历史对话总结为简短的业务背景摘要。"
    summary_prompt += "重点保留用户的查询意图、地域、时间、核心指标等业务信息，绝对不要包含任何 JSON 或代码块。\n\n"

    # 把“消毒”后的干净对话塞给大模型
    summary_prompt += "\n".join(clean_history)

    response = llm.invoke([HumanMessage(content=summary_prompt)])

    # 物理删除旧消息
    delete_messages = [RemoveMessage(id=m.id) for m in messages_to_summarize]
    print(f"\n🧠 [记忆引擎]: 记录已修剪，新摘要 -> {response.content}")

    return {"summary": response.content, "messages": delete_messages}

# 路由
def route_after_agent(state: AgentState) -> Literal["tools", "summarize_conversation", END]:
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tools"
    # 消息>6 则要清洗一次
    if len(messages) > 6:
        return "summarize_conversation"
    return END


workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("summarize_conversation", summarize_conversation)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", route_after_agent)
workflow.add_edge("tools", "agent")
workflow.add_edge("summarize_conversation", END)

memory = MemorySaver()
agent_executor = workflow.compile(checkpointer=memory)


# ==========================================
# 6. 核心业务函数：供 FastAPI 路由或外部调用
# ==========================================
def run_bi_agent(user_input: str, session_id: str) -> dict:
    print(f"\n👤 [会话 {session_id}] 收到请求: {user_input}")
    config = {"configurable": {"thread_id": session_id}}

    print("🔍 [RAG 正在检索相关知识...]")
    retrieved_docs = retriever.invoke(user_input)
    rag_context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    enriched_user_input = f"【参考业务知识】\n{rag_context}\n\n【用户问题】\n{user_input}"

    result = agent_executor.invoke({
        "messages": [HumanMessage(content=enriched_user_input)]
    }, config=config)

    final_reply = result["messages"][-1].content

    # 解析图表拦截层 (增强版正则，兼容多余空格和换行)
    chart_pattern = r"```chart_json\s+(.*?)\s+```"
    match = re.search(chart_pattern, final_reply, re.DOTALL)

    clean_text = final_reply
    chart_json_obj = None

    if match:
        try:
            chart_json_obj = json.loads(match.group(1))
            clean_text = re.sub(chart_pattern, "", final_reply, flags=re.DOTALL).strip()
        except Exception as e:
            print(f"⚠️ JSON 解析失败: {e}")

    total_tokens = 0
    if hasattr(result["messages"][-1], 'usage_metadata') and result["messages"][-1].usage_metadata:
        total_tokens = result["messages"][-1].usage_metadata.get('total_tokens', 0)

    return {
        "report": clean_text,
        "chart": chart_json_obj,
        "usage": {"total_tokens": total_tokens}
    }


# ==========================================
# 本地测试入口
# ==========================================
if __name__ == "__main__":
    test_question = "帮我分析一下北京2025年有效项目中，各项目类型的数量占比情况？"
    api_response = run_bi_agent(test_question, session_id="test_user_001")

    print("\n🎯 函数返回的结构体结果：\n")
    print(json.dumps(api_response, indent=2, ensure_ascii=False))