# 终端执行安装: pip install fastapi uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from starlette.middleware.cors import CORSMiddleware

from agent_app import run_bi_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（本地开发用 * 没问题）
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法（包括那个报错的 OPTIONS）
    allow_headers=["*"],
)

# 定义前端传过来的数据格式
class ChatRequest(BaseModel):
    question: str
    session_id: str


# 暴露一个 API 接口给前端调用
@app.post("/api/ask")
async def ask_agent(request: ChatRequest):
    print(f"收到前端问题: {request.question}")

    # 1. 调用你的 LangGraph Agent
    result = run_bi_agent(request.question,request.session_id)

    # 2. 直接把字典返回，FastAPI 会自动帮你转成标准 JSON 发给前端
    # result 应该长这样: {"report": "文字解读...", "chart": {图表配置...}}
    return result


if __name__ == "__main__":
    # 启动服务器，暴露在 8000 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)