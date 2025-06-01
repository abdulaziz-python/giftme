from pydantic_settings import BaseSettings
from typing import Optional, List

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
    MEDIA_DIR: str = "media"
    
    # Admin Configuration
    ADMIN_USERNAMES: List[str] = ["ablaze_coder", "yordam_42"]
    ADMIN_IDS: List[int] = []
    
    # Security
    SECRET_KEY: str = "default-secret-key-change-in-production"
    
    # Reminder Settings
    REMINDER_DAYS: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields without validation errors

settings = Settings()
