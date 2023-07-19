from re import compile as re_compile, IGNORECASE as re_IGNORECASE
from os import path as os_path, mkdir as os_mkdir
from platform import system as platform_system
from typing import Optional
from sys import argv as sys_argv, modules as sys_modules
from enum import Enum
from datetime import date as dt_date

DEBUG = len(sys_argv) > 1 and sys_argv[1] in ("-d", "-D")
TESTING = len(sys_argv) > 1 and sys_argv[1] in ("-t", "-T")
print(f"{DEBUG=}, {TESTING=}")


class LAYERS(Enum):
    DEBUG = "debug"
    TESTING = "testing"
    OUTER = "outer"
    READER = "reader"
    CUSTOM = "custom"  # can't be used in working code? only whule writing


def init_testing():
    with open(TMP_TESTS_FILE, "w"):
        pass
    if not TESTING:
        return
    from sys import argv
    if len(argv) < 3:
        raise IndexError("No test number found during launching testing mode")
    add_layer(LAYERS.TESTING)
    AUTOPLAY_UNFINSHED(True)
    FORCE_LOCAL(True)
    IS_READ_ALOUD(False)
    LOCAL_LIBRARY_FILE(TEST_SOURCE_FILE)
    SAVE_CACHE_PACKAGE(False)
    SUPPRESS_AUTOSAVE(True)
    SUPPRESS_GOOD(True)
    SUPPESS_PICS(True)
    SUPPRESS_RESULTS(True)
    UNFINISHED_FILE_READ(TEST_FILE % argv[2])
    UNIFY_DATE(True)
    WRITE_TESTS_OUTPUT(True)
    _Config.write_dict_diff()

def init_debug():
    if not DEBUG:
        return
    add_layer(LAYERS.DEBUG)
    AUTOPLAY_UNFINSHED(True)
    FORCE_LOCAL(True)
    IS_READ_ALOUD(False)
    SAVE_CACHE_PACKAGE(False)
    SUPPRESS_AUTOSAVE(True)
    SUPPRESS_GOOD(True)
    SUPPESS_PICS(True)
    SUPPRESS_RESULTS(True)
    UNIFY_DATE(True)
    WRITE_TESTS_OUTPUT(True)
    _Config.write_dict_diff()


def init_outer_main():
    add_layer(LAYERS.OUTER)
    FORCE_LOCAL(False)
    IS_READ_ALOUD(False)
    SAVE_CACHE_PACKAGE(True)
    UNIFY_DATE(True)
    WRITE_TESTS_OUTPUT(False)
    # _Config.write_dict_diff()

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

    def _add_layer(self, layer):
        self._history.append(dict())
        self._set_value('layer', layer)

    def _pop_layer(self, layer):
        old_layer = self._get_value('layer')
        if old_layer != layer:
            raise ValueError(f"Error found while popping config. Expected {old_layer.value!r} got {layer.value!r}")
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
    def add_layer(cls, layer: LAYERS):
        cls.get_instance()._add_layer(layer)

    @classmethod
    def pop_layer(cls, layer: LAYERS):
        cls.get_instance()._pop_layer(layer)

    @classmethod
    def write_dict_diff(cls):
        from ChGKQuestions import my_print
        my_print(cls.process("layer", None).value, set(cls.get_instance().__dict__.keys()) - set(cls.get_instance()._history[-1].keys()), sep=": ", silent=True)

def name_wrap(func):
    def wrapper(*args, **kwargs):
        return func(func.__name__, *args, **kwargs)
    return wrapper

@name_wrap
def AUTOPLAY_UNFINSHED(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)

@name_wrap
def FORCE_LOCAL(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)

@name_wrap
def IS_READ_ALOUD(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)and CURRENT_SYSTEM == SYSTEM_WINDOWS

@name_wrap
def LOCAL_LIBRARY_FILE(name, new_val: Optional[str] = None):
    return _Config.process(name, new_val)

@name_wrap
def SUPPRESS_AUTOSAVE(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)

@name_wrap
def SAVE_CACHE_PACKAGE(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)

@name_wrap
def SUPPRESS_GOOD(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)

@name_wrap
def SUPPESS_PICS(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)

@name_wrap
def SUPPRESS_RESULTS(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)

@name_wrap
def UNFINISHED_FILE_READ(name, new_val: Optional[str] = None):
    return _Config.process(name, new_val)

@name_wrap
def UNIFY_DATE(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)

@name_wrap
def WRITE_TESTS_OUTPUT(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)

def add_layer(layer: LAYERS):
    _Config.add_layer(layer)

def pop_layer(layer: LAYERS):
    _Config.pop_layer(layer)



CURRENT_SYSTEM = platform_system()

SYSTEM_WINDOWS = "Windows"
SYSTEM_LINUX = "Linux"
SYSTEM_MACOS = "Darwin"

if CURRENT_SYSTEM == SYSTEM_WINDOWS:
    try:
        import colorama
        colorama.init()
    except ModuleNotFoundError:
        pass
USE_CONTROL_CHARACTERS = "colorama" in sys_modules.keys() or CURRENT_SYSTEM != SYSTEM_WINDOWS

DB_CHGK = "https://db.chgk.net"

DEFAULT_DATE = dt_date(1970, 1, 1)

MEASURE_TIME = False and DEBUG
FORCE_LOCAL(False)
SUPPRESS_AUTOSAVE(False)
SUPPRESS_GOOD(False)
SUPPESS_PICS(False)
SUPPRESS_RESULTS(False)
UNIFY_DATE(False)

IS_READ_ALOUD(False)
AUTOPLAY_UNFINSHED(True)
WRITE_TESTS_OUTPUT(True)
SAVE_CACHE_PACKAGE(True)

RE_SITE = re_compile("(https?://[a-zA-Z\d./_-]*\.(png|jpg|jpeg|gif|bmp))", re_IGNORECASE)
RE_DB_SITE = re_compile("pic:[ \n](\d+\.(png|jpg|jpeg|gif|bmp))", re_IGNORECASE)
RE_RAZDATOCHNYI_MATERIAL = re_compile("\s*\[Раздаточный материал: (.+)\]")
RE_RAZDATKA = re_compile("\s*<раздатка>(.+)<\/раздатка>")

INTERNET_ON = False
RUNNING = True
SECONDS_PER_REQUEST = 15

CURRENT_DIR = os_path.dirname(os_path.abspath(__file__))
PARENT_DIR = os_path.dirname(CURRENT_DIR)
LOCAL_LIBRARY_DIR = os_path.join(PARENT_DIR, "ChGKWordGetter", "src")
RESULT_DIR = os_path.join(CURRENT_DIR, "results")
TESTS_DIR = os_path.join(CURRENT_DIR, "tests")
TESTS_SRC_DIR = os_path.join(TESTS_DIR, "src")
TMP_DIR = os_path.join(CURRENT_DIR, "tmp")
TMP_PACKAGE_CACHE_DIR = os_path.join(TMP_DIR, "package_cache")
TMP_TESTS_DIR = os_path.join(TMP_DIR, "tests")
FOLDERS_TO_CREATE = (RESULT_DIR, TMP_DIR, TESTS_DIR, TMP_TESTS_DIR, TESTS_SRC_DIR, TMP_PACKAGE_CACHE_DIR)

CANON_EXTENSION = ".canon"
TEST_EXTENSION = ".tst"
TEST_SOURCE_BASE_EXTENSION = ".srclist"
CANON_RESULT_FILE = os_path.join(TESTS_DIR, f"%s{CANON_EXTENSION}")
COMMAND_HISTORY_LOG_FILE = os_path.join(TMP_DIR, "command_history.log")
GOOD_FILE = os_path.join(CURRENT_DIR, "good.txt")
LOCAL_LIBRARY_FILE(os_path.join(LOCAL_LIBRARY_DIR, "%s.xml"))
PACKAGE_CACHE_FILE = os_path.join(TMP_PACKAGE_CACHE_DIR, "%s.xml")
READ_ALOUD_FILE = os_path.join(TMP_DIR, "read.vbs")
TEST_FILE = os_path.join(TESTS_DIR, f"%s{TEST_EXTENSION}")
TEST_SOURCE_FILE = os_path.join(TESTS_SRC_DIR, "%s.xml")
TEST_SOURCE_BASE_FILE = os_path.join(TESTS_SRC_DIR, f"%s{TEST_SOURCE_BASE_EXTENSION}")
TMP_DIFF_FILE = os_path.join(TMP_DIR, "diff.txt")
TMP_TESTS_FILE = os_path.join(TMP_TESTS_DIR, "test.result")
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


class COLORS:
    OKGREEN = '\033[92m' if USE_CONTROL_CHARACTERS else ''
    FAIL = '\033[91m' if USE_CONTROL_CHARACTERS else ''
    END = '\033[0m' if USE_CONTROL_CHARACTERS else ''
