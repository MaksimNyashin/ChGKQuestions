#!/usr/bin/python3
from my_config import SYSTEM_WINDOWS, CURRENT_SYSTEM, TESTS_DIR, TEST_FILE, TEST_EXTENSION, CURRENT_DIR, CANON_RESULT_FILE, TMP_TESTS_FILE, TMP_DIFF_FILE, COLORS
from os import system as os_system, listdir, path as os_path
from sys import argv

def run_system_command(cmnd):
    null = {SYSTEM_WINDOWS: "nul"}.get(CURRENT_SYSTEM, "/dev/null")
    return os_system(f"{cmnd} > {null} 2> {null}")

NUM = 0
PRC = 50

def print_end():
    print(f"{'#' * PRC}{'DONE':>60}{100:>5}%")


def run_test(num, name):
    def print_status(ind):
        tup = ("Running test", "Checking results of test", "Finished test")
        mul = len(tup)
        com = tup[ind]
        ind += num * mul
        p = PRC * ind // (NUM * mul)
        prc = ind * 100 // (NUM * mul)
        print(f"{'#' * p}{'_' * (PRC - p)}      {com:<25}{name:>25}{TEST_EXTENSION}{prc:>5}%", end='\r')

    print_status(0)

    run_system_command(f'{os_path.join(CURRENT_DIR, "ChGKQuestions.py")} -t {name}')
    print_status(1)

    if not os_path.exists(CANON_RESULT_FILE % name):
        # print(f"Error: {name}{TEST_EXTENSION} canon file doesn\'t exist")
        with open(CANON_RESULT_FILE % name, "w") as fo:
            pass

    import difflib

    with open(TMP_TESTS_FILE, 'r', encoding="utf-8") as fi:
        result_data = fi.read().splitlines()

    with open(CANON_RESULT_FILE % name, 'r', encoding="utf-8") as fi:
        canon_data = fi.read().splitlines()

    cnt = 0
    with open(TMP_DIFF_FILE, "a", encoding="utf-8") as fo:
        for line in difflib.unified_diff(canon_data, result_data, fromfile=f"{name}.canon", tofile="test_result"):
            cnt += 1
            fo.write(line)
            fo.write("\n")
        fo.write("\n\n")

    print_status(2)
    if cnt == 0:
        return 1
    else:
        print(f"{COLORS.FAIL}Fail:{COLORS.END}{' ' * PRC} {'Result differs in test':<25}{name:>25}{TEST_EXTENSION}      ")
        return 0


def canonise_test(num, name):
    def print_status(ind):
        tup = ("Running test", "Canonising test", "Finished test")
        mul = len(tup)
        com = tup[ind]
        ind += num * mul
        p = PRC * ind // (NUM * mul)
        prc = ind * 100 // (NUM * mul)
        print(f"{'#' * p}{'_' * (PRC - p)}      {com:<25}{name:>25}{TEST_EXTENSION}{prc:>5}%", end='\r')

    print_status(0)
    
    run_system_command(f'{os_path.join(CURRENT_DIR, "ChGKQuestions.py")} -t {name}')
    print_status(1)

    from shutil import copyfile as sh_copyfile
    sh_copyfile(TMP_TESTS_FILE, CANON_RESULT_FILE % name)
    global good_cnt
    print_status(2)

    return 1


def main():
    global NUM
    list_dir = listdir(TESTS_DIR)
    NUM = len(list_dir)

    canonise = False
    if len(argv) > 1 and argv[1] == "-c":
        canonise = True
    
    with open(TMP_DIFF_FILE, "w") as fo:
        pass

    good_cnt, cnt = 0, 0
    for num, filename in enumerate(list_dir):
        if not filename.endswith(TEST_EXTENSION):
            continue
        name = filename[:-len(TEST_EXTENSION)]
        if canonise:
            good_cnt += canonise_test(num, name)
        else:
            good_cnt += run_test(num, name)
        cnt += 1
    print_end()

    if good_cnt == cnt:
        print(f"{COLORS.OKGREEN}Ok{COLORS.END}")
    else:
        print(f"{COLORS.FAIL}Fail: {good_cnt}/{cnt}{COLORS.END}")

if __name__ == '__main__':
    main()