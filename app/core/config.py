from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "VitrineIA API"
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:3000"]
    timezone: str = "America/Sao_Paulo"

    # Privacidade (LGPD): grupos com menos respostas que isso nunca são exibidos
    min_group_size: int = 5

    # IA generativa (opcional). Sem chave, o sistema usa textos gerados por regras.
    ai_api_key: str | None = None
    ai_model: str = "claude-sonnet-5-5"
    ai_timeout_seconds: float = 25.0


settings = Settings()
