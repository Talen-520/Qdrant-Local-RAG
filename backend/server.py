# server.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import os
import shutil
import asyncio
import functools
from typing import Generator, Any, Optional, Dict, List
from chat import initialize_rag_chain, QdrantRAGChain
from contextlib import asynccontextmanager # 👈 1. Import asynccontextmanager

# --- Global variable ---
# This variable will be initialized at server startup and will hold the RAG chain instance
rag_chain: Optional[QdrantRAGChain] = None

# --- ✨ 2. Define the new lifespan context manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan. The code before `yield` is executed on startup,
    and the code after `yield` is executed on shutdown.
    """
    # --- Startup Logic ---
    global rag_chain
    print("--- The server is starting, initialize the RAG chain... ---")
    # The initialization process is synchronous, so we run it in a thread pool to avoid blocking the event loop
    rag_chain = await run_in_threadpool(initialize_rag_chain)
    if rag_chain is None:
        print("FATAL: RAG Chain failed to initialize. The API will not be functional.")
    else:
        print("--- The RAG Chain has been loaded successfully. The server is ready. ---")
    
    yield # The application runs here
    
    # --- Shutdown Logic ---
    print("--- The server is shutting down. ---")
    # You can add cleanup code here if needed, e.g., closing database connections.
    

# --- RAG and LangChain Imports ---
from langchain_ollama import ChatOllama
from build_or_get_vectorstore_qrant import (
    build_or_get_vectorstore,
    semantic_search_with_custom_scoring,
)

app = FastAPI(
    title="RAG Q&A API",
    description="A FastAPI application for RAG (Retrieval-Augmented Generation) Q&A using Qdrant and Ollama.",
    lifespan=lifespan # 👈 3. Register the lifespan event handler

)

# --- 配置 ---
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
LLM_MODEL_NAME = "gemma3:latest" # Define the model name here

# --- CORS 中间件 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应指定前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic model definitions ---
# (These remain unchanged)
class QueryRequest(BaseModel):
    query: str
    top_k: int = 6
    file_filters: Optional[List[str]] = None # ✅ 新增: 用于接收前端传来的文件名列表
    preferred_sources: Optional[List[str]] = None # <--- 新增
    preferred_model: Optional[str] = None # <--- 新增


class SourceDocument(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float

class AnswerResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]

# --- ✨ 核心改动：异步生成器包装器 ---
# 这个辅助函数可以将一个同步生成器转换为异步生成器
# 它通过在线程池中运行 next() 来防止阻塞事件循环
async def to_async_generator(sync_gen: Generator[Any, None, Any]):
    """
    Wraps a synchronous generator to be used in an async context without blocking.
    """
    # functools.partial 创建一个无参数的函数，用于调用生成器的 next()
    sync_next = functools.partial(next, sync_gen, "__STOP__")
    while (item := await run_in_threadpool(sync_next)) != "__STOP__":
        yield item
        # 短暂暂停，确保其他任务有机会运行，尤其是在快速产生大量日志时
        await asyncio.sleep(0.001)

@app.on_event("startup")
async def startup_event():
    """
    在服务器启动时执行的异步函数。
    它会初始化 RAG Chain 并将其存储在全局变量中。
    """
    global rag_chain
    print("--- Server is starting up, initializing RAG chain... ---")
    # 初始化过程是同步的，所以我们在线程池中运行它以避免阻塞事件循环
    rag_chain = await run_in_threadpool(initialize_rag_chain)
    if rag_chain is None:
        print("FATAL: RAG Chain failed to initialize. The API will not be functional.")
    else:
        print("--- RAG Chain loaded successfully. Server is ready. ---")

# --- API 端点 ---


@app.get("/files")
async def list_files():
    """读取 knowledge_base 文件夹下所有文件"""
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
    try:
        filenames = await run_in_threadpool(os.listdir, BASE_DIR)
        files = [{"name": f, "path": os.path.join(BASE_DIR, f)} for f in filenames]
        return JSONResponse(content=files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法读取文件列表: {e}")

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """上传文件到 knowledge_base"""
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    # 🔴【修正 1】: 将 save_file 从 'async def' 改为 'def'
    # 这个函数包含阻塞的 IO 操作，应该是一个标准的同步函数
    def save_file(uploaded_file: UploadFile):
        # uploaded_file.filename may be None according to type hints; validate and normalize it
        filename = uploaded_file.filename
        if not filename:
            # 返回 400，让客户端知道文件缺少文件名
            raise HTTPException(status_code=400, detail="Uploaded file is missing a filename")
        # 防止路径遍历，确保只使用基础名
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(BASE_DIR, safe_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

    # 并发地在线程池中运行同步的 save_file 函数
    await asyncio.gather(*(run_in_threadpool(save_file, f) for f in files))

    # 返回更新后的文件列表
    return await list_files()


@app.delete("/delete")
async def delete_file(filename: str):
    """删除指定文件"""
    # 安全性检查：防止路径遍历攻击
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
        
    file_path = os.path.join(BASE_DIR, filename)
    
    # 🔴【修正 2】: 将 do_delete 从 'async def' 改为 'def'
    # 它将在线程池中执行，必须是同步函数
    def do_delete():
        if not os.path.exists(file_path):
            # 在同步函数中抛出的 HTTPException 会被 FastAPI 正确捕获
            raise HTTPException(status_code=404, detail="文件不存在")
        try:
            os.remove(file_path)
        except OSError as e:
            # 增加对权限等 OS 错误的捕获
            raise HTTPException(status_code=500, detail=f"删除文件时出错: {e}")

    await run_in_threadpool(do_delete)
    
    # 返回更新后的文件列表
    return await list_files()



@app.get("/embed-stream")
async def embed_stream():
    """
    使用 Server-Sent Events (SSE) 实时流式传输 embedding 过程的日志。
    (已优化为非阻塞)
    """
    async def event_generator():
        try:
            # 1. 调用同步生成器函数，获取生成器对象
            log_generator = build_or_get_vectorstore(
                mode="server", recreate=True, source_type="all"
            )
            
            # 2. 使用我们的异步包装器来迭代，这样就不会阻塞了
            async for log_message in to_async_generator(log_generator):
                # SSE 格式要求： "data: message\n\n"
                yield f"data: {log_message}\n\n"
        
        except Exception as e:
            # 在流中报告错误
            error_message = f"错误：向量化过程中发生意外: {str(e)}"
            yield f"data: {error_message}\n\n"
        
        finally:
            # 3. 发送一个特殊的结束信号
            yield "data: [DONE]\n\n"
            

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/query", response_model=AnswerResponse)
async def ask_question(request: QueryRequest):
    """
    Receives user queries, processes them using the RAG Chain, and returns the answer and sources.
    """
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG Chain is not available or failed to initialize.")
    
    try:
        # The RAG chain's invoke method is synchronous
        # Run it in a thread pool to prevent blocking FastAPI's asynchronous event loop
        print(f"收到的查询: '{request.query}', 文件过滤器: {request.file_filters}") # 增加日志方便调试

        answer, results = await run_in_threadpool(
            rag_chain.invoke, 
            query=request.query, 
            top_k=request.top_k,
            file_filters=request.file_filters,  # ✅ 传递过滤器

        )

        # Format source documents to match the Pydantic response model
        formatted_sources = []
        for res in results:
            doc = res.get("doc")
            if doc:
                formatted_sources.append(
                    SourceDocument(
                        content=doc.page_content,
                        metadata=doc.metadata,
                        score=res.get("combined", res.get("score", 0.0))
                    )
                )

        return AnswerResponse(answer=answer, sources=formatted_sources)

    except Exception as e:
        # Capture any exceptions that may occur in the RAG chain
        print(f"Error during query processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    # 确保使用 --port 5000 启动，以匹配前端配置
    uvicorn.run(app, host="0.0.0.0", port=5000)