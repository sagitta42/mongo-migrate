"""
    Module: migration_manager.py
    Author: Rahul George
    
    Description:
    This is the core of the mongo_migrate library.
    
    License:
    
    Created on: 14-08-2023
    
"""
import os.path
import re
import sys
from datetime import datetime
from importlib import import_module
from string import Template


import pymongo

from mongo_migrate.exceptions import MongoMigrateException
from mongo_migrate.base_migrate import BaseMigration


class MigrationManager(object):

    NEW_MIGRATION_STRING = Template("""from mongo_migrate.base_migrate import BaseMigration


class Migration(BaseMigration):
    def upgrade(self):
        pass
        
    def downgrade(self):
        pass
        
    def comment(self):
        return '$comment'
    """)

    def __init__(self, config, migrations_path):
        self.config = config        # database config - host, port, db
        self.migrations_path = migrations_path
        self.db = None

    @property
    def all_migrations(self) -> list:
        """
        List of all migrations
        """

        all_migrations = list(filter(lambda x: re.match('\d+_.+\.py', x), os.listdir(self.migrations_path)))
        all_migrations.sort()
        return all_migrations

    def get_all_migration_timestamps(self) -> list[str]:
        """
        Get list of all migration timestamps.
        """
        all_migrations_timestamp = list(map(self.timestamp_from_filename, self.all_migrations))
        return all_migrations_timestamp

    def migrate(self, direction, target_migration):
        """Public method to perform the migration - upgrade or downgrade"""
        if not os.path.exists(self.migrations_path):
            raise MongoMigrateException('Cannot find the migrations path: {}'.format(self.migrations_path))

        if (direction == "upgrade" and target_migration == "head") or (direction == "downgrade" and target_migration == "base"):
            target_migration = self._get_target_migration_timestamp(direction)

        if target_migration not in self.get_all_migration_timestamps():
            raise MongoMigrateException('Cannot find target migration in the migrations')

        migrate_instance = BaseMigration(self.config)
        self.db = migrate_instance.db

        if direction == 'upgrade':
            self._do_upgrade(target_migration)
        else:
            self._do_downgrade(target_migration)

    def create_migration(self, title, message):
        """Create the folder and the template migration file."""
        if not os.path.exists(self.migrations_path):
            os.makedirs(self.migrations_path)

        filename = "{}/{}_{}.py".format(
            self.migrations_path,
            datetime.now().strftime('%Y%m%d%H%M%S'),
            title)

        with open(filename, 'w') as fh:
            fh.write(self.NEW_MIGRATION_STRING.safe_substitute(comment=message))

        print('Migration file created: {}'.format(filename))

    def _do_upgrade(self, target_migration):
        """
        Performs the actual upgrade

        Performs the upgrade from the last migrated version in the database.
        :param target_migration:
        :return:
        """

        if not self._get_migration_history_collection():
            self.db.create_collection('migration_history')

        # Identify the migrations to apply to reach the target
        past_migrations = self._get_migration_history()
        all_migration_timestamps = self.get_all_migration_timestamps()
        if len(past_migrations):
            start_datetime = past_migrations[0]['migration_datetime']
            start_idx = all_migration_timestamps.index(start_datetime) + 1
        else:
            start_idx = 0

        last_idx = all_migration_timestamps.index(target_migration)
        migrations_to_apply = self.all_migrations[start_idx: last_idx+1]

        if not migrations_to_apply:
            print("No new changes to apply")
            return

        # Perform migration by executing the upgrade method from the identified migrations
        sys.path.append(self.migrations_path)
        for migration in migrations_to_apply:
            migration_module = import_module(migration[:-3])
            migration_instance = migration_module.Migration(self.config)
            migration_instance.upgrade()

            self._create_migration_milestone(migration[0:14])

            print("Applied migration: '{}'".format(migration))

        print("Migration completed!")

    def _do_downgrade(self, target_migration):
        """
        Performs the actual rollback operation.

        When rolling back, we cannot initiate the rollback from an intermediate state,
        So, we will always start from the last migrated location in the database.
        :param target_migration:
        :return:
        """
        if not self._get_migration_history_collection():
            raise MongoMigrateException("No past migrations found. Cannot perform rollback")

        # Identify the migrations to apply to reach the target
        past_migrations = self._get_migration_history()
        if not len(past_migrations):
            raise MongoMigrateException("No past migrations found. Cannot perform rollback")

        start_datetime = past_migrations[0]['migration_datetime']
        all_migration_timestamps = self.get_all_migration_timestamps()
        start_idx = all_migration_timestamps.index(start_datetime)

        last_idx = all_migration_timestamps.index(target_migration)
        migrations_to_apply = self.all_migrations[last_idx: start_idx + 1][-1::-1]

        if not migrations_to_apply:
            print("No new changes to apply")
            return

        # Perform migration by executing the downgrade method from the identified migrations
        sys.path.append(self.migrations_path)
        for migration in migrations_to_apply:
            migration_module = import_module(migration[:-3])
            migration_instance = migration_module.Migration(self.config)
            migration_instance.downgrade()

            self._delete_migration_milestone(migration[0:14])

            print("Applied migration: '{}'".format(migration))

        print("Migration completed!")

    def _get_migration_history_collection(self):
        return self.db.list_collection_names(filter={'name': 'migration_history'})

    def _get_migration_history(self, db_filter=None):
        if db_filter is None:
            db_filter = {}
        return list(self.db.migration_history.find(db_filter).sort([('migration_datetime', pymongo.DESCENDING)]))

    @classmethod
    def timestamp_from_filename(cls, filename):
        return filename.split('_')[0]

    def _create_migration_milestone(self, migration_datetime):
        self.db.migration_history.insert_one({'migration_datetime': migration_datetime,
                                              'created_on': datetime.now()})

    def _delete_migration_milestone(self, migration_datetime):
        self.db.migration_history.delete_one({'migration_datetime': migration_datetime})

    def _get_target_migration_timestamp(self, direction):
        """
        Get default target migration.

        Default target migration timestamp is the latest one for upgrade;
            and the first one for downgrade.
        """
        all_migration_timestamps = self.get_all_migration_timestamps()
        if direction == "upgrade":
            ret = all_migration_timestamps[-1]
        else:
            ret = all_migration_timestamps[0]
        return ret