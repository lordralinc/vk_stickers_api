from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    ACCESS_TOKEN: str | None = None
    LOGIN: str | None = None
    PASSWORD: str | None = None
    DB_URL: str | None = None
    VK_API_VERSION: str | None = "5.137"
    VK_API_CLIENT_ID: int = 2274003
    VK_API_CLIENT_SECRET: str = "hHbZxrka2uZ6jB1inYsH"

    model_config = SettingsConfigDict(env_prefix="VSA_", env_file=".env")
