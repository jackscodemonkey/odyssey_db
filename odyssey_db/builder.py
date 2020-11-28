import logging
import toml
import hashlib
import importlib.util
import re
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class Builder:

    def __init__(self, settings):
        self.MIGRATION_FOLDER = settings.MIGRATION_FOLDER
        self.MIGRATION_MAINIFEST = settings.MIGRATION_MAINIFEST

        logger.debug(f"Migration Folder: {self.MIGRATION_FOLDER}")
        logger.debug(f"Manifest File: {self.MIGRATION_MAINIFEST}")

        version_init_file = Path(self.MIGRATION_FOLDER, '__init__.py')
        if not version_init_file.is_file():
            logger.error(
                "Unable to import version from: {}".format(version_init_file))
            logger.error(
                "Ensure the setting MIGRATION_FOLDER is set and __init__.py exists under that folder.")
        else:
            spec = importlib.util.spec_from_file_location(
                "version", version_init_file)
            version = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(version)

            self.__version__ = version.__version__
            self.__release__ = version.__release__

    def get_existing_files(self):
        files = []
        extensions = ['*_up.sql', ]
        [files.extend(Path(self.MIGRATION_FOLDER).glob(x)) for x in extensions]
        return files

    def read_manifest(self):
        """
        Parses manifest file for the list and order of objects to build
        of up / down migrations.

        :param file: Location of manifest fine in toml format
        :type file: [string]
        :return: Dictionary of toml contents
        :rtype: [dict]
        """
        toml_data = toml.load(self.MIGRATION_MAINIFEST)
        return toml_data

    def generate_file_hash(self, file):
        """
        Generates blake2s hexdigest key from the contents of the input file.

        :param file: Path to input file
        :type file: [string]
        :return: hexdigest key
        :rtype: [string]
        """
        file_hash = hashlib.blake2s()
        with open(file, "rb") as f:
            while chunk := f.read(8192).encode('utf-8'):
                file_hash.update(chunk)
        digest = file_hash.hexdigest()
        return digest

    def read_source_file(self, file):
        """
        Reads entire sql source file into memory.

        :param file: Path to file
        :type file: [string]
        :return: String of file contents
        :rtype: [string]
        """
        all_file = None
        with open(file) as f:
            all_file = f.read()
            a = type(all_file)
        return all_file

    def wrap_odessey_cmd(self, objname, objtype, sql_cmd):
        """
        Appends header and footer information around a SQL statement. Header and footer information is used to quickly identify start/stop of object statement
        future parsing.

        :param objname: Name of sql object
        :type objname: [string]
        :param objtype: SQL type of object
        :type objtype: [string]
        :param sql_cmd: SQL statement for create/drop/migrate of object
        :type sql_cmd: [string]
        :return: Merged string of SQL statement and Odessy header/footer information for the object
        :rtype: [string]
        """
        begin = "\n-- ODESSEY BEGIN |{}|{}\n".format(objname, objtype)
        end = "\n-- ODESSEY END |{}|{}\n".format(objname, objtype)
        return ''.join([begin, sql_cmd, end])

    def read_and_wrap(self, objname, objtype, file, sql_source=None):
        if sql_source:
            sql_command = sql_source
        else:
            if Path(file).is_file():
                sql_command = self.read_source_file(file)
            else:
                logger.error(f"Source file not found: {str(file)}")
                exit(-1)

        wrapped_command = self.wrap_odessey_cmd(
            objname=objname, objtype=objtype, sql_cmd=sql_command)

        return wrapped_command

    def migration_file_name(self,  build_number, direction):
        filename = ''.join([build_number, '_', direction, '.sql'])
        full_path = ''.join([self.MIGRATION_FOLDER, '/', filename])
        pathlib_path = Path(full_path)
        logger.debug("Migration file: {}".format(str(full_path)))
        return pathlib_path

    def migration_file_exists(self, full_path):
        logger.debug("Checking if migration file {} exists.".format(full_path))
        if Path.is_file(full_path):
            logger.warning("Migration file exits: {}".format(full_path))
            logger.warning(
                "You must remove the migration file prior to running a build if you intend to regenerate this migration.")
            logger.warning(
                "Be sure you intend to regenenrate this migtation, this will break the integrity of the migrations.")
            logger.warning(
                "Any databases migrated with this build should be rolled back prior to this build before migrating forward.")
            return True
        else:
            return False

    def write_migration(self, file, build_spec):
        current_utc = datetime.utcnow()
        build_string = f"-- ODESSEY - Build Time UTC: {current_utc} - VERSION: {self.__version__} - RELEASE: {self.__release__}".encode(
            encoding='UTF-8', errors='strict')
        try:
            logger.debug("Writing migration file: {}".format(str(file)))
            with Path.open(file, 'wb',) as f:
                for item in build_spec:
                    f.write(item.encode(encoding='UTF-8', errors='strict'))
                    f.flush()
                f.write(build_string)
                f.flush()
            return True
        except Exception as e:
            logger.error(
                "Could not write migration file: {} {}".format(str(file), str(e)))
            return False

    def match_previous_definition(self, filename, objname, objtype):

        start = r'-- ODESSEY BEGIN \|{}\|{}'.format(objname, objtype)
        middle = r'([\S\s]*?)'
        end = r'-- ODESSEY END \|{}\|{}'.format(objname, objtype)

        pattern = [start, middle, end]

        regx = re.compile(start + middle + end)

        match = None
        found = False
        logger.info(filename)
        if Path(filename).is_file:
            with Path.open(filename, 'r') as f:
                contents = f.read()
                results = re.search(regx, contents)
                if results:
                    if results.group(1) is not None:
                        match = results.group(1)
                        found = True
        else:
            logger.error(f"Rollback file does not exist: {filename}")
            exit(-1)
        return found, match

    def build_cmds(self, manifest, source_file_info, old_migrations=None):
        wrapped_command = None
        sql_command = None
        if manifest['action'].lower() == "drop":
            # Handle drop statements without needing a source file.
            sql_command = "DROP {} {};".format(
                manifest['type'].upper(), manifest['name'])
            wrapped_command = self.wrap_odessey_cmd(
                objname=manifest['name'], objtype=manifest['type'], sql_cmd=sql_command)
        elif manifest['action'].lower() == "create" and manifest['type'].lower() == 'schema':
            # Handle create schema statements without needing a source file.
            sql_command = "CREATE SCHEMA {};".format(
                manifest['name'].lower())
            wrapped_command = self.wrap_odessey_cmd(
                objname=manifest['name'], objtype=manifest['type'], sql_cmd=sql_command)
        elif manifest['action'].lower() == "create":
            # Wrap create statements using source files
            logger.debug(source_file_info)
            source_file = next((item['file'] for item in source_file_info if item["name"].lower(
            ) == manifest['name'].lower()), None)
            if source_file:
                wrapped_command = self.read_and_wrap(
                    objname=manifest['name'], objtype=manifest['type'], file=source_file)
                source_file = None
            else:
                logger.error(
                    f"Source control file for object {manifest['name'].lower()} not found.")
                exit(-1)
        elif manifest['action'].lower() == "execute":
            # Wrap create statements using source files
            source_file = manifest['location']
            if Path(source_file).is_file():
                wrapped_command = self.read_and_wrap(
                    objname=manifest['name'], objtype=manifest['type'], file=source_file)
                source_file = None
            else:
                logger.error(f"Source file not found {source_file}")
                exit(-1)
        elif manifest['action'].lower() == "rollback":
            # Search old migration files for last version of object source.
            if old_migrations:
                for migration_file in old_migrations:
                    if migration_file:
                        if Path(migration_file).is_file():
                            result, sql_command = self.match_previous_definition(
                                filename=migration_file, objname=manifest['name'], objtype=manifest['type'])
                            if result:
                                wrapped_command = self.read_and_wrap(
                                    objname=manifest['name'], objtype=manifest['type'], file=None, sql_source=sql_command)
                                break
                        else:
                            logger.error(f'Expected migration file {migration_file} does not exist! Cannot find a rollback version for manifest!')
                            logger.error(f"Manifest: {manifest}")
                            logger.error(f"Know previous migrtion files: {old_migrations}")
                            exit(-1)
            else:
                logger.error(
                    f"Missing previous up migration files, cannot find a rollback version for manifest!")
                logger.error(f"Manifest: {manifest}")
                exit(-1)

        if wrapped_command:
            return wrapped_command
        else:
            logger.error("Build command is empty!")
            exit(-1)

    def build_up_migration(self, build_number, config, source_file_info):
        build = config[build_number]['up']
        cmds = []
        if len(build) > 0:
            for manifest in build:
                results = self.build_cmds(
                    manifest=manifest, source_file_info=source_file_info)
                cmds.append(results)
        else:
            logger.error(
                f"Build up for {build_number} is empty. Check your manifest.")
            exit(-1)
        logger.debug(f"Up commands for build {build_number}: {cmds}")
        return cmds

    def build_down_migration(self, build_number, config, source_file_info):
        cmds = []
        files = sorted(Path(self.MIGRATION_FOLDER).glob(
            '*_up.sql'), reverse=True)
        previous_files = [x for x in files if x.name.replace(
            '_up.sql', '') < build_number]
        build_down = config[build_number]['down']
        if len(build_down) > 0:
            for manifest in build_down:
                results = self.build_cmds(
                    manifest=manifest, source_file_info=source_file_info, old_migrations=previous_files)
                if results:
                    cmds.append(results)
                else:
                    logger.error(
                        f"Build down for {build_number} is empty. Every up build must have a corrisponding roll back. Check your mainifest.")
                    exit(-1)
        else:
            logger.error(
                f"Build down for {build_number} is empty. Every up build must have a corrisponding roll back. Check your mainifest.")
            exit(-1)
        logger.debug(f"Down commands for build {build_number}: {cmds}")
        return cmds
