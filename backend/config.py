# Configuration settings for the backend application
QDRANT_URL = "http://localhost:6333"
QDRANT_PATH = "/tmp/langchain_qdrant"
QDRANT_COLLECTION = "knowledge_base"
EMBEDDING_MODEL_NAME = "nomic-embed-text:latest"

CHUNK_SIZE = 512
CHUNK_OVERLAP = 102