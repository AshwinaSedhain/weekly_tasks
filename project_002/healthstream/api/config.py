# Read API settings from environment variables.
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host:     str  = "postgres"
    db_port:     int  = 5432
    db_name:     str  = "healthstream"
    db_user:     str  = "healthstream"
    db_password: str  = "healthstream123"
    api_title:   str  = "Healthstream API"
    api_version: str  = "1.0.0"
    debug:       bool = False

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
