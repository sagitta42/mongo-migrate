from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: Optional[str] = Field(default=None, alias="MONGO_HOST")
    port: Optional[int] = Field(default=None, alias="MONGO_PORT")
    username: Optional[str] = Field(default=None, alias="MONGO_INITDB_ROOT_USERNAME")
    password: Optional[str] = Field(default=None, alias="MONGO_INITDB_ROOT_PASSWORD")
    database: Optional[str] = Field(default=None, alias="MONGO_DB_NAME")
    migrations: Optional[str] = Field(default=None, description="Migrations folder")
