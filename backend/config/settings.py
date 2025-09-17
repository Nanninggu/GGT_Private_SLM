"""
Configuration settings for the chatbot backend
Converted from Spring Boot application.properties
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    """Application settings converted from Spring Boot properties"""
    
    # ===== 애플리케이션 기본 설정 =====
    APP_NAME: str = "sllm-pattern"
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    API_HOST: str = os.getenv("API_HOST", "localhost")
    
    # ===== 액추에이터/헬스체크 설정 =====
    MANAGEMENT_ENDPOINTS: list = None
    HEALTH_PROBES_ENABLED: bool = True
    
    # ===== 데이터베이스 설정 (PostgreSQL) =====
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:test1234@127.0.0.1:5433/postgres")
    DATABASE_USERNAME: str = os.getenv("DATABASE_USERNAME", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "test1234")
    
    # HikariCP 연결 풀 설정
    DB_POOL_MAX_SIZE: int = 10
    DB_POOL_MIN_IDLE: int = 3
    DB_POOL_CONNECTION_TIMEOUT: int = 30000
    DB_POOL_IDLE_TIMEOUT: int = 600000
    DB_POOL_MAX_LIFETIME: int = 1800000
    DB_POOL_LEAK_DETECTION_THRESHOLD: int = 60000
    
    # ===== 파일 업로드 설정 =====
    MAX_FILE_SIZE: str = "100MB"  # 파일 크기 제한 증가
    MAX_REQUEST_SIZE: str = "100MB"  # 요청 크기 제한 증가
    
    # ===== 서버 성능 설정 =====
    TOMCAT_MAX_THREADS: int = 20
    TOMCAT_MIN_SPARE_THREADS: int = 3
    TOMCAT_MAX_SWALLOW_SIZE: str = "5MB"
    TOMCAT_MAX_HTTP_FORM_POST_SIZE: str = "5MB"
    ASYNC_REQUEST_TIMEOUT: int = 240  # seconds
    
    # ===== Ollama 설정 =====
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")
    OLLAMA_CHAT_TIMEOUT: int = 90  # seconds
    OLLAMA_READ_TIMEOUT: int = 90  # seconds
    OLLAMA_CONNECTION_TIMEOUT: int = 120  # seconds
    
    # Ollama Chat 옵션
    OLLAMA_CHAT_NUM_CTX: int = 8192
    OLLAMA_CHAT_NUM_PREDICT: int = 2048  # 응답 길이 증가
    OLLAMA_CHAT_TEMPERATURE: float = 0.3  # 창의성 증가
    OLLAMA_CHAT_TOP_P: float = 0.9  # 다양성 증가
    OLLAMA_CHAT_TOP_K: int = 40  # 토큰 선택 다양성 증가
    OLLAMA_CHAT_REPEAT_PENALTY: float = 1.05  # 반복 방지 완화
    
    # Ollama Embedding 설정
    OLLAMA_EMBEDDING_MODEL: str = "mxbai-embed-large:latest"
    OLLAMA_EMBEDDING_NUM_CTX: int = 512
    OLLAMA_EMBEDDING_TIMEOUT: int = 90  # seconds
    
    # ===== Vector DB 설정 (pgvector) =====
    VECTOR_DB_INITIALIZE_SCHEMA: bool = True
    VECTOR_DB_INDEX_TYPE: str = "HNSW"
    VECTOR_DB_DISTANCE_TYPE: str = "COSINE_DISTANCE"
    VECTOR_DB_DIMENSIONS: int = 1024
    VECTOR_DB_SIMILARITY_THRESHOLD: float = 0.6
    VECTOR_DB_TOP_K: int = 15
    
    # HNSW 인덱스 최적화 파라미터
    VECTOR_DB_EF_CONSTRUCTION: int = 200
    VECTOR_DB_EF_SEARCH: int = 56
    VECTOR_DB_M: int = 16
    
    # ===== 비동기 작업 설정 =====
    TASK_EXECUTION_CORE_SIZE: int = 6
    TASK_EXECUTION_MAX_SIZE: int = 8
    TASK_EXECUTION_QUEUE_CAPACITY: int = 50
    TASK_EXECUTION_SHUTDOWN_AWAIT_TERMINATION: bool = True
    TASK_EXECUTION_SHUTDOWN_AWAIT_TERMINATION_PERIOD: int = 20  # seconds
    
    # ===== 로깅 설정 =====
    LOG_LEVEL_ROOT: str = os.getenv("LOG_LEVEL_ROOT", "WARN")
    LOG_LEVEL_APP: str = os.getenv("LOG_LEVEL_APP", "INFO")
    LOG_LEVEL_SERVICE: str = os.getenv("LOG_LEVEL_SERVICE", "INFO")
    LOG_LEVEL_OLLAMA: str = os.getenv("LOG_LEVEL_OLLAMA", "INFO")
    LOG_LEVEL_VECTORSTORE: str = os.getenv("LOG_LEVEL_VECTORSTORE", "INFO")
    
    # ===== RAG 설정 =====
    RAG_METADATA_FILTER_ENABLED: bool = False
    RAG_METADATA_BOOST_ENABLED: bool = False
    RAG_RESPONSE_FORMAT: str = "structured"
    RAG_CONTEXT_MIN_FALLBACK_LENGTH: int = 120
    RAG_CONTEXT_DEDUPLICATE: bool = True
    RAG_CONTEXT_APPROX_TOKENS_PER_CHAR: float = 0.30
    RAG_CONTEXT_ENABLE_FALLBACK: bool = True
    
    # ===== LangChain RAG 설정 =====
    RAG_MEMORY_WINDOW_SIZE: int = 10
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_SEARCH_FILTER_DUPLICATES: bool = True
    RAG_VECTOR_SEARCH_MIN_RESULTS: int = 1
    RAG_CONTEXT_MAX_DOCS: int = 15
    RAG_VECTOR_SEARCH_TOP_K: int = 15
    RAG_VECTOR_SEARCH_SIMILARITY_THRESHOLD: float = 0.6
    RAG_SEARCH_EXPANSION_ENABLED: bool = False
    RAG_SEARCH_RERANK_ENABLED: bool = False
    RAG_TECH_SEARCH_ENABLED: bool = False
    RAG_TECH_KEYWORDS_EXPANSION: bool = False
    RAG_SEARCH_EXPAND_QUERY: bool = False
    RAG_STRICT_MODE_ENABLED: bool = False
    RAG_FALLBACK_TO_GENERAL_KNOWLEDGE: bool = False
    RAG_REQUIRE_CONTEXT: bool = True
    RAG_CONTEXT_REQUIRED: bool = True
    RAG_VECTOR_ONLY_MODE: bool = True
    RAG_EXTERNAL_KNOWLEDGE_BLOCKED: bool = True
    RAG_CONTEXT_MAX_LENGTH: int = 300
    
    # ===== Google Custom Search API 설정 =====
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", "your_api_key_here")
    GOOGLE_SEARCH_ENGINE_ID: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "your_engine_id_here")
    GOOGLE_SEARCH_MAX_RESULTS: int = 10
    GOOGLE_SEARCH_TIMEOUT: int = 30  # seconds
    
    # ===== Deep Search 설정 =====
    DEEP_SEARCH_ENABLED: bool = True
    DEEP_SEARCH_MAX_RESULTS: int = 8
    DEEP_SEARCH_INCLUDE_SNIPPETS: bool = True
    DEEP_SEARCH_INCLUDE_METADATA: bool = True
    
    # ===== 정적 리소스 설정 =====
    STATIC_PATH_PATTERN: str = "/static/**"
    
    # ===== JWT 설정 =====
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-2024")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ===== 기존 설정 유지 =====
    MODEL_NAME: str = "exaone3.5:2.4b"
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./models/exaone3.5-2.4")
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    MAX_HISTORY: int = 10
    
    # ===== 한글 응답 설정 =====
    KOREAN_RESPONSE_ENFORCED: bool = True
    KOREAN_SYSTEM_PROMPT: str = """🚨 **중요한 언어 규칙** 🚨
• 반드시 한국어로만 답변하세요. 영어나 다른 언어 사용 금지
• 모든 응답은 한국어 문법과 표현을 사용하세요
• 전문 용어가 필요한 경우 괄호 안에 영어를 병기할 수 있습니다
• 답변의 시작과 끝은 항상 한국어로 하세요

🌟 당신은 지식 풍부한 AI 도우미입니다. 사용자의 질문에 대해 최대한 풍부하고 정확한 한국어 답변을 제공합니다."""
    
    def __post_init__(self):
        """Initialize complex fields after dataclass creation"""
        if self.MANAGEMENT_ENDPOINTS is None:
            self.MANAGEMENT_ENDPOINTS = ["health", "info", "metrics", "prometheus", "timers"]

settings = Settings()
