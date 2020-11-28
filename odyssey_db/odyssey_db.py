import argparse
import logging
import sys
from pathlib import Path
import importlib.util
from odyssey_db.migrate import Migrate
from odyssey_db.builder import Builder
from odyssey_db.fixture import Fixture

#from . import migrate
#from . import builder
#from . import fixture

logger = logging.getLogger(__name__)


def fetch_args():
    """
    Sets up command line arguments.

    Returns: object: instance of argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="commands", dest="commands")

    p_build = subparsers.add_parser(
        name="build", help="Build database migrations.")
    p_build.add_argument(
        '-t', '--target', help="Build migration target. Default is build all missing targets.", default="all")

    p_migrate = subparsers.add_parser(
        name="migrate", help="Database migration command.")
    p_migrate.add_argument(
        'up|down', help="Migrate the database up or down.", nargs='?', choices=('up', 'down'))
    p_migrate.add_argument(
        '-t', '--target', help='Migrate to target version. Default is to migrate to the latest version.', default="max")

    p_fixture = subparsers.add_parser(
        "fixture", help="Load/Extract table data to json fixture data for initial load and testing.")
    p_fixture.add_argument(
        'load|dump', help="Load or Extract table data to json for inital load and testing.", nargs='?', choices=('load', 'dump'))

    parser.add_argument('-e', '--engine', help="Database engine",
                        nargs='?', choices=('postgres', 'greenplum'), required=True)
    parser.add_argument('-s', '--settings',
                        help="Settings file", default="config/settings.py")
    parser.add_argument('-v', '--verbose', help="Verbose", action='store_true')
    return parser


def check_engine(engine):
    module = sys.modules[__name__]
    mpath = Path(module.__file__)
    module_dir = mpath.parent.parent
    return {
        'postgres': f'{module_dir}/odyssey_db/db/postgres.py',
        'greenplum': f'{module_dir}/odyssey_db/db/greenplum.py'
    }[engine]


def run_build(db_engine, migrator, settings, source_files):
    build = Builder(settings=settings)

    manifest = build.read_manifest()
    logger.debug(manifest)

    existing_files = build.get_existing_files()
    logger.debug(existing_files)

    existing_file_names = sorted([y.name for y in existing_files])
    logger.debug(existing_file_names)

    next_target_migraion = next(iter(sorted(
        [x for x in manifest if x + '_up.sql' not in existing_file_names])), None)
    logger.info(f"Next target migration: {next_target_migraion}")

    broken_migration = False
    for efile in existing_file_names:
        if efile.replace('_up.sql', '') > next_target_migraion:
            logger.error(f"Migration file greater than target exists: {efile}")
            broken_migration = True
            break

    if broken_migration:
        logger.error("Migration chain is broken. Previously generated files have likely been removed. Regenerating missing files will produce an inconsistant database migration chain. Find the last stable release to recover past migration files and build migrations from there.")
        exit(-1)

    forward_migrations = { key:value for (key, value)  in manifest.items() if key >= next_target_migraion }
    logger.debug(forward_migrations)
    fm_num = [ x for x in sorted(forward_migrations)]
    for item in fm_num:
        logger.info(f"Building up migrations for build: {item}")
        up_file = build.migration_file_name(build_number=item, direction='up')
        down_file = build.migration_file_name(build_number=item, direction='down')
        if not build.migration_file_exists(full_path=up_file) and not build.migration_file_exists(full_path=down_file):
            up_mig = build.build_up_migration(build_number=item, config=forward_migrations, source_file_info=source_files )
            build.write_migration(file=up_file, build_spec=up_mig)

            # Need to check for source files again after writing out a migration in case we're processing multiple builds at once.
            new_files = migrator.read_sql_files(srcpath=settings.SQL_SRC, str_regex=db_engine.sql_object_name)
            source_files = migrator.flatten_files_list(source_list=new_files)
            logger.info(f"Building down migrations for build: {item}")
            down_mig = build.build_down_migration(build_number=item, config=forward_migrations, source_file_info=source_files )
            build.write_migration(file=down_file, build_spec=down_mig)
        else:
            exit(-1)

def run(arguments):
    if not Path(arguments.settings).is_file():
        logger.error("Settings file not found: {}".format(arguments.settings))
    else:
        settings_file = Path(arguments.settings)
        logger.debug(f"Settings file: {settings_file}")
        spec = importlib.util.spec_from_file_location(
            "settings", arguments.settings)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)

        # Configure the logger format from the settings
        log = logging.getLogger()
        handler = log.handlers[0]
        logFormat = logging.Formatter(fmt=settings.LOGGING['format'])
        handler.setFormatter(logFormat)

    if arguments.engine:
        logger.debug('Engine: {}'.format(arguments.engine))
        specdb = importlib.util.spec_from_file_location(
            "engine", check_engine(arguments.engine))
        engine = importlib.util.module_from_spec(specdb)
        specdb.loader.exec_module(engine)
    else:
        logger.error("No database engine specified.")
        exit()

    logger.debug(f"Command arguments: {arguments}")
    db_engine = engine.Engine()
    migrator = Migrate()

    source_files = migrator.read_sql_files(srcpath=settings.SQL_SRC, str_regex=db_engine.sql_object_name)
    flat_files = migrator.flatten_files_list(source_list=source_files)

    if arguments.commands == "build":
        run_build(db_engine=db_engine, migrator=migrator, settings=settings, source_files=flat_files)

    elif arguments.commands == "fixture":
        fix = Fixture()


def main():
    arguments = fetch_args()
    args = arguments.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    run(
        arguments=args
    )


if __name__ == "__main__":
    sys.exit(main())
