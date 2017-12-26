"""Logging tools for fixie"""
import os
import json
import time
from collections.abc import Set

from xonsh.tools import print_color

from fixie.environ import ENV, expand_file_and_mkdirs


class Logger:
    """A logging object for fixie that stores information in line-oriented JSON
    format.
    """

    __inst = None

    def __new__(cls):
        # make the logger a singleton
        if Logger.__inst is None:
            Logger.__inst = object.__new__(cls)
        return Logger.__inst

    def __init__(self, filename=None):
        """
        Parameters
        ----------
        filename : str or None, optional
            Path to logfile, if None, defaults to $FIXIE_LOGFILE.
        """
        self._filename = None
        self.filename = filename
        self._dirty = True
        self._cached_entries = ()

    def log(self, message, category='misc', data=None):
        """Logs a message, the timestamp, its category, and the
        and any data to the log file.
        """
        self._dirty = True
        entry = {'message': message, 'timestamp': time.time(),
                 'category': category}
        if data is not None:
            entry['data'] = data

        # write to log file
        with open(self.filename, 'a+') as f:
            json.dump(entry, f, sort_keys=True, separators=(',', ':'),
                      default=self.json_encode)
            f.write('\n')
        # write to stdout
        msg = '{INTENSE_CYAN}' + category + '{PURPLE}:'
        msg += '{INTENSE_WHITE}' + message + '{NO_COLOR}'
        print_color(msg)

    def load(self):
        """Loads all of the records from the logfile and returns a list of dicts.
        If the log file does not yet exist, this returns an empty list.
        """
        if not os.path.isfile(self.filename):
            return []
        if not self._dirty:
            return self._cached_entries
        with open(self.filename) as f:
            entries = [json.loads(line, object_hook=self.json_decode) for line in f]
        self._dirty = False
        self._cached_entries = entries
        return entries

    @staticmethod
    def json_encode(obj):
        if isinstance(obj, Set):
            return {'__set__': True, 'elements': sorted(obj)}
        raise TypeError(repr(obj) + " is not JSON serializable")

    @staticmethod
    def json_decode(dct):
        if '__set__' in dct:
            return set(dct['elements'])
        return dct

    @property
    def filename(self):
        value = self._filename
        if value is None:
            value = ENV['FIXIE_LOGFILE']
        return value

    @filename.setter
    def filename(self, value):
        if value is None:
            self._filename = value
        else:
            self._filename = expand_file_and_mkdirs(value)


LOGGER = Logger()
