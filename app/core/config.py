import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Restaurante API"
    PROJECT_DESCRIPTION: str = "API para gerenciamento de restaurante"
    PROJECT_VERSION: str = "1.0.0"

    DB_HOST: str = "nozomi.proxy.rlwy.net"
    DB_PORT: str = "36651"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "FqpunTuoXwljoBssZoEwIKZREZWveopP"
    DB_NAME: str = "railway"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    RELOAD: bool = os.getenv("RELOAD", "True").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "low_salary")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    @property
    def DATABASE_URL(self) -> str:
        print(f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

settings = Settings()
