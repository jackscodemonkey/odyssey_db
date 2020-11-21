import argparse
import logging
from pathlib import Path
import importlib.util
from . import migrate
from . import builder
from . import fixture

logger = logging.getLogger(__name__)


def fetch_args():
    """
    Sets up command line arguments.

    Returns: object: instance of argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    p_migrate = subparsers.add_parser(
        name="migrate", help="Database migration command.")
    p_migrate.add_argument(
        'up|down', help="Migrate the database up or down.", nargs='?', choices=('up', 'down'))
    p_migrate.add_argument(
        '-t', '--target', help='Migrate to target version. latest keyword will migrate to the highest version.')

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
    return {
        'postgres': 'odyssey_db/db/postgres.py',
        'greenplum': 'odyssey_db/db/greenplum.py'
    }[engine]


def run(arguments):
    if not Path(arguments.settings).is_file():
        logger.error("Settings file not found: {}".format(arguments.settings))
    else:
        spec = importlib.util.spec_from_file_location(
            "settings", arguments.settings)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)

        #Configure the logger format from the settings
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


    db_engine = engine.Engine()
    migrator = migrate.Migrate()
    build = builder.Builder(settings=settings)
    fix = fixture.Fixture()


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
