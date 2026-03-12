from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    app_secret_key: str = "dev-secret-change-in-production"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 9000

    # MongoDB
    mongodb_uri: str = "mongodb://gloria_admin:gloria_secret_dev@localhost:27017"
    mongodb_db_name: str = "gloria_trade"

    # JWT
    jwt_secret_key: str = "jwt-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Data Providers
    alpha_vantage_api_key: str = ""

    # ML
    model_cache_dir: str = "./model_cache"
    prediction_cache_ttl_hours: int = 24

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
