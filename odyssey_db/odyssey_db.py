import argparse
import logging

logger = logging.getLogger(__name__)


class Migrate:

    def __init__(self):
        """
        Init method of the Migrate class.
        """
        pass


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

    parser.add_argument('-v', '--verbose', help="Verbose", action='store_true')
    return parser


def run(arguments):
    logger.info("This is info.")
    logger.debug("This is debug.")


if __name__ == "__main__":
    arguments = fetch_args()
    args = arguments.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    run(
        arguments=args
    )
