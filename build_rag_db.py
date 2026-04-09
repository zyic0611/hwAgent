import os
import shutil
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import MarkdownHeaderTextSplitter

# 0. 杀手锏：执行前强行物理删除旧数据库（彻底解决缓存幽灵）
db_path = "./my_local_rag_db"
if os.path.exists(db_path):
    print(f"🧹 发现旧的数据库缓存，正在物理清理 {db_path} ...")
    shutil.rmtree(db_path)

# 1. 初始化本地向量模型
print("⏳ 正在加载本地开源向量模型...")
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

# 2. 读取你的 Markdown 文件
print("📖 正在读取 knowledge.md 文件...")
try:
    with open("knowledge.md", "r", encoding="utf-8") as f:
        markdown_document = f.read()
except FileNotFoundError:
    print("❌ 致命错误：找不到 knowledge.md 文件，请确保它在这个脚本的同级目录下！")
    exit()

# 3. 核心魔法：按 Markdown 标题自动切割
headers_to_split_on = [
    ("#", "一级分类"),
    ("##", "二级分类"),
]
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
knowledge_chunks = markdown_splitter.split_text(markdown_document)

# 【自检防坑】：确保真的切出了数据！
print(f"🔪 成功将知识库切分为 {len(knowledge_chunks)} 个碎片！")
if len(knowledge_chunks) == 0:
    print("❌ 致命错误：切分结果为空！请检查 knowledge.md 里面是不是没有写 # 标题？")
    exit()

# 4. 存入数据库
print("🚀 正在写入 Chroma 向量库...")
vector_db = Chroma.from_documents(
    documents=knowledge_chunks,
    embedding=embeddings,
    persist_directory=db_path
)
print("✅ 知识库构建完成！\n" + "="*50)

# 5. 立刻就地测试一下！
user_question = "帮我查一下湖南省有哪些项目？"
print(f"👤 测试提问: {user_question}\n")

# k=2 代表捞出最相关的两条
retriever = vector_db.as_retriever(search_kwargs={"k": 2})
retrieved_docs = retriever.invoke(user_question)

print("🎯 RAG 引擎为你精准找出了以下辅助知识：\n")
for i, doc in enumerate(retrieved_docs):
    print(f"--- 知识切片 {i+1} ---")
    # 打印出 metadata，看看它是怎么智能分类的
    print(f"分类溯源: {doc.metadata}")
    print(f"内容: {doc.page_content}\n")