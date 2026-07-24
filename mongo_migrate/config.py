from argparse import Namespace
from configparser import ConfigParser
from dataclasses import dataclass
import enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Self


from mongo_migrate.env import EnvSettings
from mongo_migrate.exceptions import ConfigException

@dataclass
class Config:
    """
    Database configuration
    """
    host: str
    port: int
    database: str
    username: str | None = None
    password: str | None = None

class BaseConfig(BaseModel):
    """
    Base parent class for configurations
    """
    model_config = ConfigDict(extra="ignore")

    @property
    def names(self) -> list[str]:
        """
        List of field names.
        """
        ret = list(self.model_dump().keys())
        return ret

    def is_complementary(self, other: Self) -> bool:
        """
        Check if given configuration is complementary.

        Complementary means that null fields of given config are not null in current one,
            and vice versa.
        """
        other_model = other.model_dump()
        for field_name, field_value in self.model_dump().items():
            other_value = other_model[field_name]
            field_is_complementary = (field_value is None) ^ (other_value is None)
            if not field_is_complementary:
                return False

        return True

    def __add__(self, other):
        """
        Combine two configurations.

        Null fields take value of other, non-null stay as is.
        """
        other_model = other.model_dump()
        args = {
            field_name: field_value or other_model[field_name]
            for field_name, field_value in self.model_dump().items()
        }
        ret = self.__class__(**args)
        return ret


class DBConfig(BaseConfig):
    """
    Settings for database configuration
    """
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None


class MigrationConfig(BaseConfig):
    """
    Migrations configuration.
    """
    migrations: Optional[str] = Field(None, description="Migrations folder name")


class ConfigType(str, enum.Enum):
    """
    Configuration type.

    Value corresponds to section name in .ini file.
    """
    database = "database"
    migrations = "migrations"


class ConfigClass(enum.Enum):
    database = DBConfig
    migrations = MigrationConfig

    @classmethod
    def from_config_type(cls, config_type: ConfigType):
        return cls[config_type.name]


class ConfigBuilder:
    """
    Configuration builder.

    Combines provided argparser arguments with .ini configuration to construct final configuration.
    """
    def __init__(self, config_file: str):
        self._config_file = config_file

        self._ini_parser = ConfigParser()
        self._ini_parser.read(self._config_file)

    def build(self, config_type: ConfigType, args: Namespace | None) -> BaseConfig:
        """
        Build complete configuration of given type based on argparse arguments and .ini configuration.

        Each argument must be complementary i.e. either in .ini or argparse (no duplications)
        """
        ini_config = self._build_ini_config(config_type)
        args_config = self._build_args_config(config_type, args)

        if not args_config.is_complementary(ini_config):
            raise ConfigException(f"Provide {', '.join(ini_config.names)} either in .ini or command line arguments")

        final_config = args_config + ini_config
        return final_config

    def _build_ini_config(self, config_type: ConfigType) -> BaseConfig:
        """
        Build configuration of given type based on .ini parser values
        """
        init_args = self._ini_parser[config_type.value] if config_type.value in self._ini_parser.sections() else {}
        config_class = ConfigClass.from_config_type(config_type).value
        ret = config_class(**init_args)
        return ret
    
    def _build_args_config(self, config_type: ConfigType, args: Namespace | None) -> BaseConfig:
        """
        Build configuration of given type based on argparse arguments
        """
        init_args = {} if args is None else vars(args)
        config_class = ConfigClass.from_config_type(config_type).value
        ret = config_class(**init_args)
        return ret


class ConfigManager:
    """
    Manager for DB and migration configurations.

    Includes:
    - Builders for database and migration configurations based on .ini configuration file.
    - Environemnt settings
    - Getters for database Config and migrations foldername.
    """
    def __init__(self, config_file: str = "mongomigrate.ini"):
        self._config_file = config_file

        self._config_builder = ConfigBuilder(self._config_file)

    def get_config(self, args: Namespace | None) -> Config:
        """
        Build database config.
        
        Get Config based on .ini configuration and provided argparse arguments.
        Get username and password, if any, from environment.
        """
        db_config = self._config_builder.build(ConfigType.database, args)
        env_settings = EnvSettings()
        ret = Config(**(db_config.model_dump() | env_settings.model_dump()))

        return ret

    def get_migrations(self, args: Namespace | None) -> str:
        """
        Get migrations folder name based on .ini configuration and provided name.

        Either one or other must be provided.
        """
        migration_config = self._config_builder.build(ConfigType.migrations, args)
        return migration_config.migrations