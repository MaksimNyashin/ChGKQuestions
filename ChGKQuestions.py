#!/usr/bin/python3
from my_config import *
import requests
import xml.etree.ElementTree as Et
from sqlite3 import connect
from traceback import print_exc
from threading import Thread
from os import path, system as os_system

# requests, urllib3 instlled to wsl
import re


conn = connect(DB_NAME)
cursor = conn.cursor()


def write_time(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        return_value = func(*args, **kwargs)
        end = time.time()
        if MEASURE_TIME:
            print(f"[DEBUG]:    {func.__qualname__:<20}\t{end-start:.4f}s")
        return return_value

    return wrapper


def update_intrenet_on():
    from time import sleep
    global INTERNET_ON, RUNNING
    cnt = SECONDS_PER_REQUEST - 1
    while RUNNING:
        cnt += 1
        if cnt == SECONDS_PER_REQUEST:
            try:
                req = requests.get("https://db.chgk.info", timeout=3)
                INTERNET_ON = True
            except (requests.ConnectionError, requests.Timeout) as ex:
                INTERNET_ON = False
            cnt = 0
        sleep(1)


def read_text_aloud(txt: str):
    def _read_text(txt: str) -> None:
        # print(txt)
        # return
        readable_text = f'CreateObject("SAPI.SpVoice").Speak "{txt}"'
        with open(READ_ALOUD_FILE, "w") as fo:
            fo.write(readable_text)
        os_system(READ_ALOUD_FILE)

    if not IS_READ_ALOUD:
        return

    txt = txt.replace("\r", "").replace("\n", " ").replace("\"", "\'").replace("«", "\'").replace("»", "\'")
    res = []
    cnt = 0
    b = False
    st = 0
    razd = []
    for ind, c in enumerate(txt):
        if c in '([{<':
            cnt += 1
            if cnt == 1:
                st = ind
            continue
        elif cnt == 0:
            res.append(c)
        elif c in '}])>':
            cnt -= 1
            if cnt == 0:
                mid = txt[st: ind].lower()
                if txt.find("Ведущему", st, ind) == -1:
                    b = True
            continue
        elif cnt == 1:
            razd.append(c)
    _read_text(f'{"Внимание, в вопросе есть раздаточный материал!    " if b else ""}{"".join(res)}')


class Reader:
    _instance=None

    def __init__(self, lines: str):
        global IS_READ_ALOUD
        self._pos = 0
        self._lines = lines.split("\n")
        self._is_read_aloud = IS_READ_ALOUD
        IS_READ_ALOUD = False
        Reader._instance = self

    def input(self, txt: str = "") -> str:
        global IS_READ_ALOUD
        if self._pos + 1 < len(self._lines):
            result = self._lines[self._pos]
            print(f"{txt}{result}")
            self._pos += 1
            if self._pos + 1 == len(self._lines):
                IS_READ_ALOUD = self._is_read_aloud
            return result
        return input(txt)

    @classmethod
    def get_instance(cls):
        return cls._instance


def mid_input(txt: str = "") -> str:
    return Reader.get_instance().input(txt)


def key_input(txt: str, **kwargs) -> str:
    global IS_READ_ALOUD
    while True:
        res = mid_input(f"-> {txt}")
        result = res.lower()
        if result in MUTE_KEYS:
            IS_READ_ALOUD = False
            print("Reading aloud turned off")
        elif result in UNMUTE_KEYS:
            if platform_system == SYSTEM_WINDOWS:
                IS_READ_ALOUD = True
                print("Reading aloud turned on")
        else:
            return res


def run_system_command(cmnd):
    null = {SYSTEM_WINDOWS: "nul"}.get(CURRENT_SYSTEM, "/dev/null")
    return os_system(f"{cmnd} > {null} 2> {null}")


def kill_reading_aloud():
    run_system_command("taskkill /im wscript.exe /f")


class ResultSaver:
    def __init__(self, number: int,  name: str):
        import datetime
        self._number = number
        self._name = name
        self._result = 0
        self._day = datetime.datetime.today().strftime("%d.%m.%Y")
        self._authors = {}
        self._last = 0

    @write_time
    def set_author(self, num: int, author: str) -> None:
        while len(author) > 0 and not('а' <= author[-1] <= 'я'):
            author = author[:-1]
        if 0 < num <= self._number:
            self._authors[author] = self._authors.get(author, 0) | (1 << (num - 1))

    @write_time
    def set_answer(self, num: int, is_suc: bool) -> None:
        if 0 < num <= self._number:
            self._result |= is_suc << (num - 1)
            self._last = max(self._last, num)

    def to_json(self) -> str:
        import json
        return json.dumps(self.__dict__)

    @write_time
    def write(self) -> None:
        with open(path.join(RESULT_DIR, f"{self._name}.json"), "w+") as fo:
            fo.write(self.to_json())
        self._last = -1

    @write_time
    def write_unfinished(self) -> None:
        if self._last == -1:
            res = ""
        res = "\n".join([f"{self._name}\n"] + [f"{self._result >> i & 1}\n" for i in range(self._last)])
        with open(UNFINISHED_FILE, "w") as fo:
            fo.write(res)


def upd(sss):
    return sss.replace("_", "=")


def internet_on():
    return INTERNET_ON


@write_time
def fin_pic(sss):
    prefix = "   !!!: "
    def open_chrome(val) -> bool:
        browsers = [
            ["chrome", "Google Chrome"],
            ["firefox", "Firefox"],
            ["browser", "Yandex Browser"],
            [{SYSTEM_WINDOWS: "start", SYSTEM_LINUX: "xdg-open", SYSTEM_MACOS: "open"}.get(CURRENT_SYSTEM, "Unknown System"), "Default browser"],
        ]
        for browser in browsers:
            com2 = f"{browser[0]} {val}"
            res = run_system_command(com2)
            if res == 0:
                print(f"{prefix}{val} is opened in {browser[1]}")
                return True
        return False

    def copy_to_buffer(val):
        import clipboard
        clipboard.copy(val)
        print(f"{prefix}{val} is copied to buffer")

    if sss is None:
        return

    q = re.findall(RE_SITE, sss)
    q2 = re.findall(RE_DB_SITE, sss)
    if (q is not None and len(q) > 0) or (q2 is not None and len(q2) > 0):
        int_on = internet_on()
        for j in q:
            if int_on:
                try:
                    if not open_chrome(j[0]):
                        copy_to_buffer(j[0])
                except Exception as e:
                    copy_to_buffer(j[0])
            else:
                copy_to_buffer(j[0])
        for j in q2:
            uri = f"https://db.chgk.info/images/db/{j[0]}"
            if int_on:
                try:
                    if not open_chrome(uri):
                        copy_to_buffer(uri)
                except Exception:
                    copy_to_buffer(uri)
            else:
                copy_to_buffer(uri)



def create_table(name, arr):
    name = upd(name)
    cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='%s'""" % name)
    qq = cursor.fetchone()
    print(name, end=": ")
    if qq is None:
        sss = """CREATE TABLE IF NOT EXISTS '%s'(id int, link text)""" % name
        cursor.execute(sss)
        zz = ", ".join(["({0}, \"{1}\")".format(i, upd(arr[i])) for i in range(len(arr))])
        # for i in range(len(arr)):
        #     cursor.execute("""INSERT INTO %s VALUES(?, ?)""" % name, (i, arr[i]))
        #     conn.commit()
        cursor.execute("""INSERT INTO '%s' VALUES %s;""" % (name, zz))
        conn.commit()
        print("added")
    else:
        print("already exists")


@write_time
def read_local(src):
    cur_dir = path.dirname(path.abspath(__file__))
    par_dir = path.dirname(cur_dir)
    lcl_src = path.join(par_dir, "ChGKWordGetter", "src", "%s.xml")
    print(lcl_src % src)
    if not path.isfile(lcl_src % src):
        return DEFAULT_XML
    with open(lcl_src % src, "r", encoding="utf-8") as fo:
        txt = fo.read()
    return txt


@write_time
def read_global(src):
    url = 'https://db.chgk.info/tour/%s/xml'
    print(url % src)
    try:
        req = requests.get(url % src, timeout=2)
        return req.text
    except (requests.ConnectionError, requests.Timeout) as ex:
        return None


def read_page(src=None, name=None):
    if src[0] != "$" and not internet_on():
        read_page("$" + src, "$" + name)
        return
    lcl = False
    if src is None:
        src = ""
        name = "links"
    else:
        if src[0] == "$":
            src = src[1:]
            lcl = True
            name = src[1:]
    if lcl:
        txt = read_local(src)
    else:
        txt = read_global(src)
        if txt is None:
            read_page("$" + src[:-1], "$" + name)
            return

    # pack_src = "pack/%s.xml" % src
    # with codecs.open(pack_src, "w", "utf-8") as fo:
    #     fo.write(r.text)
    #
    # root = et.parse(pack_src).getroot()
    root = Et.fromstring(txt)
    ar = []
    for i in root.findall('tour/TextId'):
        ar.append(i.text)
    # print(ar)
    import random
    if len(ar) > 0:
        create_table(name, ar)
        qw = random.randint(0, len(ar) - 1)
        return read_page(ar[qw], ar[qw])
    else:
        return read_questions(root, src)
        # import webbrowser
        # webbrowser.get("google-chrome").open("https://db.chgk.info/tour/" + src)
    # for i in ar:
    #     read_page(i, i)
    # read_page(ar[0], ar[0])
    # rez = ET.parse()
    # print(r.text)


def read_questions(root, src):
    # @write_time
    def pr(st):
        si = 80
        p = 0
        rz = st.find("</раздатка>")
        beg = 0
        if rz != -1:
            beg = rz + 12
        st = (st[:beg] + st[beg:].replace("\n", " ")).replace("<br>", "\n").replace("<br/>", "\n")

        while p < len(st):
            nx = p + si
            nx = st.rfind(" ", p, nx)
            nxx = st.find("\n", p, nx)
            # print(p, nx, ord(st[nx]))
            if nxx != -1:
                nx = nxx
            if nx != -1 and p + si < len(st):
                print(st[p: nx])
            else:
                print(st[p:])
                break
            p = nx + 1

    @write_time
    def get_parent_title():
        parent_src = src.rsplit(".", 1)[0]
        if INTERNET_ON:
            xml_text = read_global(parent_src)
        else:
            xml_text = read_local(parent_src)
        root = Et.fromstring(xml_text)
        title = next(root.iter("Title"), None)
        return title.text if title is not None else UNKNOWN_PACKAGE

    @write_time
    def get_next_tour():
        if src.find(".", 0, -1) == -1:
            return None
        parent_src, tour_num = src.rsplit(".", 1)
        tour_num = int(tour_num) + 1
        if INTERNET_ON:
            xml_text = read_global(parent_src)
        else:
            xml_text = read_local(parent_src)
        root = Et.fromstring(xml_text)
        tours = root.findall("tour/Number")
        return f"{parent_src}.{tour_num}" if (tour_num) in [int(t.text) for t in tours] else None


    title = next(root.iter("Title"), None)
    if title is None:
        print("Error: Not found package with such name")
        return None
    print("\n\t\t\t", get_parent_title(), root.find("Title").text)

    ff = root.findall("question")
    num = len(ff)
    result_saver = ResultSaver(num, root.find("TextId").text)
    right, total = 0, 0
    try:
        for i in ff:
            total += 1
            quest_number = (int(i.find('Number').text) - 1) % num + 1

            quest = i.find('Question').text
            tx = f"{quest_number}/{num}) {quest}"
            reading = Thread(target=read_text_aloud, args=(quest,))
            reading.start()
            fin_pic(tx)
            pr(tx)
            mid_input()
            kill_reading_aloud()
            reading.join()

            answer = i.find('Answer').text
            fin_pic(answer)
            pr(f"Ответ: {answer}")

            pass_criteria = i.find('PassCriteria').text
            fin_pic(pass_criteria)
            pr(f"Зачёт: {pass_criteria}")

            com = f"Комментарий: {i.find('Comments').text}"
            fin_pic(com)
            pr(com)

            pr(f"Автор: {i.find('Authors').text}")
            result_saver.set_author(quest_number, " ".join(i.find("Authors").text.split(' ', 2)[:2]))
            
            saved = False
            while True:
                if not saved:
                    inp = key_input("Сохранить или взят> ")
                    if inp == "save" or ("сохранить".startswith(inp) and len(inp) > 1) or inp == "ыфму":
                        tmp_src = src
                        if tmp_src[-1] == ".":
                            tmp_src = tmp_src[:-1]
                        if tmp_src[-1] != "/":
                            tmp_src += "/"
                        z = tmp_src + i.find("Number").text
                        with open(GOOD_FILE, "a+") as fo:
                            fo.write(z + ";")
                        print(z)
                        saved = True
                        continue
                else:
                    inp = key_input("Взят> ")
                if inp in ("0", "1"):
                    result_saver.set_answer(quest_number, int(inp))
                    if inp == "1":
                        right += 1
                    break

            print(f"Взято: {right}/{total}\n")

        print(result_saver.to_json())
        result_saver.write()
        result_saver.write_unfinished()
        mid_input("Игра окончена")
        return get_next_tour()
    except Exception as e:
        print(e)
        result_saver.write_unfinished()
        # raise e
        return None
    except KeyboardInterrupt as ki:
        result_saver.write_unfinished()
        raise ki



if __name__ == '__main__':
    # fin_pic("<Question>[Раздаточный материал: (pic: https://i.imgur.com/huytXYR.png)] Интересно, что один бакенбард этого персонажа компьютерной игры меньше другого, что хорошо заметно и в момент превращения. Назовите имя этого персонажа.</Question>")

    # read_page()
    # s = u20let.1
    # question 6 - 2 images from database, 8 - razdatka
    # s = "balt20-1_u.2"
    # s = "mosstud19_u.2"
    # s = "ZelShum2_u.1"
    # s = "mkm17.6"

    try:
        check_connection = Thread(target=update_intrenet_on)
        check_connection.start()
        next_tour = None
        
        if os_path.exists(UNFINISHED_FILE):
            with open(UNFINISHED_FILE, "r") as fi:
                inp = fi.read()
            pack = inp.split('\n', 1)[0]
            if AUTOPLAY_UNFINSHED or inp == "" or input(f"Press ENTER if you want to continue playing {pack}: ") == "":
                Reader(inp)
            else:
                Reader("")
        else:
            Reader("")

        while True:
            s = None
            if next_tour is None:
                pac = key_input("Package: ")
            else:
                pac = next_tour
            if pac != "":
                s = pac
            next_tour = read_page(s, s)
            if next_tour is not None:
                if key_input(f"Press ENTER to play '{next_tour}': ") != "":
                    next_tour = None
            if next_tour is None and key_input("Press ENTER to play one more time: ") != "":
                break
            print("\n\n")
    except Exception as e:
        print_exc()
        mid_input(f"ERROR: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        RUNNING = False
        kill_reading_aloud()
        check_connection.join()
    # read_page("ovsch20.3_u.1", "ovsch20.3_u.1")
    # cursor.execute("""SELECT * FROM links""")
    # print(cursor.fetchall())
    # https://db.chgk.info/tour/holgo2011_u.2/xml
    
# DONE add playing by package name
# DONE add playing from inner memory
# ---TDOD print name of authors before first question
# DONE print name of authors after each question
# DONE: add jsom saver of each game(tour)
# DONE: play another game after finish
# DONE: add timer in debug mode for each function
# DONE: remove waiting while checking internet connection (while offline)
# DONE: fix saving when between package and number dot or nothing instead of slash
# DONE: fix playing online with unknown package not from base (problems with parent and receiving package name)
# DONE: fix unknown name of packages not from local base
# DONE: Added playing next tour from same tournament by default
# DONE: search pics in answer (ruch19st_u.1/5)
# DONE: check if chrome dosn't exist and do something if don't
# DONE: remove output and error output from system while copying
# DONE: make chrome opening crossplatform
# DONE: Added opening images in Firefox and Yandex browser
# DONE: Added opening images in default browser
# DONE: Added reading questions aloud (only on Windows)
# DONE: Fixed issue with finding pics in None
# DONE: Added key_input to read user keys
# DONE: Added muting and unmiuting reading aloud (between questions)
# DONE: Added interruptions to reading questions aloud
# DONE: Added exception handler when there is no such package
# DONE: Added saving unfinished game after exception (to paste the result and skip played questions)
# DONE: Added reading and auto-playing from saved unfinished game
# TODO: remove opening images while auto-playing
# TODO: add processing handouts while reading (can be used in game mode) (intvor_19.1_u.4/45, ovsch10.2-18, ...)
# TODO: add game mode (timer, no text, only reading aloud and pictures)
# TODO: add duplets and blitz to reading
