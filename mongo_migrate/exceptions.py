"""
Module: exceptions.py
Author: Rahul George

Description:

License:

Created on: 15-08-2023

"""

from pydantic import BaseModel


class MongoMigrateException(BaseException):
    pass


class ConfigException(BaseException):
    @classmethod
    def error_message(
        cls, header: str, config1: BaseModel, config2: BaseModel | None = None
    ) -> str:
        ret = f"{config1.__class__.__name__} {header}: Provide configuration either in .ini, or .env, or command line arguments!\n{config1}"
        if config2 is not None:
            ret += f"\n{config2}"

        return ret
