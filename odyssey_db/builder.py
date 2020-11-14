import logging
import toml
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


class Builder:
    def __init__(self, ):
        pass

    def read_manifest(self, file):
        """
        Parses manifest file for the list and order of objects to build
        of up / down migrations.

        :param file: Location of manifest fine in toml format
        :type file: [string]
        :return: Dictionary of toml contents
        :rtype: [dict]
        """
        toml_data = toml.load(file)
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

    def validate_migration_source_list(self, source_file_dict):
        migration_list = []
        return migration_list

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

    def read_and_wrap(self, objname, objtype, file):
        sql_command = self.read_source_file(file)
        wrapped_command = self.wrap_odessey_cmd(
            objname=objname, objtype=objtype, sql_cmd=sql_command)
        return wrapped_command

    def migration_file_name(self,  build_number, direction, migration_folder):
        filename = ''.join([build_number, '_', direction, '.sql'])
        full_path = ''.join([migration_folder, '/', filename])
        pathlib_path = Path(full_path)
        logger.debug("Migration file: {}".format(str(full_path)))
        return pathlib_path

    def migration_file_exists(self, full_path):
        logger.debug("Checking if migration file {} exists.".format(full_path))
        if Path.is_file(full_path):
            logger.error("Migration file exits: {}".format(full_path))
            logger.error(
                "You must remove the migration file prior to running a build if you intend to regenerate this migration.")
            logger.error(
                "Be sure you intent to regenenrate this migtation, this will break the integrity of the migrations.")
            logger.error(
                "Any databases migrated with this build should be rolled back prior to this build before migrating forward.")
            return True
        else:
            return False

    def write_migration(self, file, build_spec):
        try:
            logger.debug("Writing migration file: {}".format(str(file)))
            with Path.open(file, 'wb') as f:
                for item in build_spec:
                    f.write(item.encode())
                    f.flush()
            return True
        except Exception as e:
            logger.error("Could not write migration file: {} {}".format(str(file), str(e)))
            return False

    def build_migration(self, build_number, config, source_file_info):
        build = config[build_number]
        cmds = []
        if len(build) > 0:
            for manifest in build['up']:
                wrapped_command = None
                sql_command = None
                if manifest['action'].lower() == "drop":
                    # Handle drop statements without needing a source file.
                    sql_command = "DROP {} {};".format(
                        manifest['type'].upper(), manifest['name'])
                    wrapped_command = self.wrap_odessey_cmd(
                        objname=manifest['name'], objtype=manifest['type'], sql_cmd=sql_command)
                    cmds.append(wrapped_command)
                elif manifest['action'].lower() == "create" and manifest['type'].lower() == 'schema':
                    # Handle create schema statements without needing a source file.
                    sql_command = "CREATE SCHEMA {};".format(
                        manifest['name'].lower())
                    wrapped_command = self.wrap_odessey_cmd(
                        objname=manifest['name'], objtype=manifest['type'], sql_cmd=sql_command)
                    cmds.append(wrapped_command)
                elif manifest['action'].lower() == "create":
                    # Wrap create statements using source files
                    for item in source_file_info:
                        if item['name'].lower() == manifest['name'].lower():
                            source_file = item['file']
                            wrapped_command = self.read_and_wrap(
                                objname=manifest['name'], objtype=manifest['type'], file=source_file)
                            cmds.append(wrapped_command)
                elif manifest['action'].lower() == "execute":
                    # Wrap create statements using source files
                    source_file = manifest['location']
                    wrapped_command = self.read_and_wrap(
                        objname=manifest['name'], objtype=manifest['type'], file=source_file)
                    cmds.append(wrapped_command)
        return cmds
