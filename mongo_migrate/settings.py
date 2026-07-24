from argparse import Namespace
from configparser import ConfigParser
from dataclasses import dataclass
import enum
from pydantic import BaseModel, ConfigDict
from typing import Optional, Self


from mongo_migrate.exceptions import ConfigException

@dataclass
class Config:
    """
    MigrationManager Config
    """
    host: str
    port: int
    database: str

class BaseSettings(BaseModel):
    """
    Base parent class for settings.
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
        Check if given config settings are complementary.

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
        Combine two config settings.

        Null fields take value of other, non-null stay as is.
        """
        other_model = other.model_dump()
        args = {
            field_name: field_value or other_model[field_name]
            for field_name, field_value in self.model_dump().items()
        }
        ret = self.__class__(**args)
        return ret


class ConfigSettings(BaseSettings):
    """
    Settings for MigrationManager Config
    """
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None


class MigrationSettings(BaseSettings):
    migrations: Optional[str] = None


class SettingsType(str, enum.Enum):
    """
    Type of settings.

    Value corresponds to section name in .ini file.
    """
    database = "database"
    migrations = "migrations"


class SettingsClass(enum.Enum):
    """
    Name of section in .ini corresponding to settings
    """
    database = ConfigSettings
    migrations = MigrationSettings

    @classmethod
    def from_settings_type(cls, settings_type: SettingsType):
        return cls[settings_type.name]


class SettingsBuilder:
    """
    Settings builder.

    Combines provided argparser arguments with .ini configuration to construct final settubgs.
    """
    def __init__(self, config_file: str):
        self._config_file = config_file

        self._ini_parser = ConfigParser()
        self._ini_parser.read(self._config_file)

    def build(self, settings_type: SettingsType, args: Namespace | None) -> BaseSettings:
        """
        Build complete settings of given type based on argparse arguments and .ini configuration.

        Each argument must be complementary i.e. either in .ini or argparse (no duplications)
        """
        ini_settings = self._build_ini_settings(settings_type)
        args_settings = self._build_args_settings(settings_type, args)

        if not args_settings.is_complementary(ini_settings):
            raise ConfigException(f"Provide {', '.join(ini_settings.names)} either in .ini or command line arguments")

        final_settings = args_settings + ini_settings
        return final_settings

    def _build_ini_settings(self, settings_type: SettingsType) -> BaseSettings:
        """
        Build settings of given type based on .ini parser values
        """
        init_args = self._ini_parser[settings_type.value] if settings_type.value in self._ini_parser.sections() else {}
        settings_class = SettingsClass.from_settings_type(settings_type).value
        ret = settings_class(**init_args)
        return ret

    def _build_args_settings(self, settings_type: SettingsType, args: Namespace | None) -> BaseSettings:
        """
        Build settings of given type based on argparse arguments
        """
        init_args = {} if args is None else vars(args)
        settings_class = SettingsClass.from_settings_type(settings_type).value
        ret = settings_class(**init_args)
        return ret


class SettingsManager:
    """
    Settings manager for different types of settings.

    Manages database configuration settings and migration settings.
    """
    def __init__(self, config_file: str = "mongomigrate.ini"):
        self._config_file = config_file

        self._settings_builder = SettingsBuilder(self._config_file)

    def get_config(self, args: Namespace | None) -> Config:
        """
        Get config based on .ini configuration and provided argparse arguments.
        """
        config_settings = self._settings_builder.build(SettingsType.database, args)
        ret = Config(**config_settings.model_dump())
        return ret

    def get_migrations(self, args: Namespace | None) -> str:
        """
        Get migrations folder name based on .ini configuration and provided argparse arguments.
        """
        migration_settings = self._settings_builder.build(SettingsType.migrations, args)
        return migration_settings.migrations