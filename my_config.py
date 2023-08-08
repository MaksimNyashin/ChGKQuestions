from re import compile as re_compile, IGNORECASE as re_IGNORECASE, DOTALL as re_DOTALL
from os import path as os_path, mkdir as os_mkdir
from platform import system as platform_system
from typing import Optional
from sys import argv as sys_argv, modules as sys_modules
from enum import Enum
from datetime import date as dt_date


# ========== Config mods (don't touch) ==========

parse_args = lambda *args: len(sys_argv) > 1 and sys_argv[1] in args

DEBUG = parse_args("-d", "-D")
TESTING = parse_args("-t", "-T")
GAME = parse_args("-g", "-G")
DEBUG_UNFINSHED = len(sys_argv) > 2 and sys_argv[2] in ('-du', '-ud')
EXPERIMENTS = False
print(f"{DEBUG=}, {TESTING=}, {GAME=}, {DEBUG_UNFINSHED=}")


def init_testing():
    with open(TMP_TESTS_FILE, "w"):
        pass
    if not TESTING:
        return
    if len(sys_argv) < 3:
        raise IndexError("No test number found during launching testing mode")
    add_layer(LAYERS.TESTING)
    AUTOPLAY_UNFINSHED(True)
    FORCE_LOCAL(True)
    IS_READ_ALOUD(True)
    LOCAL_LIBRARY_FILE(TEST_SOURCE_FILE)
    RUN_COUNTDOWN(False)
    SAVE_CACHE_PACKAGE(False)
    SUPPRESS_AUTOSAVE(True)
    SUPPRESS_GOOD(True)
    SUPPESS_PICS(True)
    SUPPRESS_READING(True)
    SUPPRESS_RESULTS(True)
    SUPPRESS_TEXT(False)
    UNFINISHED_FILE_READ(TEST_FILE % sys_argv[2])
    UNIFY_DATE(True)
    WRITE_TESTS_OUTPUT(True)
    _Config.write_dict_diff()


def init_debug():
    if not DEBUG:
        return
    add_layer(LAYERS.DEBUG)
    AUTOPLAY_UNFINSHED(True)
    FORCE_LOCAL(True)
    IS_READ_ALOUD(True)
    RUN_COUNTDOWN(False)
    SAVE_CACHE_PACKAGE(False)
    SUPPRESS_AUTOSAVE(True)
    SUPPRESS_GOOD(True)
    SUPPESS_PICS(True)
    SUPPRESS_READING(True)
    SUPPRESS_RESULTS(True)
    SUPPRESS_TEXT(False)
    UNIFY_DATE(True)
    WRITE_TESTS_OUTPUT(True)
    _Config.write_dict_diff()


def init_outer_main():
    add_layer(LAYERS.OUTER)
    FORCE_LOCAL(False)
    IS_READ_ALOUD(False)
    RUN_COUNTDOWN(False)
    SAVE_CACHE_PACKAGE(True)
    UNIFY_DATE(True)
    WRITE_TESTS_OUTPUT(False)
    # _Config.write_dict_diff()


def init_game():
    if not GAME:
        return
    add_layer(LAYERS.GAME)
    FORCE_LOCAL(False)
    IS_READ_ALOUD(True)
    RUN_COUNTDOWN(True)
    SAVE_CACHE_PACKAGE(True)
    SUPPRESS_AUTOSAVE(False)
    SUPPRESS_GOOD(False)
    SUPPRESS_READING(False)
    SUPPRESS_TEXT(True)
    SUPPESS_PICS(False)
    SUPPRESS_RESULTS(False)
    UNIFY_DATE(False)
    WRITE_TESTS_OUTPUT(True)
    _Config.write_dict_diff()


# ========== Config and functions for changeable options (don't touch) ==========


class LAYERS(Enum):
    DEBUG = "debug"
    TESTING = "testing"
    OUTER = "outer"
    READER = "reader"
    KEY_READ_ALOUD = "key_read_aloud"
    GAME = "game"
    LOCAL_LIBRARY = "local_library"
    SUPPRESS_AUTOSAVE = "suppress_autosave"
    CUSTOM = "custom"  # can't be used in release code, only whule writing


class _Config:
    _instances = []
    LAYER = 'layer'

    def __init__(self):
        self._instances.append(self)
        self._history = [dict()]
        self._current = dict()

    def _get_value(self, name):
        return self._current.get(name, None)

    def _set_value(self, name, value):
        self._history[-1][name] = self._get_value(name)
        self._current[name] = value

    def _add_layer(self, layer: LAYERS):
        self._history.append(dict())
        self._set_value(self.LAYER, layer)

    def _pop_current_layer(self):
        for key in self._history[-1]:
            self._current[key] = self._history[-1][key]
        self._history.pop()

    def _pop_layer(self, layer: LAYERS):
        # for i in self._history:
        #     print (i)
        # print(self._current)
        if self._get_value(self.LAYER) is layer:
            return self._pop_current_layer()

        ind = len(self._history) - 1
        while ind > 0 and self._history[ind][self.LAYER] is not layer:
            ind -= 1
        if ind == 0:
            raise ValueError(f"No layer with name {layer.value!r} found in the Config history")
        ind -= 1

        tmp = self._history.pop(ind)
        keys = set(tmp.keys())
        # print(tmp)
        for i in range(ind, len(self._history)):
            cur_keys = set(self._history[i].keys())
            intersec = keys & set(self._history[i].keys())
            for key in intersec:
                self._history[i][key] = tmp[key]
            keys -= intersec
            # print(keys)

        for key in keys:
            self._current[key] = tmp[key]
        # print(self._current)

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

        my_print(
            cls.process(cls.LAYER, None).value,
            set(cls.get_instance()._current.keys()) - set(cls.get_instance()._history[-1].keys()),
            sep=": ",
            silent=True,
        )


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
    return _Config.process(name, new_val) or DEBUG or TESTING


@name_wrap
def LOCAL_LIBRARY_FILE(name, new_val: Optional[str] = None):
    return _Config.process(name, new_val)


@name_wrap
def RUN_COUNTDOWN(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)


@name_wrap
def SAVE_CACHE_PACKAGE(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)


@name_wrap
def SUPPRESS_AUTOSAVE(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)


@name_wrap
def SUPPRESS_GOOD(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)


@name_wrap
def SUPPESS_PICS(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)


@name_wrap
def SUPPRESS_READING(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val) or CURRENT_SYSTEM != SYSTEM_WINDOWS


@name_wrap
def SUPPRESS_RESULTS(name, new_val: Optional[bool] = None):
    return _Config.process(name, new_val)


@name_wrap
def SUPPRESS_TEXT(name, new_val: Optional[bool] = None):
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


# ========== System settings (don't touch) ==========

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


# ========== Default values for config options (can be changed) ==========

DEFAULT_DATE = dt_date(1970, 1, 1)

FORCE_LOCAL(False)
SUPPRESS_AUTOSAVE(False)
SUPPRESS_GOOD(False)
SUPPESS_PICS(False)
SUPPRESS_READING(False)  # don't touch, it is used only in debuging and testing, use IS_READ_ALOUD
SUPPRESS_RESULTS(False)
SUPPRESS_TEXT(False)
UNIFY_DATE(False)

IS_READ_ALOUD(False)
AUTOPLAY_UNFINSHED(True)
WRITE_TESTS_OUTPUT(True)
RUN_COUNTDOWN(False)
SAVE_CACHE_PACKAGE(True)

RE_SITE = re_compile("(https?://[a-zA-Z\d./_-]*\.(png|jpg|jpeg|gif|bmp))", re_IGNORECASE)
RE_DB_SITE = re_compile("pic:[ \n](\d+\.(png|jpg|jpeg|gif|bmp))", re_IGNORECASE)
RE_RAZDATOCHNYI_MATERIAL = re_compile("\s*\[Раздаточный материал: (.+)\]", re_DOTALL)
RE_RAZDATKA = re_compile("\s*<раздатка>(.+)<\/раздатка>", re_DOTALL)

CONSOLE_WIDTH = 80

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
if DEBUG_UNFINSHED:
    UNFINISHED_FILE_READ(os_path.join(TMP_DIR, "unfinished_debug.txt"))
else:
    UNFINISHED_FILE_READ(os_path.join(TMP_DIR, "unfinished.txt"))
UNFINISHED_FILE_WRITE = os_path.join(TMP_DIR, "unfinished.txt")

MUTE_KEYS = ("-m", "-ь")
UNMUTE_KEYS = ("-u", "-um", "-г", "-гь")
DEBUG_TESTS_KEYS = ('-dt', "-ве")
SUPPRESS_AUTOSAVE_KEYS = ('-sa', '-ыф')


# ========== Other settings (don't touch) ==========

INTERNET_ON = False
RUNNING = True
SECONDS_PER_REQUEST = 15
GAME_RUNNING = True

MEASURE_TIME = False and DEBUG

for folder in FOLDERS_TO_CREATE:
    if not os_path.exists(folder):
        os_mkdir(folder)

UNKNOWN_PACKAGE = "Unknown package"
DEFAULT_XML = f"<tournament><Title>{UNKNOWN_PACKAGE}</Title></tournament>"

TIME_TO_WAIT = 0.01


class COLORS:
    OKGREEN = '\033[92m' if USE_CONTROL_CHARACTERS else ''
    FAIL = '\033[91m' if USE_CONTROL_CHARACTERS else ''
    END = '\033[0m' if USE_CONTROL_CHARACTERS else ''
