from re import compile as re_compile, IGNORECASE as re_IGNORECASE
from os import path as os_path, mkdir as os_mkdir
from platform import system as platform_system
from typing import Optional

DEBUG = False
TESTING = False

class _Config:
    _instances = []
    def __init__(self):
        self._instances.append(self)
        self._history = [dict()]

    def _get_value(self, name):
        return self.__dict__.get(name, None)

    def _set_value(self, name, value):
        self._history[-1][name] = self._get_value(name)
        self.__dict__[name] = value

    def _add_layer(self):
        self._history.append(dict())

    def _pop_layer(self):
        for key in self._history[-1]:
            self.__dict__[key] = self._history[-1][key]

    @classmethod
    def get_instance(cls):
        if len(cls._instances) == 0:
            cls()
        return cls._instances[-1]

    @classmethod
    def process(cls, name, new_val):
        if new_val is None:
            return cls.get_instance()._get_value(name)
        else:
            cls.get_instance()._set_value(name, new_val)

    @classmethod
    def add_layer(cls):
        cls.get_instance()._add_layer()

    @classmethod
    def pop_layer(cls):
        cls.get_instance()._pop_layer()


def name_wrap(func):
    def wrapper(*args, **kwargs):
        return func(func.__name__, *args, **kwargs)
    return wrapper

@name_wrap
def FORCE_LOCAL(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val) and (DEBUG or TESTING)

@name_wrap
def IS_READ_ALOUD(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)and CURRENT_SYSTEM == SYSTEM_WINDOWS

@name_wrap
def LOCAL_LIBRARY_FILE(name, new_val: Optional[str] = None):
    return _Config.process(name, new_val)

@name_wrap
def SUPPRESS_AUTOSAVE(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val) and (DEBUG or TESTING)

@name_wrap
def SUPPRESS_GOOD(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val) and (DEBUG or TESTING)

@name_wrap
def SUPPESS_PICS(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val) and (DEBUG or TESTING)

@name_wrap
def SUPPRESS_RESULTS(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val) and (DEBUG or TESTING)

@name_wrap
def UNFINISHED_FILE_READ(name, new_val: Optional[str] = None):
    return _Config.process(name, new_val)


def add_layer():
    _Config.add_layer()

def pop_layer():
    _Config.pop_layer()



CURRENT_SYSTEM = platform_system()

SYSTEM_WINDOWS = "Windows"
SYSTEM_LINUX = "Linux"
SYSTEM_MACOS = "Darwin"

if CURRENT_SYSTEM == SYSTEM_WINDOWS:
    import colorama
    colorama.init()

MEASURE_TIME = False and DEBUG
FORCE_LOCAL(True)
SUPPRESS_AUTOSAVE(True)
SUPPRESS_GOOD(True)
SUPPESS_PICS(True)
SUPPRESS_RESULTS(True)

IS_READ_ALOUD(False)
AUTOPLAY_UNFINSHED = True

RE_SITE = re_compile("(https?://[a-zA-Z\d./_-]*\.(png|jpg|jpeg|gif|bmp))", re_IGNORECASE)
RE_DB_SITE = re_compile("pic:[ \n](\d+\.(png|jpg|jpeg|gif|bmp))", re_IGNORECASE)
RE_RAZDATOCHNYI_MATERIAL = re_compile("\s*\[Раздаточный материал: (.+)\]")
RE_RAZDATKA = re_compile("\s*<раздатка>(.+)<\/раздатка>")

INTERNET_ON = False
RUNNING = True
SECONDS_PER_REQUEST = 15

CURRENT_DIR = os_path.dirname(os_path.abspath(__file__))
LOCAL_LIBRARY_DIR = os_path.join(os_path.dirname(CURRENT_DIR), "ChGKWordGetter", "src")
RESULT_DIR = os_path.join(CURRENT_DIR, "results")
TMP_DIR = os_path.join(CURRENT_DIR, "tmp")
TESTS_DIR = os_path.join(TMP_DIR, "tests")
FOLDERS_TO_CREATE = (RESULT_DIR, TMP_DIR)

GOOD_FILE = os_path.join(CURRENT_DIR, "good.txt")
LOCAL_LIBRARY_FILE(os_path.join(LOCAL_LIBRARY_DIR, "%s.xml"))
COMMAND_HISTORY_LOG_FILE = os_path.join(TMP_DIR, "command_history.log")
READ_ALOUD_FILE = os_path.join(TMP_DIR, "read.vbs")
UNFINISHED_FILE_READ(os_path.join(TMP_DIR, "unfinished.txt"))
UNFINISHED_FILE_WRITE = os_path.join(TMP_DIR, "unfinished.txt")


for folder in FOLDERS_TO_CREATE:
    if not os_path.exists(folder):
        os_mkdir(folder)

DB_NAME = "mydatabase.db"

UNKNOWN_PACKAGE = "Unknown package"
DEFAULT_XML = f"<tournament><Title>{UNKNOWN_PACKAGE}</Title></tournament>"

MUTE_KEYS = ("-m", "-ь")
UNMUTE_KEYS = ("-u", "-um", "-г", "-гь")
