import re
import psycopg2
import logging
from types import SimpleNamespace
import json

logger = logging.getLogger(__name__)
logger.debug("Loading postgres database engine.")

class Engine:

    def __init__(self):

        # Dictionary of regex used to parse sql files
        self.regex_dict = {
            'object': '(?<=create )(.*?)((\w*)\.(\w*))|(?<=create )(.*?)(\w*)\;',
        }

        # Converts dictionary to dot notation object
        self.regex_strings = json.loads(json.dumps(self.regex_dict), object_hook=lambda item: SimpleNamespace(**item))

        # Compile top level regex
        logger.debug("Regex string for object name: {}".format(self.regex_strings.object))
        self.sql_object_name = re.compile(self.regex_strings.object, re.MULTILINE|re.IGNORECASE)
