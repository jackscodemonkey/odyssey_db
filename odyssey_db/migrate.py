import logging
from pathlib import Path
from collections import defaultdict

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

        :param srcpath: [string]: File system path to sql source files.
        :return: [list] - list containg the path of all sql source files.
        """
        files = Path(srcpath).rglob('*.sql')
        return files

    def get_name_from_file(self, file_name, str_regex):
        """
        Extracts the object name from a provided SQL source file.

        :param file_name: [string]: File name to inspect for SQL object name
        :param str_regex: [re.compile]: Regex object to search for object name.
        :return: [list] - Returns a list containing the full path to the file the object type and the object name found in the file.
        """
        file_info = []
        with open(file_name) as f:
            content = f.read()
            objname = None
            if str_regex.findall(content):
                objresults = [file_name]
                objname = [tuple(str(i).strip() for i in m if i) for m in str_regex.findall(content)]
                objresults.extend(*objname)
                file_info.append(objresults)
        return file_info

    def read_sql_files(self, srcpath, str_regex):
        """

        Control function to build a complete dictionary of known object types and their object names from the sql source code.

        :param srcpath: path to source files
        :type srcpath: [string]
        :param str_regex: compiled regular expression
        :type str_regex: [re.compile]
        :return: dictionary of sql object types with file path and object name as contents
        :rtype: [default dictionary]
        """
        results = defaultdict(list)
        files = self.get_sql_files(srcpath=srcpath)
        for file in files:
            result = self.get_name_from_file(file_name=file, str_regex=str_regex)
            if len(result) > 0:
                results[result[0][1]].append({'name':result[0][2],'file':result[0][0]})
        return results
