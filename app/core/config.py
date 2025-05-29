from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Bot Configuration
    BOT_TOKEN: Optional[str] = None
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    MINI_APP_URL: str = "http://localhost:8000"
    
    # Game Settings
    SPIN_COST: int = 10
    MAX_GIFT_COST: int = 100
    
    # File Paths
    UPLOAD_DIR: str = "uploads"
    CHARTS_DIR: str = "charts"
    
    # Admin Configuration
    INITIAL_ADMINS: list[str] = ["ablaze_coder", "yordam_42"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
