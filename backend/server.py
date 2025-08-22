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
rag_chain: Optional[QdrantRAGChain] = None

# --- lifespan context manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan. The code before `yield` is executed on startup,
    and the code after `yield` is executed on shutdown.
    """
    global rag_chain
    print("--- The server is starting, initialize the RAG chain... ---")
    rag_chain = await run_in_threadpool(initialize_rag_chain)
    if rag_chain is None:
        print("FATAL: RAG Chain failed to initialize. The API will not be functional.")
    else:
        print("--- The RAG Chain has been loaded successfully. The server is ready. ---")
    
    yield 
    
    # --- Shutdown Logic ---
    print("--- The server is shutting down. ---")
    

# --- RAG and LangChain Imports ---
from langchain_ollama import ChatOllama
from build_or_get_vectorstore_qrant import (
    build_or_get_vectorstore,
    semantic_search_with_custom_scoring,
)

app = FastAPI(
    title="RAG Q&A API",
    description="A FastAPI application for RAG (Retrieval-Augmented Generation) Q&A using Qdrant and Ollama.",
    lifespan=lifespan
)

# --- 配置 ---
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
LLM_MODEL_NAME = "gemma3:latest" # Define the model name here

# --- CORS 中间件 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic model definitions ---
class QueryRequest(BaseModel):
    query: str
    top_k: int = 6
    file_filters: Optional[List[str]] = None # file type filters, e.g., ["pdf", "docx"]
    preferred_sources: Optional[List[str]] = None 
    preferred_model: Optional[str] = None 


class SourceDocument(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float

class AnswerResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]

# --- 异步生成器包装器 ---
async def to_async_generator(sync_gen: Generator[Any, None, Any]):
    """
    Wraps a synchronous generator to be used in an async context without blocking.
    """
    sync_next = functools.partial(next, sync_gen, "__STOP__")
    while (item := await run_in_threadpool(sync_next)) != "__STOP__":
        yield item
        await asyncio.sleep(0.001)

@app.on_event("startup")
async def startup_event():
    """
    在服务器启动时执行的异步函数。
    它会初始化 RAG Chain 并将其存储在全局变量中。
    """
    global rag_chain
    print("--- Server is starting up, initializing RAG chain... ---")
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


    def save_file(uploaded_file: UploadFile):
        filename = uploaded_file.filename
        if not filename:
            raise HTTPException(status_code=400, detail="Uploaded file is missing a filename")
        safe_filename = os.path.basename(filename)
        file_path = os.path.join(BASE_DIR, safe_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)

    await asyncio.gather(*(run_in_threadpool(save_file, f) for f in files))
    return await list_files()


@app.delete("/delete")
async def delete_file(filename: str):
    """删除指定文件"""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")
        
    file_path = os.path.join(BASE_DIR, filename)

    def do_delete():
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        try:
            os.remove(file_path)
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"删除文件时出错: {e}")

    await run_in_threadpool(do_delete)
    
    return await list_files()



@app.get("/embed-stream")
async def embed_stream():
    """
    使用 Server-Sent Events (SSE) 实时流式传输 embedding 过程的日志。
    (已优化为非阻塞)
    """
    async def event_generator():
        try:
            log_generator = build_or_get_vectorstore(
                mode="server", recreate=True, source_type="all"
            )
            
            async for log_message in to_async_generator(log_generator):
                # SSE 格式要求： "data: message\n\n"
                yield f"data: {log_message}\n\n"
        
        except Exception as e:
            error_message = f"错误：向量化过程中发生意外: {str(e)}"
            yield f"data: {error_message}\n\n"
        
        finally:
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
        print(f"收到的查询: '{request.query}', 文件过滤器: {request.file_filters}")
        answer, results = await run_in_threadpool(
            rag_chain.invoke, 
            query=request.query, 
            top_k=request.top_k,
            file_filters=request.file_filters, 

        )

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
    uvicorn.run(app, host="0.0.0.0", port=5000)