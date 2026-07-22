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
    def build(self, settings_type: SettingsType, parser: ConfigParser) -> BaseSettings:
        """
        Build settings of given type based on .ini parser values
        """
        settings_class = SettingsClass.from_settings_type(settings_type).value
        settings_args = parser[settings_type.value] if settings_type.value in parser.sections() else {}
        ret = settings_class(**settings_args)
        return ret


class SettingsConstructor:
    """
    Settings constructor.

    Combines provided argparser arguments with .ini settings.
    """
    def __init__(self, settings: BaseSettings):
        self._settings = settings

    def get_settings(self, args: Namespace | None) -> BaseSettings:
        """
        Get settings based on argparse arguments and .ini configuration.

        Each argument must be complementary i.e. either in .ini or argparse (no duplications)
        """
        init_args = {} if args is None else vars(args)
        args_settings = self._settings.__class__(**init_args)

        if not args_settings.is_complementary(self._settings):
            raise ConfigException(f"Provide {', '.join(self._settings.names)} either in .ini or command line arguments")

        final_settings = args_settings + self._settings
        return final_settings



class SettingsManager:
    """
    Builder for migration settings.

    Combines provided arguments with .ini settings.
    """
    def __init__(self, config_file: str = "mongomigrate.ini"):
        self._config_file = config_file

        ini_parser = ConfigParser()
        ini_parser.read(self._config_file)

        settings_builder = SettingsBuilder()

        config_settings = settings_builder.build(SettingsType.database, ini_parser)
        self._config_constructor = SettingsConstructor(config_settings)

        migration_settings = settings_builder.build(SettingsType.migrations, ini_parser)
        self._migration_constructor = SettingsConstructor(migration_settings)

    def get_config(self, args: Namespace | None) -> Config:
        """
        Build config based on .ini configuration and provided argparse arguments.
        """
        config_settings = self._config_constructor.get_settings(args)
        ret = Config(**config_settings.model_dump())
        return ret

    def get_migrations(self, args: Namespace | None) -> str:
        """
        Get migrations folder name based on .ini configuration and provided name.

        Either one or other must be provided.
        """
        migration_settings = self._migration_constructor.get_settings(args)
        return migration_settings.migrations