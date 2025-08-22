# build_or_get_vectorstore_qrant.py
"""
- 基于 LangChain 官方 Qdrant 集成改造（使用 QdrantVectorStore）
- 支持本地 in-memory / on-disk / server / cloud 多种部署方式
- 支持 structured table -> payload 构造
- 支持 metadata filter + 自定义 re-ranking（weighting）
"""
from config import *
import os
from pathlib import Path
from typing import List, Dict, Optional, Generator, Any

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredExcelLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from qdrant_client.http import models as qmodels
from langchain_qdrant import QdrantVectorStore, RetrievalMode

# qdrant client 用于 collection 创建与 filter models
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)

# ----------------- 配置 -----------------
SCRIPT_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = SCRIPT_DIR / "knowledge_base"

# ----------------- Loader helpers -----------------
def _is_structured_file(filename: str) -> bool:
    return filename.lower().endswith((".csv", ".xlsx", ".xls"))

def _load_csv_table_as_documents(file_path: str) -> List[Document]:
    docs: List[Document] = []
    filename = os.path.basename(file_path)
    try:
        if file_path.endswith(".csv"):
            loader = CSVLoader(file_path, encoding="utf-8")
            raw_docs = loader.load()
            for idx, rd in enumerate(raw_docs):
                meta = dict(rd.metadata or {})
                meta.update({
                    "source": filename,
                    "row_id": idx,
                    "is_structured": True
                })
                docs.append(Document(page_content=rd.page_content, metadata=meta))
        else:
            excel_loader = UnstructuredExcelLoader(file_path, mode="elements")
            raw = excel_loader.load()
            for idx, rd in enumerate(raw):
                meta = dict(rd.metadata or {})
                meta.update({
                    "source": filename,
                    "row_id": idx,
                    "is_structured": True
                })
                docs.append(Document(page_content=rd.page_content, metadata=meta))
    except Exception as e:
        print(f"Failed to load structured file {file_path}: {e}")
    return docs

def _load_generic_file(file_path: str) -> List[Document]:
    filename = os.path.basename(file_path)
    docs: List[Document] = []
    try:
        if file_path.endswith(".txt"):
            loader = TextLoader(file_path, encoding="utf-8")
            loaded = loader.load()
            for ld in loaded:
                meta = dict(ld.metadata or {})
                meta.update({"source": filename, "is_structured": False})
                docs.append(Document(page_content=ld.page_content, metadata=meta))
        elif file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            loaded = loader.load()
            for ld in loaded:
                meta = dict(ld.metadata or {})
                meta.update({"source": filename, "is_structured": False})
                docs.append(Document(page_content=ld.page_content, metadata=meta))
        elif file_path.endswith((".doc", ".docx")):
            loader = UnstructuredWordDocumentLoader(file_path)
            loaded = loader.load()
            for ld in loaded:
                meta = dict(ld.metadata or {})
                meta.update({"source": filename, "is_structured": False})
                docs.append(Document(page_content=ld.page_content, metadata=meta))
    except Exception as e:
        print(f"Failed to load {file_path}: {e}")
    return docs

# ----------------- Build / load vectorstore -----------------
def build_or_get_vectorstore(
    mode: str = "server",  # "memory", "disk", "server"
    recreate: bool = False,
    source_type: str = "all",
) -> Generator[str, None, Optional[QdrantVectorStore]]:
    """
    mode:
      - memory: QdrantClient(":memory:") => ephemeral (good for dev)
      - disk: QdrantClient(path="/tmp/langchain_qdrant") => on-disk local storage
      - server: remote/local qdrant server via URL (http://localhost:6333) 或 Qdrant Cloud
    """
    # Embedding
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL_NAME)

    # Init client based on mode
    if mode == "memory":
        client = QdrantClient(":memory:")
    elif mode == "disk":
        client = QdrantClient(path=QDRANT_PATH)
    else:
        client = QdrantClient(url=QDRANT_URL)

    # Calculate vector size
    sample_vec = embeddings.embed_query("hello world")
    if isinstance(sample_vec, list) and isinstance(sample_vec[0], list):
        sample_vec = sample_vec[0]
    vector_size = len(sample_vec)

    # Create collection if recreate True
    try:
        existing = None
        try:
            existing = client.get_collection(collection_name=QDRANT_COLLECTION)
        except Exception:
            cols = client.get_collections()
            exists_list = getattr(cols, "collections", []) or []
            if any(c.name == QDRANT_COLLECTION for c in exists_list):
                existing = True

        if recreate:
            try:
                client.delete_collection(collection_name=QDRANT_COLLECTION)
            except Exception:
                pass

        # If collection doesn't exist, create it with VectorParams
        try:
            client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            yield f"Created collection '{QDRANT_COLLECTION}' (size={vector_size})."
        except Exception:
            yield f"Collection '{QDRANT_COLLECTION}' already exists."
            pass
    except Exception as e:
        print(f"Warning while creating/inspecting collection: {e}")

    # Scan and load documents
    docs_to_index: List[Document] = []
    dirs_to_scan = [KNOWLEDGE_BASE_DIR]

    for directory in dirs_to_scan:
        if not os.path.exists(directory):
            yield f"Warning: Directory '{directory}' not found, skipping."
            continue

        yield f"Scanning files in '{directory}'..."
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if os.path.isfile(path):
                if _is_structured_file(filename):
                    loaded = _load_csv_table_as_documents(path)
                else:
                    loaded = _load_generic_file(path)
                
                if loaded:
                    docs_to_index.extend(loaded)
                    yield f"Loaded {len(loaded)} docs from {filename}"

    if not docs_to_index:
        yield "No new documents to index."
    else:
        # Split into chunks
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )
        splits = splitter.split_documents(docs_to_index)
        yield "Splitting documents into chunks..."
        yield f"Total chunks: {len(splits)}"

        # Use LangChain wrapper to create/populate vector store
        if mode == "memory" or mode == "disk":
            vector_store = QdrantVectorStore.from_documents(
                splits,
                embeddings,
                client=client,
                collection_name=QDRANT_COLLECTION,
                retrieval_mode=RetrievalMode.DENSE,
            )
        else:
            vector_store = QdrantVectorStore.from_documents(
                splits,
                embeddings,
                url=QDRANT_URL,
                collection_name=QDRANT_COLLECTION,
                prefer_grpc=True,
                retrieval_mode=RetrievalMode.DENSE,
            )
        yield "Vector store populated."
        return vector_store

    # If no docs indexed, attempt to return wrapper around existing collection
    try:
        if mode == "memory" or mode == "disk":
            vec = QdrantVectorStore(
                client=client,
                collection_name=QDRANT_COLLECTION,
                embedding=embeddings,
            )
        else:
            vec = QdrantVectorStore.from_documents(
                [], embeddings, url=QDRANT_URL, collection_name=QDRANT_COLLECTION
            )
        return vec
    except Exception as e:
        print(f"Failed to build vectorstore wrapper: {e}")
        return None

# ----------------- re-ranking and custom scoring  -----------------
def semantic_search_with_custom_scoring(
    vector_store: QdrantVectorStore,
    query: str,
    top_k: int = 5,
    preferred_sources: Optional[List[str]] = None,
    filter_file_types: Optional[List[str]] = None,
    weight_sim: float = 0.7,
    weight_payload: float = 0.3,
) -> List[dict]:
    """
    使用 vector_store.similarity_search_with_score 并结合自定义 payload 加分重排序。
    修复了过滤器参数问题。
    """
    try:
        # 先获取更大的候选集，然后进行过滤和重排序
        results_with_score = vector_store.similarity_search_with_score(
            query=query,
            k=top_k * 4  # 获取更多候选结果
        )
        print(f"  > 原始检索到 {len(results_with_score)} 个结果。")

        # 如果有文件类型过滤要求，在Python层面进行过滤
        if filter_file_types:
            filtered_results = []
            for doc, score in results_with_score:
                doc_source = doc.metadata.get("source", "")
                if any(ft.strip() in doc_source for ft in filter_file_types):
                    filtered_results.append((doc, score))
            results_with_score = filtered_results
        
        # 自定义加分重排序
        print("\n 步骤3: 正在为每个文档计算自定义分数...")
        scored = []
        for doc, score in results_with_score:
            payload = doc.metadata or {}
            payload_bonus = 0.0
            # 记录加分原因
            bonus_reasons = []
            # 首选来源加分
            if preferred_sources and payload.get("source") in preferred_sources:
                payload_bonus += 0.5

            # 结构化数据加分
            if payload.get("is_structured"):
                payload_bonus += 0.2

            similarity_score = score if score is not None else 0.0

            # 计算综合得分
            combined = weight_sim * (score if score is not None else 0.0) + weight_payload * payload_bonus
            print(f"  - 文档 {doc} | 来源: {payload.get('source', 'N/A')}")
            print(f"    - 原始相似度分 (sim): {similarity_score:.4f}")
            print(f"    - 附加分 (bonus): {payload_bonus:.4f} ({', '.join(bonus_reasons) or '无'})")
            print(f"    - 综合分 (combined): {weight_sim:.2f} * {similarity_score:.4f} + {weight_payload:.2f} * {payload_bonus:.4f} = {combined:.4f}")

            scored.append({"doc": doc, "score": score, "payload": payload, "combined": combined})

        # 按综合得分排序并返回top_k结果
        scored_sorted = sorted(scored, key=lambda x: x["combined"], reverse=True)[:top_k]
        # Informational message; use print instead of yield to avoid making this function a generator
        print(f"Found {str(scored_sorted)} results after custom scoring.")
        return scored_sorted
        
    except Exception as e:
        print(f"Error in semantic_search_with_custom_scoring: {e}")
        return []

# ----------------- 示例运行 -----------------
if __name__ == "__main__":
    # Choose mode
    mode = "server"
    
    # Create the generator instance
    vs_generator = build_or_get_vectorstore(mode=mode, recreate=True, source_type="all")
    
    vs = None
    
    # Manually iterate to capture the return value
    while True:
        try:
            message = next(vs_generator)
            print(message)
        except StopIteration as e:
            vs = e.value
            break

    if vs is None:
        print("Vector store initialization failed.")
        exit(1)
    
    print("\n--- Vector Store Initialized Successfully ---\n")

    # Example search
    preferred = ['Meta backend Developer.pdf']
    file_filters = ['Meta backend Developer.pdf', 'employee_data.csv']

    res = semantic_search_with_custom_scoring(
        vs,
        "what is Deserialization?", 
        preferred_sources=preferred if preferred else None,
        filter_file_types=file_filters,
        top_k=5
    )

    print(f"\nDEBUG: Found {len(res)} results.")
    for r in res:
        print(f"combined={r['combined']:.4f} sim={r['score']:.4f} payload={r['payload']}")