"""
    Module: base_migrate.py
    Author: Rahul George
    
    Description:
        This module will act as the base class for all the migration files.
        It will take care of the database connection.
        The child classes should worry about implementing the actual migration.
    License:
    
    Created on: 15-08-2023
    
"""
import pymongo
from abc import abstractmethod

from pymongo.database import Database

from mongo_migrate.settings import Config


class BaseMigration(object):
    def __init__(self, config: Config):
        client = pymongo.MongoClient(host=config.host, port=config.port)
        self.db: Database = client[config.database]

    @abstractmethod
    def upgrade(self):
        """Implement this in the child classes"""
        pass

    @abstractmethod
    def downgrade(self):
        """Implement this in the child classes"""
        pass

    @abstractmethod
    def comment(self):
        """Implement this in the child classes"""
        pass

