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

class ConfigSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None

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

class ConfigBuilder:
    def __init__(self, config_file: str = "mongomigrate.ini"):
        self._config_file = config_file

    def build(self, host: str | None = None, port: int | None = None, database: str | None = None) -> Config:
        """
        Build config based on .ini configuration and provided host, port, and database name.

        Each argument must be complementary i.e. either in .ini or provided (no duplications)
        """

        args_settings = ConfigSettings(host=host, port=port, database=database)

        ini_parser = ConfigParser()
        ini_parser.read(self._config_file)
        ini_settings = ConfigSettings(**ini_parser["mongo-migrate"])

        if not args_settings.is_complementary(ini_settings):
            raise ConfigException(f"Provide host, port, and database either in {self._config_file} or command line arguments")

        final_settings = args_settings + ini_settings

        ret = Config(**final_settings.model_dump())
        return ret