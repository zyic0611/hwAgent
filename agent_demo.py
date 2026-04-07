import streamlit as st
import uuid
from dashscope import Application
from http import HTTPStatus

# ================= 核心配置区 (极其重要：安全化处理) =================
# 不要在这里写死 Key！部署时在 Streamlit Cloud 的 Secrets 里配置
try:
    dashscope_api_key = st.secrets["DASHSCOPE_API_KEY"]
    APP_ID = st.secrets["BAILIAN_APP_ID"]
except KeyError:
    st.error("🚨 未找到 API Key 配置，请在 Streamlit 的 Secrets 中进行设置！")
    st.stop()

# ================= 网页 UI 设置 =================
st.set_page_config(page_title="环卫招标智能分析系统", page_icon="📊", layout="wide")
st.title("📊 环卫招投标数据智能分析专家")

# ================= 初始化状态 =================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4()).replace("-", "")

# 渲染历史记录
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ================= 核心交互逻辑 =================
if prompt := st.chat_input("请输入您的数据分析需求，例如：查询25年国企中标总额"):

    # 1. 渲染用户输入
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. 渲染 AI 回答区域
    with st.chat_message("assistant"):
        thought_expander = st.expander("🧠 展开查看 AI 思考与查库过程", expanded=True)
        thought_placeholder = thought_expander.empty()
        answer_placeholder = st.empty()

        full_thought = ""
        full_answer = ""

        try:
            # 调用官方 SDK
            responses = Application.call(
                api_key=dashscope_api_key,
                app_id=APP_ID,
                prompt=prompt,
                session_id=st.session_state.session_id,
                stream=True,
                incremental_output=True,
                has_thoughts=True
            )

            for chunk in responses:
                if chunk.status_code == HTTPStatus.OK:
                    if not chunk.output or (not chunk.output.thoughts and not chunk.output.text):
                        continue

                    # 渲染思考过程
                    if chunk.output.thoughts:
                        for it in chunk.output.thoughts:
                            if it.action_type == 'reasoning':
                                content = str(it.thought) if not isinstance(it.thought, str) else it.thought
                                full_thought += content
                                thought_placeholder.markdown(full_thought + " ▌")

                    # 渲染最终回答
                    if chunk.output.text:
                        thought_placeholder.markdown(full_thought) # 移除思考框的光标
                        full_answer += str(chunk.output.text)
                        answer_placeholder.markdown(full_answer + " ▌")
                else:
                    st.error(f"API请求失败: [{chunk.status_code}] {chunk.message}")
                    break

            answer_placeholder.markdown(full_answer)
            st.session_state.messages.append({"role": "assistant", "content": full_answer})

        except Exception as e:
            st.error(f"请求发生异常: {str(e)}")