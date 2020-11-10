import argparse
import logging
from pathlib import Path
import configparser
import os
import importlib.util

logger = logging.getLogger(__name__)


class Migrate:

    def __init__(self):
        """
        Init method of the Migrate class.
        """
        pass

    def get_sql_files(self, srcpath):
        """
        Provided a source path, recursivly finds all files with the extention .sql

        Args:
            srcpath ([string]): File system path to sql source files.

        Returns:
            [list]: list containg the path of all sql source files.
        """
        files = Path(srcpath).rglob('*.sql')
        return files

    def get_name_from_file(self, file_name, str_regex):
        """
        Extracts the object name from a provided SQL source file.

        Args:
            | file_name ([string]): File name to inspect for SQL object name
            | str_regex ([re.compile]): Regex object to search for object name.

        Returns:
            [string]: Returns the name of the object if found. Returns None if not.
        """
        with open(file_name) as f:
            content = f.read()
            objname = None
            if str_regex.findall(content):
                objname = str_regex.findall(content)[0][1]
            return objname

        return one

class Fixture:

    def __init__(self):
        """
        Init method of the Fixture class
        """


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
        'postgres': 'from db.postgres import pg as Engine',
        'greenplum': 'from db.greenplum import gp as Engine'
    }[engine]


def run(arguments):
    db_engine = Engine()


if __name__ == "__main__":
    arguments = fetch_args()
    args = arguments.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if not Path(args.settings).is_file():
        logger.error("Settings file not found: {}".format(args.settings))
    else:
        spec = importlib.util.spec_from_file_location(
            "settings", args.settings)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)

    if args.engine:
        exec(check_engine(args.engine))
    else:
        logger.error("No database engine specified.")
        exit()

    run(
        arguments=args
    )
