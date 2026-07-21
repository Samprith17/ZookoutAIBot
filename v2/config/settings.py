from pydantic import BaseSettings

class Settings(BaseSettings):
    bot_token: str
    database_url: str
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    log_level: str = "INFO"
    instagram_client_id: str = ""
    instagram_client_secret: str = ""
    whatsapp_api_url: str = ""
    whatsapp_api_key: str = ""
    dashboard_secret: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False
