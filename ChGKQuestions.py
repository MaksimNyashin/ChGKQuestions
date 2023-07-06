#!/usr/bin/python3
import requests
import xml.etree.ElementTree as Et
from sqlite3 import connect
from traceback import print_exc
from threading import Thread
from os import path, mkdir, system as os_system

# requests, urllib3 instlled to wsl

conn = connect("mydatabase.db")
cursor = conn.cursor()

from sys import stderr
import re

DEBUG = False
MEASURE_TIME = True and DEBUG
RE_SITE = re.compile("(https?://[a-zA-Z\d./_-]*\.(png|jpg|jpeg|gif|bmp))", re.IGNORECASE)
RE_DB_SITE = re.compile("pic:[ \n](\d+\.(png|jpg|jpeg|gif|bmp))", re.IGNORECASE)
INTERNET_ON = False
RUNNING = True
SECONDS_PER_REQUEST = 15
RESULT_FOLDER = path.join(path.dirname(path.abspath(__file__)), "results")

if not path.exists(RESULT_FOLDER):
    mkdir(RESULT_FOLDER)


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



class ResultSaver:
    def __init__(self, number: int,  name: str):
        import datetime
        self._number = number
        self._name = name
        self._result = 0
        self._day = datetime.datetime.today().strftime("%d.%m.%Y")
        self._authors = {}

    @write_time
    def set_author(self, num: int, author: str) -> None:
        if author[-1] == ",":
            author = author[:-1]
        if 0 < num <= self._number:
            self._authors[author] = self._authors.get(author, 0) | (1 << (num - 1))

    @write_time
    def set_answer(self, num: int, is_suc: bool) -> None:
        if is_suc and 0 < num <= self._number:
            self._result |= 1 << (num - 1)

    def to_json(self) -> str:
        import json
        return json.dumps(self.__dict__)

    @write_time
    def write(self) -> None:
        with open(path.join(RESULT_FOLDER, f"{self._name}.json"), "w+") as fo:
            fo.write(self.to_json())


def upd(sss):
    return sss.replace("_", "=")


def internet_on():
    return INTERNET_ON


@write_time
def fin_pic(sss):
    prefix = "   !!!: "
    def open_chrome(val) -> bool:
        from platform import system as platform_system
        current_system = platform_system()
        browsers = [
            ["chrome", "Google Chrome"],
            ["firefox", "Firefox"],
            ["browser", "Yandex Browser"],
            [{"Windows": "start", "Linux": "xdg-open", "Darwin": "open"}.get(current_system, "Unknown System"), "Default browser"],
        ]
        null = {"Windows": "nul"}.get(current_system, "/dev/null")
        for browser in browsers:
            com2 = f"{browser[0]} {val} > {null} 2> {null}"
            res = os_system(com2)
            if res == 0:
                print(f"{prefix}{val} is opened in {browser[1]}")
                return True
        return False

    def copy_to_buffer(val):
        import clipboard
        clipboard.copy(val)
        print(f"{prefix}{val} is copied to buffer")

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
        return "<tournament><Title>Unknown package</Title></tournament>"
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
        read_page(ar[qw], ar[qw])
    else:
        read_questions(root, src)
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
        return root.find("Title").text

    print("\n\t\t\t", get_parent_title(), root.find("Title").text)

    ff = root.findall("question")
    num = len(ff)
    result_saver = ResultSaver(num, root.find("TextId").text)
    right, total = 0, 0
    for i in ff:
        total += 1
        quest_number = (int(i.find('Number').text) - 1) % num + 1
        tx = f"{quest_number}/{num}) {i.find('Question').text}"
        fin_pic(tx)
        pr(tx)
        input()
        answer = i.find('Answer').text
        fin_pic(answer)
        pr(f"Ответ: {answer}")
        pass_criteria = i.find('PassCriteria').text
        pr(f"Зачёт: {pass_criteria}")
        com = f"Комментарий: {i.find('Comments').text}"
        fin_pic(com)
        pr(com)
        pr(f"Автор: {i.find('Authors').text}")
        result_saver.set_author(quest_number, " ".join(i.find("Authors").text.split(' ', 2)[:2]))
        saved = False
        while True:
            if not saved:
                inp = input("Сохранить или взят> ")
                if inp == "save" or ("сохранить".startswith(inp) and len(inp) > 1) or inp == "ыфму":
                    tmp_src = src
                    if tmp_src[-1] == ".":
                        tmp_src = tmp_src[:-1]
                    if tmp_src[-1] != "/":
                        tmp_src += "/"
                    z = tmp_src + i.find("Number").text
                    with open("good.txt", "a+") as fo:
                        fo.write(z + ";")
                    print(z)
                    saved = True
                    inp = input("Взят> ")
            else:
                inp = input("Взят> ")
            if inp in ("0", "1"):
                result_saver.set_answer(quest_number, int(inp))
                if inp == "1":
                    right += 1
                break
        print(f"Взято: {right}/{total}\n")
    print(result_saver.to_json())
    result_saver.write()
    input("Игра окончена")


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
        while True:
            s = None
            pac = input("Package: ")
            if pac != "":
                s = pac
            read_page(s, s)
            if input("Press ENTER to play one more time: ") != "":
                break
            print("\n\n")
    except Exception as e:
        print_exc()
        input(f"ERROR: {e}")
    finally:
        RUNNING = False
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
# TODO: play next tour from same tournament by default
# DONE: search pics in answer (ruch19st_u.1/5)
# DONE: check if chrome dosn't exist and do something if don't
# DONE: remove output and error output from system while copying
# DONE: make chrome opening crossplatform
# DONE: Added opening images in Firefox and Yandex browser
# DONE: Added opening images in default browser
