from pydantic_settings import BaseSettings
from typing import Optional, List, Union

class Settings(BaseSettings):
    BOT_TOKEN: str
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"
    
    DATABASE_URL: str = "postgres://avnadmin:AVNS_c7_OGHEYa11zfgd_o23@pg-1c1548ec-ablaze-coder.e.aivencloud.com:18321/defaultdb?sslmode=require"
    REDIS_URL: str = "redis://localhost:6379"
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    MINI_APP_URL: str
    
    SECRET_KEY: str
    
    SPIN_COST: int = 50
    MAX_GIFT_COST: int = 200
    
    ADMIN_USERNAMES: List[str] = ["ablaze_coder", "yordam_42"]
    ADMIN_IDS: List[int] = []
    
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    
    CHARTS_DIR: str = "charts"
    
    class Config:
        env_file = ".env"

settings = Settings()
