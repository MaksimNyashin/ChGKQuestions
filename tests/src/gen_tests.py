#!/usr/bin/python3
import sys
from os import path as os_path

sys.path.append(os_path.dirname(os_path.dirname(os_path.dirname(os_path.abspath(__file__)))))

from ChGKQuestions import read_global
from my_config import (
    init_outer_main,
    TESTS_SRC_DIR,
    TEST_SOURCE_BASE_FILE,
    TEST_SOURCE_FILE,
    TEST_SOURCE_BASE_EXTENSION,
    DB_CHGK,
)
from os import listdir
from threading import Thread
import xml.etree.ElementTree as Et

XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<tournament>
<Title>Тест_%s</Title>
<TextId>%s</TextId>
<ParentTextId>Test</ParentTextId>



%s



</tournament>
"""


def read_from_global(link, result, ind):
    root = Et.fromstring(read_global(link[0]))
    for quest in root.iter('question'):
        if quest.find('Number').text == link[1]:
            quest.find('Number').text = str(ind)
            result.append(quest)
            break


def read_from_test_base(filename):
    with open(TEST_SOURCE_BASE_FILE % filename, "r") as fi:
        links = [quest.split("/") for quest in fi.read().splitlines()]

    result = []
    threads = []
    for ind, link in enumerate(links):
        result.append([])
        threads.append(Thread(target=read_from_global, args=(link, result[-1], ind + 1)))
        threads[-1].start()

    for i in threads:
        i.join()

    with open(TEST_SOURCE_FILE % filename, "w", encoding="utf-8") as fo:
        fo.write(
            XML_TEMPLATE
            % (
                filename,
                filename,
                "\n\n".join(
                    Et.tostring(val[0], encoding="unicode").replace(" />", "/>") for ind, val in enumerate(result)
                ),
            )
        )


def main():
    init_outer_main()
    threads = []
    for filename in listdir(TESTS_SRC_DIR):
        if filename.endswith(TEST_SOURCE_BASE_EXTENSION):
            threads.append(Thread(target=read_from_test_base, args=(filename[: -len(TEST_SOURCE_BASE_EXTENSION)],)))
            threads[-1].start()

    for ind, val in enumerate(threads):
        val.join()


if __name__ == '__main__':
    main()
