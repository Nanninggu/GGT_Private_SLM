"""
Configuration settings for the chatbot backend
Converted from Spring Boot application.properties
"""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Settings:
    """Application settings converted from Spring Boot properties"""
    
    # ===== 애플리케이션 기본 설정 =====
    APP_NAME: str = "sllm-pattern"
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))
    API_HOST: str = os.getenv("API_HOST", "localhost")
    
    # ===== 액추에이터/헬스체크 설정 =====
    MANAGEMENT_ENDPOINTS: list = field(default_factory=lambda: ["health", "info", "metrics", "prometheus", "timers"])
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
    ASYNC_REQUEST_TIMEOUT: int = 60  # seconds (프론트엔드와 통일)
    
    # ===== Ollama 설정 =====
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")
    OLLAMA_CHAT_TIMEOUT: int = 60  # seconds (성능 최적화)
    OLLAMA_READ_TIMEOUT: int = 60  # seconds (성능 최적화)
    OLLAMA_CONNECTION_TIMEOUT: int = 90  # seconds (성능 최적화)
    
    # Ollama Chat 옵션 - 성능 최적화 (추가 최적화)
    OLLAMA_CHAT_NUM_CTX: int = 2048  # 컨텍스트 크기 75% 감소 (속도 향상)
    OLLAMA_CHAT_NUM_PREDICT: int = 256  # 응답 길이 대폭 최적화 (87% 감소)
    OLLAMA_CHAT_TEMPERATURE: float = 0.5  # 창의성 감소로 속도 향상
    OLLAMA_CHAT_TOP_P: float = 0.7  # 다양성 감소로 속도 향상
    OLLAMA_CHAT_TOP_K: int = 10  # 토큰 선택 대폭 최적화 (75% 감소)
    OLLAMA_CHAT_REPEAT_PENALTY: float = 1.05  # 반복 방지 최적화
    
    # Ollama Embedding 설정
    OLLAMA_EMBEDDING_MODEL: str = "mxbai-embed-large:latest"
    OLLAMA_EMBEDDING_NUM_CTX: int = 512
    OLLAMA_EMBEDDING_TIMEOUT: int = 60  # seconds (성능 최적화)
    
    # ===== Vector DB 설정 (pgvector) =====
    VECTOR_DB_INITIALIZE_SCHEMA: bool = True
    VECTOR_DB_INDEX_TYPE: str = "HNSW"
    VECTOR_DB_DISTANCE_TYPE: str = "COSINE_DISTANCE"
    VECTOR_DB_DIMENSIONS: int = 1024
    VECTOR_DB_SIMILARITY_THRESHOLD: float = 0.4  # 유사도 임계값 상향 조정 (정확도 향상)
    VECTOR_DB_TOP_K: int = 3  # 검색 문서 수 대폭 감소 (80% 감소)
    
    # ===== 성능 최적화 추가 설정 =====
    VECTOR_DB_QUERY_TIMEOUT: int = 10  # 벡터 검색 타임아웃 (초)
    VECTOR_DB_CONNECTION_POOL_SIZE: int = 5  # 벡터 검색 전용 연결 풀 크기
    VECTOR_DB_PRELOAD_COMMON_QUERIES: bool = True  # 일반적인 쿼리 사전 로드
    
    # HNSW 인덱스 고성능 최적화 파라미터 (추가 최적화)
    VECTOR_DB_EF_CONSTRUCTION: int = 100  # 인덱스 구축 속도 향상 (50% 감소)
    VECTOR_DB_EF_SEARCH: int = 16  # 검색 속도 대폭 향상 (75% 감소)
    VECTOR_DB_M: int = 12  # 메모리 사용량 최적화 (25% 감소)
    
    # PostgreSQL 벡터 최적화 설정
    VECTOR_DB_BATCH_SIZE: int = 100  # 배치 처리 크기
    VECTOR_DB_CONCURRENT_SEARCHES: int = 4  # 동시 검색 수
    VECTOR_DB_CACHE_SIZE: int = 1000  # 결과 캐시 크기
    VECTOR_DB_PRELOAD_INDEX: bool = True  # 인덱스 사전 로드
    VECTOR_DB_ENABLE_SEQSCAN: bool = False  # 인덱스 사용 강제
    VECTOR_DB_RANDOM_PAGE_COST: float = 1.1  # SSD 최적화
    VECTOR_DB_EFFECTIVE_CACHE_SIZE: str = "4GB"  # 캐시 크기
    
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
    RAG_MEMORY_WINDOW_SIZE: int = 3  # 메모리 윈도우 대폭 최적화 (40% 추가 감소)
    RAG_CHUNK_SIZE: int = 600  # 청크 크기 대폭 최적화 (25% 추가 감소)
    RAG_CHUNK_OVERLAP: int = 100  # 오버랩 대폭 최적화 (33% 추가 감소)
    RAG_SEARCH_FILTER_DUPLICATES: bool = True
    RAG_VECTOR_SEARCH_MIN_RESULTS: int = 1  # 최소 결과 수 유지
    RAG_CONTEXT_MAX_DOCS: int = 3  # 컨텍스트 문서 수 대폭 감소 (62% 추가 감소)
    RAG_VECTOR_SEARCH_TOP_K: int = 3  # 검색 문서 수 대폭 감소 (62% 추가 감소)
    RAG_VECTOR_SEARCH_SIMILARITY_THRESHOLD: float = 0.4  # 유사도 임계값 상향 조정 (정확도 향상)
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
    RAG_CONTEXT_MAX_LENGTH: int = 100  # 컨텍스트 길이 대폭 최적화 (50% 추가 감소)
    
    # ===== 웹 검색 엔진 설정 =====
    SEARCH_ENGINE: str = os.getenv("SEARCH_ENGINE", "duckduckgo")  # duckduckgo, google, serpapi
    SEARCH_ENGINE_TIMEOUT: int = 30  # seconds
    
    # ===== Google Custom Search API 설정 =====
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "AIzaSyD9308788888888888888888888888888")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "aaaaa")
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", "AIzaSyD9308788888888888888888888888888")
    GOOGLE_SEARCH_ENGINE_ID: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "aaaaa")
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
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8시간으로 연장
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30일로 연장
    
    # ===== 관리자 설정 =====
    ADMIN_USER_ID: str = "eee65338-086b-457a-8746-b88cceac42a3"  # admin 사용자 ID (actual login ID)
    
    # ===== 기존 설정 유지 =====
    # Model configurations for different types
    MODEL_FAST: str = "exaone3.5:2.4b-instruct-q4_K_M"
    MODEL_QUALITY: str = "exaone3.5:2.4b-instruct-q8_0"
    MODEL_COMPLEX: str = "exaone3.5:7.8b"
    MODEL_NAME: str = "exaone3.5:2.4b"  # Default model
    
    # Model configurations dictionary (제거 - 중복 정의)
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./models/exaone3.5-2.4")
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    MAX_HISTORY: int = 10
    
    # ===== 하이브리드 모델 설정 =====
    # 빠른 응답용 (Q4_K_M 양자화)
    FAST_MODEL: str = "exaone3.5:2.4b"
    # 고품질 응답용 (Q8_0 양자화)
    QUALITY_MODEL: str = "exaone3.5:2.4b-instruct-q8_0"
    # 복잡한 작업용 (7.8B 파라미터)
    COMPLEX_MODEL: str = "exaone3.5:7.8b"
    
    # 모델별 최적화된 파라미터
    MODEL_CONFIGS: dict = field(default_factory=lambda: {
        "fast": {
            "model": "exaone3.5:2.4b-instruct-q4_K_M",
            "num_ctx": 2048,
            "num_predict": 256,
            "temperature": 0.5,
            "top_p": 0.7,
            "top_k": 10,
            "repeat_penalty": 1.05,
            "description": "⚡ 초고속 응답 (1.6GB, Q4_K_M)",
            "use_case": "일반적인 질문, 초고속 응답이 필요한 경우"
        },
        "quality": {
            "model": "exaone3.5:2.4b-instruct-q8_0",
            "num_ctx": 8192,
            "num_predict": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "description": "🎯 고품질 응답 (2.8GB, Q8_0)",
            "use_case": "정확한 답변이 필요한 경우, 창의적 작업"
        },
        "complex": {
            "model": "exaone3.5:7.8b",
            "num_ctx": 16384,
            "num_predict": 2048,
            "temperature": 0.8,
            "top_p": 0.95,
            "top_k": 50,
            "repeat_penalty": 1.15,
            "description": "🧠 복잡한 작업 (4.8GB, 7.8B 파라미터)",
            "use_case": "복잡한 추론, 창의적 글쓰기, 전문적 분석"
        }
    })
    
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
        # No longer needed since we use default_factory
        pass

settings = Settings()
