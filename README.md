# Welcome to mongo-migrate

Migrate Mongodb seamlessly using Python and mongo-migrate. 

MongoDB is a schemaless database but most of the time the data that you store in the database will end up have a loose schema. 
The Python library is aimed to solve the below problem scenarios: 
  1. As your project grows, the schema also changes and grows with it. When you want to go back to a specific version of the code and run that version. Most of the time, you do not remember the database schema used with the particular version of code. This is where creating a migration file and keeping it under version control along with your code helps. You can retrace the steps to that particular version of the schema. 
  2. Lastly, even if your code base is in another language, you can use the Mongo-migrate package to create migrations. Exactly for this reason, mongo-migrate is coming out of the box with a lot of subcommands. 

You can read my the detailed article [here](https://rahulgeorge.hashnode.dev/migrate-mongodb-data-seamlessly-with-mongo-migrate-and-python)

The mongo-migrate library can create migrations, and perform upgrade and downgrade operations.

### Installation

    pip install mongo-migrate

### Usage

    usage: mongo-migrate [-h] {create,upgrade,downgrade} ...
    
    positional arguments:
      {create, upgrade, downgrade}
        create              create a new migration
        upgrade             upgrade the database to the specific migration
        downgrade           downgrade the database to the specific migration
    
    optional arguments:
      -h, --help            show this help message and exit

## Key Features

### Create Migrations

    usage: mongo-migrate create [-h] [--host HOST] [--port PORT] [--database DATABASE] [--migrations MIGRATIONS] --message MESSAGE [--title TITLE]
    
    options:
      -h, --help            show this help message and exit
      --host HOST           the database host
      --port PORT           the database port
      --database DATABASE   the database name
      --migrations MIGRATIONS
                            provide the folder to store migrations. By default creates migrations/
      --message MESSAGE     short message that will be saved as a comment inside the migration file
      --title TITLE         short title that will be used in the file name. Default: contents of --message

An example command would look like this:
    
    mongo-migrate create --host 127.0.0.1 --port 27017 --database test --message 'first migration'


### Upgrade database

    usage: mongo-migrate upgrade [-h] [--host HOST] [--port PORT] [--database DATABASE] [--migrations MIGRATIONS] [--upto UPTO] [--username USERNAME] [--password PASSWORD] [target_migration]
    
    positional arguments:
      target_migration      target migration timestamp or keyword (options: head, +N)
    
    options:
      -h, --help            show this help message and exit
      --host HOST           the database host
      --port PORT           the database port
      --database DATABASE   the database name
      --migrations MIGRATIONS
                            provide the folder to store migrations. By default creates migrations/
      --upto UPTO           target migration timestamp or keyword (options: head, +N)
      --username USERNAME   the database user
      --password PASSWORD   the database user

The positional argument `target_migration` is an alternative to the keyword argument `--upto` (the latter would override the former, at least one is required); `--upto` is remaining for backwards compatibility

Example commands would look like this:
    
    mongo-migrate upgrade 20230815092813 --host 127.0.0.1 --port 27017 --database test
    mongo-migrate upgrade head --host 127.0.0.1 --port 27017 --database test
    mongo-migrate upgrade +3 --host 127.0.0.1 --port 27017 --database test --username user42 --password abc123

head: upgrade to and including the latest migration

+N: upgrade N next migrations

### Downgrade database

    usage: mongo-migrate downgrade [-h] [--host HOST] [--port PORT] [--database DATABASE] [--migrations MIGRATIONS] [--upto UPTO] [--username USERNAME] [--password PASSWORD] [target_migration]
    
    positional arguments:
      target_migration      target migration timestamp or keyword (options: base, -N)
    
    options:
      -h, --help            show this help message and exit
      --host HOST           the database host
      --port PORT           the database port
      --database DATABASE   the database name
      --migrations MIGRATIONS
                            provide the folder to store migrations. By default creates migrations/
      --upto UPTO           target migration timestamp or keyword (options: base, -N)
      --username USERNAME   the database user
      --password PASSWORD   the database user

Example commands would look like this:
    
    mongo-migrate downgrade 20230815092813 --host 127.0.0.1 --port 27017 --database test
    mongo-migrate downgrade base --host 127.0.0.1 --port 27017 --database test
    mongo-migrate downgrade -3 --host 127.0.0.1 --port 27017 --database test --username user42 --password abc123

base: downgrade all migrations

-N: downgrade this and N-1 previous migrations

## Configuration file `mongomigrate.ini`

Some or all of the configuration can be set in a configuration file `mongomigrate.ini` with the following format:

```ini
[database]
host = 127.0.0.1
port = 27017
database = test

[migrations]
migrations = mongo_migrations
```

as an alternative to keyword arguments (see `mongomigrate.ini.template` in this repository).

This allows for shorter CLI commands. Examples:

```bash
$ mongo-migrate create --message 'first migration'
$ mongo-migrate upgrade head
$ mongo-migrate upgrade +3
$ mongo-migrate downgrade base
$ mongo-migrate downgrade -3
```

Hybrid CLI/`.ini` example:

```bash
mongo-migrate upgraade head --username user42 --password abc123
```

(only username and password are provided via CLI, the rest from `.ini` configuration)

The settings must be provided either in `.ini` or as command line arguments, not both.

## Environment file `.env`

Some or all of the configuration can be set in the environment file `.env` with the following format:

```env
MONGO_DB_NAME=test
MONGO_HOST=127.0.0.1
MONGO_PORT=27017
MONGO_INITDB_ROOT_USERNAME=user42
MONGO_INITDB_ROOT_PASSWORD=abc123
MIGRATIONS=mongo_migrations
```

as an alternative to keyword arguments or `mongomigrate.ini` (see `.env.template` in this repository).

This allows for shorter CLI commands same as in case of `mongomigrate.ini` as well as recycling existing MongoDB environment settings (e.g. set up for `docker-compose.yml` MongoDB service)

The settings must be provided either in `.ini` or `.env` or as command line arguments in a complementary way (no duplications).

## Planned Enhancements

Our commitment to continuous improvement includes planned features such as:
  * Support for connection string
  * More migration generation shortcuts

## Get Involved
If you encounter any issues, please raise it as a ticket in the [issue tracker.](https://github.com/blitzcode-io/mongo-migrate/issues)
If you like to contribute to this open-source project, [let me know](https://www.linkedin.com/in/rahultgeorge05). 

