"""
Configuration settings for the chatbot backend
Converted from Spring Boot application.properties
"""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Settings:
    """
    Configuration settings for the chatbot backend
    """
    
    # ===== 애플리케이션 기본 설정 =====
    APP_NAME: str = "sllm-pattern"
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "9502"))
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
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_CHAT_TIMEOUT: int = 60  # seconds (성능 최적화)
    OLLAMA_READ_TIMEOUT: int = 60  # seconds (성능 최적화)
    OLLAMA_CONNECTION_TIMEOUT: int = 90  # seconds (성능 최적화)
    OLLAMA_EMBEDDING_TIMEOUT: int = 60  # seconds (임베딩 생성 타임아웃)
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"  # 임베딩 모델
    OLLAMA_EMBEDDING_NUM_CTX: int = 2048  # 임베딩 컨텍스트 길이
    
    # Ollama Chat 옵션 - 성능 최적화 (추가 최적화)
    OLLAMA_CHAT_NUM_CTX: int = 2048  # 컨텍스트 길이 (기본값)
    OLLAMA_CHAT_NUM_PREDICT: int = 1024  # 예측 토큰 수 (기본값)
    OLLAMA_CHAT_TEMPERATURE: float = 0.7  # 창의성 (0.0-1.0)
    OLLAMA_CHAT_TOP_P: float = 0.9  # 핵심 샘플링 (0.0-1.0)
    OLLAMA_CHAT_TOP_K: int = 40  # 상위 K개 토큰 선택
    OLLAMA_CHAT_REPEAT_PENALTY: float = 1.1  # 반복 방지 (1.0-2.0)
    
    # ===== 벡터 데이터베이스 설정 =====
    VECTOR_DB_TYPE: str = "chroma"  # chroma, pinecone, weaviate
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "documents"
    CHROMA_DISTANCE_METRIC: str = "cosine"
    CHROMA_EMBEDDING_FUNCTION: str = "sentence-transformers"
    CHROMA_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_DB_CACHE_SIZE: int = 1000  # 추가된 속성
    VECTOR_DB_EFFECTIVE_CACHE_SIZE: str = "256MB"  # 추가된 속성
    VECTOR_DB_ENABLE_SEQSCAN: bool = False  # 추가된 속성
    VECTOR_DB_RANDOM_PAGE_COST: float = 1.0  # 추가된 속성
    VECTOR_DB_TOP_K: int = 5  # 벡터 검색 상위 K개
    VECTOR_DB_SIMILARITY_THRESHOLD: float = 0.7  # 벡터 유사도 임계값
    VECTOR_DB_EF_SEARCH: int = 200  # HNSW ef_search parameter for better recall
    
    # ===== RAG 설정 =====
    RAG_MAX_DOCS: int = 5  # 검색할 최대 문서 수
    RAG_SIMILARITY_THRESHOLD: float = 0.7  # 유사도 임계값
    RAG_CHUNK_SIZE: int = 1000  # 문서 청크 크기
    RAG_CHUNK_OVERLAP: int = 200  # 청크 간 겹침
    RAG_VECTOR_SEARCH_TOP_K: int = 5  # 벡터 검색에서 반환할 상위 K개 문서
    RAG_VECTOR_SEARCH_SIMILARITY_THRESHOLD: float = 0.7  # 벡터 검색 유사도 임계값
    RAG_CONTEXT_MAX_DOCS: int = 5  # RAG 컨텍스트 최대 문서 수
    RAG_STRICT_MODE_ENABLED: bool = False  # RAG strict mode (requires context)
    RAG_FALLBACK_TO_GENERAL_KNOWLEDGE: bool = True  # Fallback to general knowledge when no context
    RAG_SEARCH_FILTER_DUPLICATES: bool = True  # Filter duplicate documents
    RAG_VECTOR_SEARCH_MIN_RESULTS: int = 1  # Minimum results required
    
    # ===== 캐시 설정 =====
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # 캐시 TTL (초)
    CACHE_MAX_SIZE: int = 1000  # 최대 캐시 항목 수
    
    # ===== 로깅 설정 =====
    LOG_LEVEL: str = "INFO"
    LOG_LEVEL_APP: str = "INFO"  # 추가된 속성
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "chatbot.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # ===== 보안 설정 =====
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-jwt-secret-here")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-here")  # 추가된 속성
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ===== CORS 설정 =====
    CORS_ALLOWED_ORIGINS: list = field(default_factory=lambda: ["http://localhost:8501", "http://127.0.0.1:8501"])
    CORS_ALLOWED_METHODS: list = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    CORS_ALLOWED_HEADERS: list = field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # ===== 모니터링 설정 =====
    METRICS_ENABLED: bool = True
    PROMETHEUS_ENDPOINT: str = "/metrics"
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    
    # ===== 파일 처리 설정 =====
    SUPPORTED_FILE_TYPES: list = field(default_factory=lambda: [".txt", ".pdf", ".docx", ".md", ".json", ".csv"])
    MAX_FILE_SIZE_MB: int = 100
    UPLOAD_DIRECTORY: str = "./uploads"
    
    # ===== 모델 설정 =====
    MODEL_NAME: str = "exaone3.5:2.4b-instruct-q4_K_M"
    MODEL_BASE_URL: str = "http://localhost:11434"
    MODEL_TIMEOUT: int = 60
    
    # ===== LangChain 설정 =====
    LANGCHAIN_TRACING: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "chatbot"
    
    # ===== 프롬프트 설정 =====
    SYSTEM_PROMPT: str = """당신은 도움이 되는 AI 어시스턴트입니다. 사용자의 질문에 정확하고 유용한 답변을 제공하세요."""
    RAG_PROMPT_TEMPLATE: str = """다음 컨텍스트를 사용하여 질문에 답변하세요:

컨텍스트:
{context}

질문: {question}

답변:"""
    
    # ===== 성능 최적화 설정 =====
    ENABLE_GPU: bool = True
    GPU_LAYERS: int = 20
    BATCH_SIZE: int = 512
    MAX_CONCURRENT_REQUESTS: int = 10
    
    # ===== 메모리 관리 설정 =====
    MAX_MEMORY_USAGE: float = 0.8  # 80% 메모리 사용 제한
    MEMORY_CLEANUP_INTERVAL: int = 300  # 5분마다 메모리 정리
    CACHE_CLEANUP_INTERVAL: int = 600  # 10분마다 캐시 정리
    
    # ===== 에러 처리 설정 =====
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: int = 1  # seconds
    CIRCUIT_BREAKER_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60
    
    # ===== 사용자 관리 설정 =====
    USER_SESSION_TIMEOUT: int = 1800  # 30분
    MAX_SESSIONS_PER_USER: int = 10
    SESSION_CLEANUP_INTERVAL: int = 3600  # 1시간마다 세션 정리
    
    # ===== 백업 설정 =====
    BACKUP_ENABLED: bool = True
    BACKUP_INTERVAL: int = 86400  # 24시간마다 백업
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_DIRECTORY: str = "./backups"
    
    # ===== 알림 설정 =====
    NOTIFICATION_ENABLED: bool = False
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_USER: str = ""
    EMAIL_SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    
    # ===== API 제한 설정 =====
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # ===== 외부 API 설정 =====
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY", "")  # 추가된 속성
    GOOGLE_SEARCH_ENGINE_ID: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")  # 추가된 속성
    GOOGLE_SEARCH_TIMEOUT: int = 30  # seconds (구글 검색 API 타임아웃)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")  # 구글 API 키 (별칭)
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "")  # 구글 CSE ID (별칭)
    SEARCH_ENGINE: str = "google"  # 기본 검색 엔진
    
    # ===== 웹소켓 설정 =====
    WEBSOCKET_ENABLED: bool = True
    WEBSOCKET_PING_INTERVAL: int = 30
    WEBSOCKET_PING_TIMEOUT: int = 10
    WEBSOCKET_MAX_CONNECTIONS: int = 100
    
    # ===== 스트리밍 설정 =====
    STREAMING_ENABLED: bool = True
    STREAMING_CHUNK_SIZE: int = 8
    STREAMING_DELAY: float = 0.005
    
    # ===== 품질 관리 설정 =====
    QUALITY_CHECK_ENABLED: bool = True
    MIN_QUALITY_SCORE: float = 0.5
    QUALITY_FEEDBACK_ENABLED: bool = True
    
    # ===== 다국어 지원 설정 =====
    SUPPORTED_LANGUAGES: list = field(default_factory=lambda: ["ko", "en", "ja", "zh"])
    DEFAULT_LANGUAGE: str = "ko"
    AUTO_DETECT_LANGUAGE: bool = True
    
    # ===== 모델별 설정 =====
    # 빠른 응답용 (2.4B 파라미터)
    FAST_MODEL: str = "exaone3.5:2.4b-instruct-q4_K_M"
    
    # 고품질 응답용 (2.4B 파라미터, 고정밀도)
    QUALITY_MODEL: str = "exaone3.5:2.4b-instruct-q8_0"
    
    # 복잡한 작업용 (7.8B 파라미터)
    COMPLEX_MODEL: str = "exaone3.5:7.8b"
    
    # 모델별 최적화된 파라미터 (토큰 수 대폭 증가)
    MODEL_CONFIGS: dict = field(default_factory=lambda: {
        "fast": {
            "model": "exaone3.5:2.4b-instruct-q4_K_M",
            "num_ctx": 2048,
            "num_predict": 2048,  # 512 → 2048로 대폭 증가 (4배)
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
            "num_predict": 3072,  # 1536 → 3072로 증가 (2배)
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
            "num_predict": 6144,  # 3072 → 6144로 증가 (2배)
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
        # Ensure directories exist
        os.makedirs(self.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        os.makedirs(self.UPLOAD_DIRECTORY, exist_ok=True)
        os.makedirs(self.BACKUP_DIRECTORY, exist_ok=True)

# Global settings instance
settings = Settings()