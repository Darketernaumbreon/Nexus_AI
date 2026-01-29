
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXUS-AI"
    API_V1_STR: str = "/api/v1"
    
    # DATABASE
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "nexus_ai"
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI: str | None = None

    @property
    def DATABASE_URL(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # AUTHENTICATION
    # RS256 keys - In production, use file paths or secrets manager.
    # We read them lazily or via a helper to avoid Pydantic field confusion.
    PRIVATE_KEY: str = ""
    PUBLIC_KEY: str = ""

    def model_post_init(self, __context):
        # Override to load keys if they are empty (default behavior for this skeletal)
        # Note: BaseSettings usually loads from env. If env is missing, we load from file.
        if not self.PRIVATE_KEY:
            try:
                with open("private.pem", "r") as f:
                    self.PRIVATE_KEY = f.read()
            except FileNotFoundError:
                pass # Handle gracefully or let it fail later
        
        if not self.PUBLIC_KEY:
            try:
                with open("public.pem", "r") as f:
                    self.PUBLIC_KEY = f.read()
            except FileNotFoundError:
                pass
                
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # REDIS
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None

    @property
    def REDIS_SETTINGS(self):
        from arq.connections import RedisSettings
        return RedisSettings(host=self.REDIS_HOST, port=self.REDIS_PORT, password=self.REDIS_PASSWORD)

    # OPENTOPOGRAPHY & DEM ACQUISITION
    OPENTOPOGRAPHY_API_KEY: str
    DEM_CACHE_DIR: str = "data/dem_cache"
    DEM_BBOX_BUFFER: float = 0.01  # degrees
    DEM_DEFAULT_DATASET: str = "COP30"  # COP30 or SRTMGL1
    
    # DEM CONDITIONING
    CONDITIONED_DEM_CACHE_DIR: str = "data/conditioned_cache"
    
    # FLOW ANALYSIS
    FLOW_ACCUMULATION_THRESHOLD: int = 1000  # cells for channel extraction
    
    # WEATHER DATA (Open-Meteo API)
    WEATHER_CACHE_DIR: str = "data/weather_cache"
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    OPEN_METEO_ARCHIVE_URL: str = "https://archive-api.open-meteo.com/v1"
    WEATHER_API_TIMEOUT: int = 60  # seconds
    WEATHER_MAX_RETRIES: int = 3
    WEATHER_RETRY_DELAY: float = 2.0  # seconds (exponential backoff base)
    
    # GROUND TRUTH DATA (CWC Flood Gauges)
    CWC_BASE_URL: str = "https://ffs.tamcnhp.com"
    GROUND_TRUTH_CACHE_DIR: str = "data/ground_truth_cache"
    CWC_REQUEST_TIMEOUT: int = 30
    CWC_MAX_RETRIES: int = 3
    CWC_RETRY_DELAY: float = 2.0
    
    # TIME-SERIES CLEANING THRESHOLDS
    MAX_WATER_LEVEL_JUMP_MH: float = 3.0  # meters/hour (physical impossibility threshold)
    MAX_GAP_HOURS_INTERPOLATE: int = 6  # interpolate gaps <= 6 hours
    
    # ML ENGINE
    ML_ARTIFACTS_DIR: str = "ml_engine/artifacts"
    ML_TRAINING_DATA_DIR: str = "data/ml_training"
    
    # XGBOOST HYPERPARAMETERS
    XGB_MAX_DEPTH: int = 4
    XGB_LEARNING_RATE: float = 0.05
    XGB_N_ESTIMATORS: int = 200
    XGB_SUBSAMPLE: float = 0.8
    XGB_COLSAMPLE_BYTREE: float = 0.8
    
    # FEATURE ENGINEERING
    LAG_DAYS: list = [1, 2, 3, 5, 7]
    ROLLING_WINDOWS: list = [3, 5, 7]  # days
    
    # TRAINING
    TEST_SIZE: float = 0.2
    RECALL_WEIGHT: float = 2.0  # For F2-score

    class Config:
        env_file = ".env"

settings = Settings()
