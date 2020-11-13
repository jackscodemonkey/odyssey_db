import logging
import toml
import hashlib

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
        all_file=None
        with open(file) as f:
            all_file = f.read()
        return all_file

    def wrap_odessey_cmd(self, objname, objtype, sql_cmd):
        begin = "\n-- ODESSEY BEGIN |{}|{}\n".format(objname,objtype)
        end = "\n-- ODESSEY END |{}|{}\n".format(objname,objtype)
        return ''.join([begin,sql_cmd,end])

    def write_migration_files(self, build_number, config, source_file_info):
        build = config[build_number]
        cmds = []
        if len(build) > 0:
            for manifest in build['up']:
                if manifest['action'].lower() == "drop":
                    sql_command = "DROP {} {};".format(manifest['type'].upper(), manifest['name'])
                    wrapped_command = self.wrap_odessey_cmd(objname=manifest['name'], objtype=manifest['type'], sql_cmd=sql_command)
                    cmds.append(wrapped_command)
                elif manifest['action'].lower() == "create" and manifest['type'].lower() == 'schema':
                    sql_command = "CREATE SCHEMA {};".format(manifest['name'].lower())
                    wrapped_command = self.wrap_odessey_cmd(objname=manifest['name'], objtype=manifest['type'], sql_cmd=sql_command)
                    cmds.append(wrapped_command)
                elif manifest['action'].lower() == "create":
                    for item in source_file_info:
                        if item['name'].lower() == manifest['name'].lower():
                            sql_command = self.read_source_file(item['file'])
                            wrapped_command = self.wrap_odessey_cmd(objname=manifest['name'], objtype=manifest['type'], sql_cmd=sql_command)
                            cmds.append(wrapped_command)
        return cmds
