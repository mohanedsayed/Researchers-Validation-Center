from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    redis_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    s3_endpoint_url: str
    s3_bucket_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"

    file_encryption_key: str  # base64-encoded 32-byte key

    ollama_base_url: str = "http://ollama:11434"
    ollama_chunker_model: str = "qwen2.5:7b"

    session_ttl_hours: int = 24
    max_file_size_mb: int = 500
    free_tier_max_pages: int = 20

settings = Settings()
