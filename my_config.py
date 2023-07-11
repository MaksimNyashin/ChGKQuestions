from re import compile as re_compile, IGNORECASE as re_IGNORECASE
from os import path as os_path, mkdir as os_mkdir
from platform import system as platform_system

CURRENT_SYSTEM = platform_system()

SYSTEM_WINDOWS = "Windows"
SYSTEM_LINUX = "Linux"
SYSTEM_MACOS = "Darwin"

if CURRENT_SYSTEM == SYSTEM_WINDOWS:
    import colorama
    colorama.init()

DEBUG = False
MEASURE_TIME = False and DEBUG
SUPPRESS_AUTOSAVE = True and DEBUG
SUPPESS_PICS = True and DEBUG

IS_READ_ALOUD = False and CURRENT_SYSTEM == SYSTEM_WINDOWS
AUTOPLAY_UNFINSHED = True

RE_SITE = re_compile("(https?://[a-zA-Z\d./_-]*\.(png|jpg|jpeg|gif|bmp))", re_IGNORECASE)
RE_DB_SITE = re_compile("pic:[ \n](\d+\.(png|jpg|jpeg|gif|bmp))", re_IGNORECASE)
RE_RAZDATOCHNYI_MATERIAL = re_compile("\s*\[Раздаточный материал: (.+)\]")
RE_RAZDATKA = re_compile("\s*<раздатка>(.+)<\/раздатка>")

INTERNET_ON = False
RUNNING = True
SECONDS_PER_REQUEST = 15

CURRENT_DIR = os_path.dirname(os_path.abspath(__file__))
TMP_DIR = os_path.join(CURRENT_DIR, "tmp")
READ_ALOUD_FILE = os_path.join(TMP_DIR, "read.vbs")
UNFINISHED_FILE = os_path.join(TMP_DIR, "unfinished.txt")
LOCAL_LIBRARY_DIR = os_path.join(os_path.dirname(CURRENT_DIR), "ChGKWordGetter", "src")
LOCAL_LIBRARY_FILE = os_path.join(LOCAL_LIBRARY_DIR, "%s.xml")
RESULT_DIR = os_path.join(CURRENT_DIR, "results")
GOOD_FILE = os_path.join(CURRENT_DIR, "good.txt")
FOLDERS_TO_CREATE = (RESULT_DIR, TMP_DIR)

for folder in FOLDERS_TO_CREATE:
    if not os_path.exists(folder):
        os_mkdir(folder)

DB_NAME = "mydatabase.db"

UNKNOWN_PACKAGE = "Unknown package"
DEFAULT_XML = f"<tournament><Title>{UNKNOWN_PACKAGE}</Title></tournament>"

MUTE_KEYS = ("-m", "-ь")
UNMUTE_KEYS = ("-u", "-um", "-г", "-гь")
