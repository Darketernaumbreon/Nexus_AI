
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXUS-AI"
    API_V1_STR: str = "/api/v1"
    
    # DATABASE
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "nexus_ai"
    SQLALCHEMY_DATABASE_URI: str | None = None

    @property
    def DATABASE_URL(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

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

    class Config:
        env_file = ".env"

settings = Settings()
