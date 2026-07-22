from configparser import ConfigParser
from dataclasses import dataclass
from pydantic import BaseModel, ConfigDict
from typing import Optional, Self


from mongo_migrate.exceptions import ConfigException

@dataclass
class Config:
    host: str
    port: int
    database: str

class BaseSettings(BaseModel):
    """
    Base parent class for settings.
    """

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
    model_config = ConfigDict(extra="ignore")

    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None

class MigrationSettings(BaseSettings):
    migrations: Optional[str] = None


class SettingsBuilder:
    """
    Builder for migration settings.

    Combines provided arguments with .ini settings.
    """
    def __init__(self, config_file: str = "mongomigrate.ini"):
        self._config_file = config_file

        ini_parser = ConfigParser()
        ini_parser.read(self._config_file)

        self._config_settings = ConfigSettings(**ini_parser["database"])
        self._migration_settings = MigrationSettings(**ini_parser["migrations"])

    def build_config(self, host: str | None = None, port: int | None = None, database: str | None = None) -> Config:
        """
        Build config based on .ini configuration and provided host, port, and database name.

        Each argument must be complementary i.e. either in .ini or provided (no duplications)
        """

        args_settings = ConfigSettings(host=host, port=port, database=database)

        if not args_settings.is_complementary(self._config_settings):
            raise ConfigException(f"Provide {', '.join(args_settings.names)} either in {self._config_file} or command line arguments")

        final_settings = args_settings + self._config_settings

        ret = Config(**final_settings.model_dump())
        return ret

    def get_migrations(self, migrations: str | None = None) -> str:
        """
        Get migrations folder name based on .ini configuration and provided name.

        Either one or other must be provided.
        """
        args_settings = MigrationSettings(migrations=migrations)

        if not args_settings.is_complementary(self._migration_settings):
            raise ConfigException(f"Provide {args_settings.names} either in {self._config_file} or command line arguments")

        final_settings = args_settings + self._migration_settings

        return final_settings.migrations       