from dataclasses import dataclass
from pathlib import Path
from typing import Self

from mongo_migrate.utils import timestamp_from_filename


@dataclass
class Migration:
    filename: str
    previous: Self | None
    next: Self | None

    @property
    def timestamp(self) -> str:
        """ Migration timestamp """
        ret = timestamp_from_filename(self.filename)
        return ret

    @property
    def basename(self) -> str:
        """ Migration file base name (without extension) """
        ret = Path(self.filename).stem
        return ret

class MigrationViewer:
    """
    Migration viewer.

    Facilitates determining relationships between migrations
        such as finding first/last/next/previous migration etc.
    """
    def __init__(self, migration_filenames: list[str]) -> None:
        """
        Populate list of disconnected migrations.
        Connect migrations among each other by establishing previous and next migrations.
        Map migrations to timestamps.
        """
        migration_filenames.sort()

        migrations = [ Migration(filename=filename, previous=None, next=None) for filename in migration_filenames]
        num_migrations = len(migrations)

        for idx, migration in enumerate(migrations):
            previous_migration = None if idx == 0 else migrations[idx-1]
            next_migration = None if idx == num_migrations - 1 else migrations[idx+1]

            migration.previous = previous_migration
            migration.next = next_migration

        self._migrations = migrations

        self._migration_map = {m.timestamp: m for m in self._migrations}
        self._timestamps = list(self._migration_map.keys())

    @property
    def last_migration(self) -> Migration:
        return self._migrations[-1]

    @property
    def first_migration(self) -> Migration:
        return self._migrations[0]

    def has_migration(self, timestamp: str) -> bool:
        """
        Whether migration with given timestamp is present.
        """
        ret = timestamp in self._migration_map
        return ret

    def get_migration(self, timestamp: str) -> Migration:
        """
        Get migration by timestamp.
        """
        ret = self._migration_map[timestamp]
        return ret

    def get_timestamp(self, key: str, reference_timestamp: str | None) -> str | None:
        """
        Get migration timestamp based on keyword and reference timestamp.

        key (str): head/base/+N/-N

        Null reference timestamp means no migrated timestamp (at base)
        """
        if key == "head":
            return self.last_migration.timestamp
        
        if key == "base":
            return None

        if key.startswith("+"):
            if reference_timestamp is None:
                return self.last_migration.timestamp

            next_migration = self._get_next_migration(reference_timestamp, int(key[1:]))
            return next_migration.timestamp

        if key.startswith("-"):
            if reference_timestamp is None:
                return None

            previous_migration = self._get_previous_migration(reference_timestamp, int(key[1:]))
            if previous_migration is None:
                return None
            return previous_migration.timestamp


    def get_migrations_between(self, timestamp_from: str | None, timestamp_to: str | None) -> list[Migration]:
        """
        Get migrations between given timestamps.

        To timestamp is included, from timestamp is not.
            (upgrade or downgrade for from timestamp should not be performed)
        If start/end timestamp is None, first/last timestamp is included.
        """
        migration_from = self.first_migration if timestamp_from is None else self.get_migration(timestamp_from).next
        migration_to = self.last_migration if timestamp_to is None else self.get_migration(timestamp_to)
        timestamps_between = self._get_timestamps_between(migration_from.timestamp, migration_to.timestamp)
        ret = [self._migration_map[timestamp] for timestamp in timestamps_between]
        return ret


    def _get_timestamps_between(self, start_timestamp: str, end_timestamp: str) -> list[str]:
        """
        Get list of timestamps between the given two.

        Both timestamps are included.
        """
        idx_start = self._timestamps.index(start_timestamp)
        idx_end = self._timestamps.index(end_timestamp)
        ret = self._timestamps[idx_start : idx_end + 1]
        return ret


    def _get_next_migration(self, reference_timestamp: str, step: int) -> Migration:
        """
        Get migration given number of steps after reference timestamp.
        """
        if reference_timestamp is None:
            return self.last_migration
        
        reference_migration = self.get_migration(reference_timestamp)
        ret = reference_migration

        for _ in range(step+1):
            next_migration = ret.next
            if next_migration is None:
                return self.last_migration
            ret = next_migration
        return ret

    
    def _get_previous_migration(self, reference_timestamp: str, step: int) -> Migration | None:
        """
        Get migration given number of steps before reference timestamp.

        If steps go over the first migration, return None representing base.
        """
        reference_migration = self.get_migration(reference_timestamp)
        ret = reference_migration
        
        for _ in range(step):
            previous_migration = ret.previous
            if previous_migration is None:
                return None
            ret = previous_migration
        return ret