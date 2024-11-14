from dataclasses import dataclass
from typing import List

@dataclass
class Config:
    # App settings
    APP_NAME: str = "Recruitment Analytics"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Data settings
    CACHE_TTL: int = 3600  # 1 hour
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    # Visualization settings
    DEFAULT_WEEKS_TO_SHOW: int = 4
    MAX_WEEKS_TO_SHOW: int = 12
    CHART_HEIGHT: int = 400
    
    # Recruiter settings
    EXCLUDED_RECRUITERS: List[str] = ["Sam Nadler", "Jordan Metzner"]
    
    # Date formats
    DATE_FORMAT: str = "%Y-%m-%d"
    WEEK_FORMAT: str = "%Y-W%V" 