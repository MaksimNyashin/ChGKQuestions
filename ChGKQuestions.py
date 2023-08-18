#!/usr/bin/python3
from my_config import *
import requests
import xml.etree.ElementTree as Et
from traceback import format_exc
from threading import Thread
from os import path, system as os_system
from abc import ABC
from typing import Tuple, List

# requests, urllib3 instlled to wsl
import re


def write_time(func):
    import time

    def wrapper(*args, **kwargs):
        start = time.time()
        return_value = func(*args, **kwargs)
        end = time.time()
        if MEASURE_TIME:
            my_print(f"[DEBUG]:    {func.__qualname__:<20}\t{end-start:.4f}s")
        return return_value

    return wrapper


def update_intrenet_on():
    from time import sleep

    global INTERNET_ON, RUNNING
    cnt = SECONDS_PER_REQUEST - 1
    try:
        while RUNNING:
            cnt += 1
            if cnt == SECONDS_PER_REQUEST:
                if not FORCE_LOCAL():
                    try:
                        req = requests.get(DB_CHGK, timeout=3)
                        INTERNET_ON = True
                    except (requests.ConnectionError, requests.Timeout) as ex:
                        INTERNET_ON = False
                cnt = 0
            sleep(1)
    except Exception as e:
        my_print(format_exc(), silent=True)
        mid_input(f"ERROR: {e}")
    except KeyboardInterrupt:
        my_print("update_internet_on: Ctrl+C")
        pass


class TransNode:
    def __init__(self, word_num: int, dep: int):
        self._children = dict()
        self._suf = None
        self._term = False
        self._change = None
        self._word_num = word_num
        self._dep = dep
        self._root = None

        # root only
        self._letters = set()
        self._words = []

    def __str__(self):
        return f"term={self._term}, change={self._change!r}, word={self._root._words[self._word_num]!r}, dep={self._dep}, pref={self._root._words[self._word_num][:self._dep]!r}"

    def _get_child(self, ch, default):
        return self._children.get(ch, default)

    def add_str(self, word, change):
        from re import sub

        word = sub("\s+", ' ', word).strip()
        root = self
        word_num = len(root._words)
        root._words.append(word)

        cur = root
        for ind, let in enumerate(word):
            root._letters.add(let)
            if cur._children.get(let, None) is None:
                cur._children[let] = TransNode(word_num, ind + 1)
            cur = cur._children[let]
            cur._root = root
        cur._term = True
        cur._change = change

    def build_aho(self):
        from collections import deque

        root = self
        preroot = TransNode(-1, 0)
        root._suf = preroot
        preroot._suf = preroot

        q = deque()
        q.append(root)
        while len(q) > 0:
            cur = q.popleft()

            for let in root._letters:
                if cur._children.get(let, None) is not None:
                    cur._children[let]._suf = cur._suf._get_child(let, root)
                    q.append(cur._children[let])
                else:
                    cur._children[let] = cur._suf._get_child(let, root)

    def go(self, txt: str):
        root = self
        cur = root

        res = []
        for let in txt:
            nxt = cur._get_child(let, root)
            if nxt is cur:
                res.append(let)
            elif nxt._term:
                res.append(nxt._change)
                nxt = root
            elif nxt._dep <= cur._dep:
                cur_word = root._words[cur._word_num]
                res.append(cur_word[: cur._dep - nxt._dep])
                if nxt is root:
                    res.append(let)
                else:
                    res.append(cur_word[cur._dep - nxt._dep])
            cur = nxt
        return "".join(res)

    @classmethod
    def init(cls, txt):
        from re import compile, findall, DOTALL

        c = compile("([\"']?[a-zA-Z][^а-яА-ЯёЁ\[]*[^\sа-яА-ЯёЁ\[])\s*\[([^\]]+)\]", DOTALL)
        root = TransNode(0, 0)
        root._root = root
        for i in findall(c, txt):
            root.add_str(*i)
        root.build_aho()
        return root


class Reader:
    _instances = []

    def __init__(self, lines: str):
        self._pos = 0
        self._lines = lines.split("\n")
        if self.is_auto_playing():
            add_layer(LAYERS.READER)
            IS_READ_ALOUD(False)
            SUPPESS_PICS(True)
        Reader._instances.append(self)
        with open(COMMAND_HISTORY_LOG_FILE, "w"):
            pass

    def input(self, txt: str = "") -> str:
        res = self._input(txt)
        with open(COMMAND_HISTORY_LOG_FILE, "a", encoding="utf-8") as fo:
            fo.write(f"{res}\n")
        return res

    def _input(self, txt) -> str:
        if self.is_auto_playing():
            result = self._lines[self._pos]
            my_print(f"{txt}{result}")
            self._pos += 1
            if not self.is_auto_playing():
                pop_layer(LAYERS.READER)
            return result
        inp_res = input(txt)
        my_print(f"{txt}{inp_res}", silent=True)
        return inp_res

    def is_auto_playing(self) -> bool:
        return self._pos + 1 < len(self._lines)

    @classmethod
    def get_instance(cls):
        if len(cls._instances) == 0:
            cls("\n" * 1000)
        return cls._instances[-1]


def mid_input(txt: str = "") -> str:
    return Reader.get_instance().input(txt)


def key_input(txt: str, **kwargs) -> str:
    while True:
        res = mid_input(f"-> {txt}")
        result = res.lower()
        if result in MUTE_KEYS:
            if IS_READ_ALOUD():
                pop_layer(LAYERS.KEY_READ_ALOUD)
                my_print("Reading aloud turned off")
            else:
                my_print("Reading aloud is already turned off")
        elif result in UNMUTE_KEYS:
            if CURRENT_SYSTEM == SYSTEM_WINDOWS:
                if not IS_READ_ALOUD():
                    add_layer(LAYERS.KEY_READ_ALOUD)
                    IS_READ_ALOUD(True)
                    my_print("Reading aloud turned on")
                else:
                    my_print("Reading aloud is already turned on")
            else:
                my_print("Reading aloud is not supported yet on your OS")
        elif result in DEBUG_TESTS_KEYS:
            if LOCAL_LIBRARY_FILE() == TEST_SOURCE_FILE:
                pop_layer(LAYERS.LOCAL_LIBRARY)
                my_print("Local library is Local library")
            else:
                add_layer(LAYERS.LOCAL_LIBRARY)
                LOCAL_LIBRARY_FILE(TEST_SOURCE_FILE)
                my_print("Local library is Tests")
        elif result in SUPPRESS_AUTOSAVE_KEYS:
            add_layer(LAYERS.SUPPRESS_AUTOSAVE)
            if SUPPRESS_AUTOSAVE():
                SUPPRESS_AUTOSAVE(False)
                my_print("Autosave Suppression is turned OFF")
            else:
                SUPPRESS_AUTOSAVE(True)
                my_print("Autosave Suppression is turned ON")
        else:
            return res


class BaseQuestion(ABC):
    def __init__(self, txts: Tuple[str, ...], **kwargs):
        self._question_texts = txts
        self._current_ind = 0
        self._trans_node_root = None
        self._init_trans_node()
        self._after_txt = [
            f"Ответ: {kwargs.get('Answer', '')}",
            f"Зачёт: {kwargs.get('PassCriteria', '')}",
            f"Комментарий: {kwargs.get('Comments', '')}",
            f"Автор: {kwargs.get('Authors', '')}",
        ]

    def _get_current(self) -> str:
        return (
            self._question_texts[self._current_ind]
            if self._current_ind < len(self._question_texts)
            else self._after_txt[self._current_ind - len(self._question_texts)]
        )

    def _init_trans_node(self) -> None:
        self._trans_node_root = TransNode.init(" ".join(self._question_texts))

    def find_pictures(self) -> List[str]:
        text = self._get_current()
        if SUPPESS_PICS() or text is None:
            return []

        return [i[0] for i in re.findall(RE_SITE, text)] + [
            f"{DB_CHGK}/images/db/{i[0]}" for i in re.findall(RE_DB_SITE, text)
        ]

    def get_audio_text(self) -> str:
        text = self._trans_node_root.go(self._get_current()).translate(
            str.maketrans(
                {
                    "\r": "",
                    "\n": " ",
                    "\"": "\'",
                    "«": "\'",
                    "»": "\'",
                    "\u0301": "",
                }
            )
        )
        text = text.replace("<раздатка>", "<").replace("</раздатка>", ">")
        res = []
        cnt = 0
        for c in text:
            if c in '([{<':
                cnt += 1
            elif cnt == 0:
                res.append(c)
            elif c in '}])>':
                cnt -= 1
        return re.sub("\s\s+", " ", ''.join(res).strip())

    def get_handouts(self) -> List[str]:
        return re.findall(RE_RAZDATOCHNYI_MATERIAL, self._get_current()) + re.findall(RE_RAZDATKA, self._get_current())

    def has_pictures(self) -> bool:
        return len(re.findall(RE_SITE, self._get_current())) + len(re.findall(RE_DB_SITE, self._get_current())) > 0

    def _print_text(self, offset) -> None:
        self.write_text_with_width(self._get_current(), offset=offset)

    @staticmethod
    def _read_text(text) -> None:
        if SUPPRESS_READING():
            return
        readable_text = f'CreateObject("SAPI.SpVoice").Speak "{text}"'
        with open(READ_ALOUD_FILE, "w") as fo:
            fo.write(readable_text)
        os_system(READ_ALOUD_FILE)

    def run_countdown(self, start_time: int, countdown_time: int) -> None:
        from time import sleep

        if RUN_COUNTDOWN():
            for i in range(countdown_time + 1):
                if not GAME_RUNNING:
                    my_print()
                    return
                current_time = start_time - i
                my_print(f"\r{current_time // 60}:{current_time % 60:0>2}", end='', flush=True)
                sleep(1)
            countdown_end = "Время вышло, сдавайте ваши ответы"
            my_print(f"\r{countdown_end}")
            self._read_text(f"ПИИИИИП! {countdown_end}")

    @staticmethod
    def show_pictures(pictures: List[str]) -> None:
        prefix = "   !!!: "

        def open_browser(val) -> bool:
            browsers = [
                ["chrome", "Google Chrome"],
                ["firefox", "Firefox"],
                ["browser", "Yandex Browser"],
                [
                    {SYSTEM_WINDOWS: "start", SYSTEM_LINUX: "xdg-open", SYSTEM_MACOS: "open"}.get(
                        CURRENT_SYSTEM, "Unknown System"
                    ),
                    "Default browser",
                ],
            ]
            for browser in browsers:
                com2 = f"{browser[0]} {val}"
                res = run_system_command(com2)
                if res == 0:
                    my_print(f"{prefix}{val} is opened in {browser[1]}")
                    return True
            return False

        def copy_to_buffer(val) -> None:
            import clipboard

            clipboard.copy(val)
            my_print(f"{prefix}{val} is copied to buffer")

        int_on = is_internet_on()
        for pic in pictures:
            if int_on:
                try:
                    if not open_browser(pic):
                        copy_to_buffer(pic)
                except Exception as e:
                    copy_to_buffer(pic)
            else:
                copy_to_buffer(pic)

    @staticmethod
    def write_text_with_width(text, offset: int) -> None:
        width = CONSOLE_WIDTH
        current_postion = 0
        handout_end = text.find("</раздатка>")
        # TODO: add other handout types
        start_index = 0
        if handout_end != -1:
            start_index = handout_end + 12
        text = (text[:start_index] + text[start_index:].replace('\n', ' ')).replace('<br>', '\n').replace('<br/>', '\n')

        while current_postion < len(text):
            next_position = text.rfind(" ", current_postion, current_postion + width - offset)
            new_line_next_postion = text.find("\n", current_postion, next_position)
            if new_line_next_postion != -1:
                next_position = new_line_next_postion
            if next_position != -1 and current_postion + width <= len(text):
                my_print(text[current_postion:next_position])
            else:
                my_print(text[current_postion:])
                break
            current_postion = next_position + 1
            offset = 0

    def process_reading_aloud(self, start_time: int, countdown_time: int) -> None:
        global GAME_RUNNING
        try:
            if IS_READ_ALOUD():
                has_handouts_or_pics = (len(self.get_handouts()) > 0) or self.has_pictures()
                str_to_read = f'{"Внимание, в вопросе есть раздаточный материал!    " if has_handouts_or_pics else ""}{self.get_audio_text()}'

                if SUPPRESS_READING():
                    from time import sleep

                    sleep(TIME_TO_WAIT)
                    my_print(f"READING:\n'''{str_to_read}'''")
                else:
                    self._read_text(str_to_read)

            GAME_RUNNING = True
            if countdown_time > 0:
                self.run_countdown(start_time, countdown_time)
        except Exception as e:
            my_print(format_exc(), silent=True)
            mid_input(f"ERROR: {e}")
        except KeyboardInterrupt:
            my_print("read_text_aloud: Ctrl+C")

    def process_question(self, prefix: str, quest_number: int, result_saver):
        start_countdown = sum(self._TIME)
        my_print(prefix, end="")

        for ind, quest in enumerate(self._question_texts):
            global GAME_RUNNING
            self._current_ind = ind

            self.show_pictures(self.find_pictures())

            if not SUPPRESS_TEXT():
                self._print_text(offset=len(prefix) if ind == 0 else 0)
            else:
                handouts = ' '.join(f'[{val}]' for val in self.get_handouts(quest))
                self.write_text_with_width(handouts, offset=0)

            reading = Thread(
                target=self.process_reading_aloud,
                args=(start_countdown, self._TIME[self._current_ind]),
            )
            reading.start()

            mid_input()
            kill_reading_aloud()
            GAME_RUNNING = False
            reading.join()

        for text in self._after_txt:
            self._current_ind += 1
            self.show_pictures(self.find_pictures())

            self._print_text(offset=0)

        result_saver.set_author(quest_number, " ".join(self._after_txt[-1].split(' ', 3)[1:3]))

    @staticmethod
    def generate_question(root: Et.Element):
        question_text = root.find('Question').text
        dct = dict([(name, root.find(name).text) for name in ('Answer', 'PassCriteria', 'Comments', 'Authors')])
        # TODO: add duplets and blitz
        return SingleQuestion.generate(question_text, **dct)


class SingleQuestion(BaseQuestion):
    _TIME = (60,)

    @classmethod
    def generate(cls, txt: str, **kwargs):
        return cls((txt,), **kwargs)


class DupletQuestion(BaseQuestion):
    _TIME = (0, 30, 30)

    @classmethod
    def generate(cls, pretext: str, quest1: str, quest2: str, **kwargs):
        return cls((pretext, quest1, quest2), **kwargs)


def update_src(text: str) -> str:
    return text.replace(CURRENT_DIR, "CURRENT_DIR").replace(PARENT_DIR, "PARENT_DIR").replace('\\', '/')


def my_print(*args, **kwargs):
    if kwargs.get("silent", False) != True:
        kwargs.pop('silent', None)
        print(*args, **kwargs)
    if not WRITE_TESTS_OUTPUT():
        return
    result = kwargs.get("sep", ' ').join(str(arg) for arg in args) + kwargs.get("end", '\n')
    with open(TMP_TESTS_FILE, "a", encoding="utf-8") as fo:
        fo.write(result.replace('\r', '\\r'))


def run_system_command(cmnd):
    null = {SYSTEM_WINDOWS: "nul"}.get(CURRENT_SYSTEM, "/dev/null")
    return os_system(f"{cmnd} > {null} 2> {null}")


def kill_reading_aloud():
    run_system_command("taskkill /im wscript.exe /f")


class ResultSaver:
    def __init__(self, number: int, name: str):
        import datetime

        self._number = number
        self._name = name
        self._result = 0
        if UNIFY_DATE():
            self._day = DEFAULT_DATE.strftime("%d.%m.%Y")
        else:
            self._day = datetime.datetime.today().strftime("%d.%m.%Y")
        self._authors = {}
        self._last = 0

    @write_time
    def set_author(self, num: int, author: str) -> None:
        while len(author) > 0 and not ('а' <= author[-1] <= 'я'):
            author = author[:-1]
        if 0 < num <= self._number:
            self._authors[author] = self._authors.get(author, 0) | (1 << (num - 1))

    @write_time
    def set_answer(self, num: int, is_suc: bool) -> None:
        if 0 < num <= self._number:
            self._result |= is_suc << (num - 1)
            self._last = max(self._last, num)

    def to_json(self) -> str:
        from json import dumps

        return dumps(self.__dict__)

    @write_time
    def write(self) -> None:
        if not SUPPRESS_RESULTS():
            with open(path.join(RESULT_DIR, f"{self._name}.json"), "w+") as fo:
                fo.write(self.to_json())
        self._last = -1

    @write_time
    def write_unfinished(self) -> None:
        if SUPPRESS_AUTOSAVE():
            return
        if self._last == -1:
            res = ""
        else:
            res = "\n".join([f"{self._name}\n"] + [f"{self._result >> i & 1}\n" for i in range(self._last)])
        with open(UNFINISHED_FILE_WRITE, "w") as fo:
            fo.write(res)


def is_internet_on():
    return INTERNET_ON and not FORCE_LOCAL()


@write_time
def read_local(src, silent=False):
    if not exists_local(src):
        return DEFAULT_XML
    if path.exists(LOCAL_LIBRARY_FILE() % src):
        lcl_src = LOCAL_LIBRARY_FILE() % src
    elif path.exists(PACKAGE_CACHE_FILE % src):
        lcl_src = PACKAGE_CACHE_FILE % src
    my_print(update_src(lcl_src), silent=silent)
    with open(lcl_src, "r", encoding="utf-8") as fo:
        return fo.read()


@write_time
def read_global(src, silent=False):
    if exists_local(src):
        return read_local(src)
    uri = f'{DB_CHGK}/tour/%s/xml'
    my_print(uri % src, silent=silent)
    try:
        req = requests.get(uri % src, timeout=2)
        if SAVE_CACHE_PACKAGE():
            with open(PACKAGE_CACHE_FILE % src, "w", encoding="utf-8") as fo:
                fo.write(req.text)
        return req.text
    except (requests.ConnectionError, requests.Timeout) as ex:
        global INTERNET_ON
        INTERNET_ON = False
        return None


def read_page(src=None, name=None):
    if src[0] != "$" and not is_internet_on():
        return read_page("$" + src, "$" + name)
    lcl = False
    if src is None:
        src = ""
        name = "links"
    else:
        if src[0] == "$":
            src = src[1:]
            lcl = True
            name = src[1:]
    if lcl or not is_internet_on():
        txt = read_local(src)
    else:
        txt = read_global(src)
        if txt is None:
            return read_page("$" + src, "$" + name)

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
        qw = random.randint(0, len(ar) - 1)
        return read_page(ar[qw], ar[qw])
    else:
        return read_questions(root, src)
        # import webbrowser
        # webbrowser.get("google-chrome").open(f"{DB_CHGK}/tour/{src}")
    # for i in ar:
    #     read_page(i, i)
    # read_page(ar[0], ar[0])
    # rez = ET.parse()
    # print(r.text)


def exists_local(filename) -> bool:
    return path.exists(PACKAGE_CACHE_FILE % filename) or path.exists(LOCAL_LIBRARY_FILE() % filename)


def read_questions(root, src):
    parent_xml = None

    @write_time
    def get_parent_xml(parent_src, silent=False):
        nonlocal parent_xml
        if parent_xml is None:
            if is_internet_on():
                txt = read_global(parent_src, silent)
            else:
                txt = read_local(parent_src, silent)
            parent_xml = Et.fromstring(txt)
        return parent_xml

    @write_time
    def get_parent_title():
        parent = root.find("ParentTextId")
        return parent.text if parent is not None else UNKNOWN_PACKAGE

    @write_time
    def get_next_tour(silent=False):
        if src.find(".", 0, -1) == -1:
            return None
        parent_src, tour_num = src.rsplit(".", 1)
        tour_num = int(tour_num) + 1
        root = get_parent_xml(parent_src, silent)
        tours = root.findall("tour/Number")
        lst = [int(t.text) for t in tours]
        for num in lst:
            if not exists_local(f"{parent_src}.{num}"):
                Thread(target=read_global, args=(f"{parent_src}.{num}", True)).start()
        return f"{parent_src}.{tour_num}" if tour_num in lst else None

    title = next(root.iter("Title"), None)
    if title is None or title.text == UNKNOWN_PACKAGE:
        if not is_internet_on():
            my_print("Error: Internet is off and the package with such name wasn't found in the local library")
        else:
            my_print(f"Error: The package with such name wasn't found at {DB_CHGK}")
        return None
    my_print("\n\t\t\t", get_parent_title(), title.text)

    ff = root.findall("question")
    num = len(ff)
    result_saver = ResultSaver(num, root.find("TextId").text)
    right, total = 0, 0
    Thread(target=get_next_tour, args=(True,))
    try:
        for i in ff:
            total += 1
            quest_number = (int(i.find('Number').text) - 1) % num + 1

            prefix = f"{quest_number}/{num}) "

            question = BaseQuestion.generate_question(i)
            question.process_question(prefix, quest_number, result_saver)

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
                        if not SUPPRESS_GOOD():
                            with open(GOOD_FILE, "a+") as fo:
                                fo.write(z + ";")
                        my_print(f"Saved as {z}")
                        saved = True
                        continue
                else:
                    inp = key_input("Взят> ")
                if inp in ("0", "1"):
                    result_saver.set_answer(quest_number, int(inp))
                    if inp == "1":
                        right += 1
                    break

            my_print(f"Взято: {right}/{total}\n")

        my_print(result_saver.to_json())
        result_saver.write()
        result_saver.write_unfinished()
        mid_input("Игра окончена")
        return get_next_tour()
    except Exception as e:
        my_print(e)
        result_saver.write_unfinished()
        return None
    except KeyboardInterrupt as ki:
        result_saver.write_unfinished()
        raise ki


def main():
    global GAME_RUNNING, RUNNING
    try:
        check_connection = None
        init_testing()
        init_debug()
        init_game()

        check_connection = Thread(target=update_intrenet_on)
        check_connection.start()
        next_tour = None
        my_print(update_src(sys_argv[0]), *(sys_argv[1:]), silent=True)

        if os_path.exists(UNFINISHED_FILE_READ()):
            with open(UNFINISHED_FILE_READ(), "r") as fi:
                inp = fi.read()
            if (
                AUTOPLAY_UNFINSHED()
                or inp == ""
                or input(f"Press ENTER if you want to continue playing the last unfinished package: ") == ""
            ):
                Reader(inp)
                if AUTOPLAY_UNFINSHED():
                    if not FORCE_LOCAL():
                        my_print("Looking for unfinished game...", end="", flush=True)
                        from time import sleep

                        sleep(1.3)
                        if USE_CONTROL_CHARACTERS:
                            my_print(end="\r\033[K")
                        else:
                            my_print(f"\r{' '*30}\r", end="")
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
            my_print("\n\n")
    except Exception as e:
        my_print(format_exc(), silent=True)
        mid_input(f"ERROR: {e}")
    except KeyboardInterrupt:
        my_print("Ctrl+C")
    finally:
        RUNNING = False
        GAME_RUNNING = False
        kill_reading_aloud()
        if check_connection is not None:
            check_connection.join()


if __name__ == '__main__':
    # fin_pic("<Question>[Раздаточный материал: (pic: https://i.imgur.com/huytXYR.png)] Интересно, что один бакенбард этого персонажа компьютерной игры меньше другого, что хорошо заметно и в момент превращения. Назовите имя этого персонажа.</Question>")

    # read_page()
    # s = u20let.1
    # question 6 - 2 images from database, 8 - razdatka
    # s = "balt20-1_u.2"
    # s = "mosstud19_u.2"
    # s = "ZelShum2_u.1"
    # s = "mkm17.6"

    main()
    # read_page("ovsch20.3_u.1", "ovsch20.3_u.1")
    # cursor.execute("""SELECT * FROM links""")
    # print(cursor.fetchall())
    # https://db.chgk.net/tour/holgo2011_u.2/xml

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
# DONE: Removed opening images while auto-playing
# DONE: Added processing handouts while reading (can be used in game mode) (intvor_19.1_u.4/45, ovsch10.2-18, ...)
# DONE: Added config class with all changeable (during run) configs ans save to stack
# DONE: Added command logging
# DONE: Added launch with keys (for testing, debug, game mods)
# DONE: Added testing mode
# DONE: Added xml_loader with caching all loaded xmls (included parents)
# DONE: Added reading from cache/memory if there exists package
# DONE: Added testing
# DONE: Added test creator (existing questions from different packages by its names into one new package)
# DONE: Added replacing from transliteration in square brackets
# DONE: Added game mode (timer, no text, only reading aloud and pictures)
# DONE: Created BaseQuestion class and moved all questions functions into it
# TODO: add other handout types into BaseQuestion.write_text_with_width
# TODO: add duplets and blitz to reading and showing pictures (u20let.1/6)
