# chat.py
import ollama
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import sys
from typing import List, Tuple, Optional

# 导入修复后的函数
try:
    from build_or_get_vectorstore_qrant import (
        build_or_get_vectorstore,
        semantic_search_with_custom_scoring
    )
except ImportError as e:
    print(f" Import error: {e}")
    print("Please ensure build_or_get_vectorstore_qrant.py is in the same directory.")
    sys.exit(1)

# Check if the specified model exists in the local Ollama installation
def check_model_exists(model_name: str) -> None:
    """
    Checks Ollama status and model availability.
    """
    try:
        # First, get the data. We'll print messages after confirming the status.
        response = ollama.list()
        installed_models = [m.model for m in response.models]
    except Exception as e:
        # Handles connection error
        print(" Error: Could not connect to Ollama.")
        print("Please ensure the Ollama application or server is running.")
        print(f"Connection error details: {e}")
        sys.exit(1)

    if not installed_models:
        print(" No Ollama models found!")
        print("You can pull a model using the command line, for example:")
        print(f"  ollama pull {model_name}")
        sys.exit(1)

    # If models exist, list them
    print(" Installed Ollama models:")
    for model in installed_models:
        print(f"  ✓ {model}")
    print("-" * 40)

    # Check if the specific model is in our list
    if model_name not in installed_models:
        print(f" Error: Model '{model_name}' is not installed.")
        print("Please install it using the following command:")
        print(f"  ollama pull {model_name}")
        sys.exit(1)
    else:
        print(f" Model '{model_name}' is available. Proceeding...")


def format_docs_from_custom_results(results: List[dict]) -> str:
    """
    Format documents from custom scoring results for the prompt.
    """
    if not results:
        return "No relevant documents found."
    
    formatted_docs = []
    for i, result in enumerate(results, 1):
        doc = result["doc"]
        score = result.get("combined", result.get("score", 0))
        
        # Add document metadata for context
        content = doc.page_content.strip()
        metadata_info = ""
        if doc.metadata:
            source = doc.metadata.get("source", "unknown")
            is_structured = doc.metadata.get("is_structured", False)
            doc_type = "Structured Data" if is_structured else "Document"
            metadata_info = f"\n[{doc_type} from: {source}, Relevance: {score:.3f}]"
        
        formatted_docs.append(f"Document {i}:{metadata_info}\n{content}")
    
    return "\n\n" + "="*50 + "\n\n".join(formatted_docs) + "\n" + "="*50


def print_retrieved_docs_custom(results: List[dict]) -> None:
    """
    Print retrieved documents from custom scoring results in a readable format.
    """
    if not results:
        print("🔍 The retriever did not find any relevant documents.")
        return 

    print(f" Found {len(results)} relevant documents:")
    print("=" * 60)
    
    for i, result in enumerate(results, 1):
        doc = result["doc"]
        combined_score = result.get("combined", 0)
        sim_score = result.get("score", 0)
        
        # Clean up the page content by normalizing whitespace
        cleaned_content = ' '.join(doc.page_content.split())
        # Truncate very long content for display
        display_content = cleaned_content[:300] + "..." if len(cleaned_content) > 300 else cleaned_content
        
        print(f"Document {i}:")
        print(f"Content: {display_content}")
        print(f"Combined Score: {combined_score:.4f} | Similarity Score: {sim_score:.4f}")
        
        if doc.metadata:
            source = doc.metadata.get("source", "unknown")
            is_structured = doc.metadata.get("is_structured", False)
            doc_type = " Structured" if is_structured else " Text"
            print(f"   🏷️  {doc_type} | Source: {source}")
        print("-" * 60)


class QdrantRAGChain:
    """
    Custom RAG chain using Qdrant vector store with custom scoring.
    """
    def __init__(self, vectorstore, llm, preferred_sources: Optional[List[str]] = None):
        self.vectorstore = vectorstore
        self.llm = llm
        self.preferred_sources = preferred_sources or []
        # self.filter_file_types = None
        
        self.prompt = ChatPromptTemplate.from_template("""
        You are an expert AI assistant that provides comprehensive answers based on the provided context documents.

        INSTRUCTIONS:
        1. Use the context documents below to answer the question thoroughly
        2. If information is found in multiple documents, synthesize the information coherently
        3. Cite the source documents when possible (e.g., "According to [Document Name]...")
        4. If the information is not available in the context, clearly state this
        5. Provide detailed, well-structured answers
        6. When dealing with technical topics, explain concepts clearly

        CONTEXT DOCUMENTS:
        {context}

        QUESTION: {input}

        ANSWER:
        """)
    # static method to set file filters
    '''
    def set_file_filters(self, filter_types: Optional[List[str]] = None):
        """Set file type filters for document retrieval."""
        self.filter_file_types = filter_types
        if filter_types:
            print(f" File filters set: {', '.join(filter_types)}")
    '''
    def retrieve_documents(self, query: str, top_k: int = 6, file_filters: Optional[List[str]] = None) -> List[dict]:
        """
        Retrieve documents using custom scoring.
        """
        try:
            return semantic_search_with_custom_scoring(
                self.vectorstore,
                query=query,
                top_k=top_k,
                preferred_sources=self.preferred_sources,
                filter_file_types=file_filters,
                weight_sim=0.7,
                weight_payload=0.3
            )
        except Exception as e:
            print(f"Error during document retrieval: {e}")
            return []
    
    def invoke(self, query: str, top_k: int = 6, file_filters: Optional[List[str]] = None) -> tuple[str, list[dict]]:
        """
        完整的 RAG 流程: 检索 -> 格式化 -> 生成答案。
        """
        print(f"正在搜索: '{query}'")
        if file_filters:
            print(f"   - 应用文件过滤器: {file_filters}")
        
        # 将 file_filters 传递给检索方法
        results = self.retrieve_documents(query, top_k, file_filters)
        
        if not results:
            return "根据您选择的文件，我找不到任何相关的文档来回答您的问题。", []
        
        context = format_docs_from_custom_results(results)
        
        try:
            print("正在生成回应...")
            formatted_prompt = self.prompt.format(context=context, input=query)
            response = self.llm.invoke(formatted_prompt)
            return response.content, results
        except Exception as e:
            print(f"生成回应时出错: {e}")
            return f"生成回应时发生错误: {e}", results


def initialize_vectorstore(mode: str = "server", recreate: bool = False) -> Optional[object]:
    """
    Initialize the Qdrant vector store with proper generator handling.
    """
    print("Initializing Qdrant vector store...")
    
    try:
        # Create the generator instance
        vs_generator = build_or_get_vectorstore(
            mode=mode, 
            recreate=recreate, 
            source_type="all"
        )
        
        vs = None
        
        # Manually iterate to capture the return value
        while True:
            try:
                # Get the next yielded message
                message = next(vs_generator)
                print(f" {message}")
            except StopIteration as e:
                # The generator is finished, its return value is in e.value
                vs = e.value
                break
        
        if vs is None:
            print(" Vector store initialization failed.")
            return None
            
        print(" Vector store initialized successfully!")
        return vs
        
    except Exception as e:
        print(f" Error initializing vector store: {e}")
        return None

def initialize_rag_chain(model_name: str = "gemma3:latest") -> Optional[QdrantRAGChain]:
    """
    执行所有检查和初始化步骤，并返回一个配置好的 RAG chain 实例。
    """
    print("=" * 60)
    print(" Initializing RAG Chain for Server...")
    print("=" * 60)

    check_model_exists(model_name)
    
    vectorstore = initialize_vectorstore(mode="server", recreate=False)
    if vectorstore is None:
        print(" Unable to create or load Qdrant vectorstore. Cannot start.")
        return None

    print(f" Initializing LLM: {model_name}")
    try:
        llm = ChatOllama(model=model_name)
    except Exception as e:
        print(f" Error initializing LLM: {e}")
        return None

    preferred_sources = ['Meta backend Developer.pdf']
    # file_filters = ['Meta backend Developer.pdf', 'employee_data.csv']

    rag_chain = QdrantRAGChain(
        vectorstore=vectorstore,
        llm=llm,
        preferred_sources=preferred_sources if preferred_sources else None
    )
    # rag_chain.set_file_filters(file_filters)
    
    print("\n RAG Chain is fully initialized and ready.")
    return rag_chain


def main():
    """
    用于命令行交互的主函数。
    """
    # 【重构】: 调用新的初始化函数
    rag_chain = initialize_rag_chain()
    if not rag_chain:
        sys.exit(1)

    print("\n" + "=" * 60)
    print(" Ready for questions! Type 'quit' to exit.")
    print("=" * 60)

    # 交互式查询循环
    while True:
        try:
            query = input("\n Your question: ").strip()
            if not query:
                continue
            if query.lower() in ['quit', 'exit', 'q']:
                print(" Goodbye!")
                break
            
            print("\n" + "-" * 50)
            
            # 使用 RAG chain 的 invoke 方法
            answer, results = rag_chain.invoke(query)
            
            # 打印检索到的文档
            print_retrieved_docs_custom(results)
            
            print("\n Answer:")
            print("-" * 20)
            print(answer)
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n Goodbye!")
            break
        except Exception as e:
            print(f" An error occurred: {e}")

if __name__ == "__main__":
    main()
