#!/usr/bin/env python3
import os
import re
import sys
from dataclasses import dataclass

from helpers import DLC_DIR_NAMES, get_xml_file_paths, get_all_file_paths, print_red, print_green, print_yellow


pattern = re.compile(r"{PAWN_gender\s*\?\s*(.[^:]*)\s*:\s*\1}")

@dataclass
class ErrorLine:
    file: str
    line_num: int
    content: str
    match: re.Match


def check_file(filepath) -> list[ErrorLine]:
    err_lines = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, start=1):
            # ignore comments
            if re.match(r"^\s*<!--", line):
                continue

            # remove comments at the end
            line = re.sub(r"<!--.*$", "", line)

            if match := pattern.search(line):
                err_lines.append(ErrorLine(filepath, i, line, match))

    return err_lines


def search_bad_pawn_gender(files) -> list[ErrorLine]:
    err_lines = []
    for f in files:
        err_lines.extend(check_file(f))
    return err_lines


def print_report(err_lines: list[ErrorLine]):
    if not err_lines:
        print_green("OK")
        return

    print_red("ERROR")

    err_lines = sorted(err_lines, key=lambda v: v.file)

    prev_file = ""
    for err in err_lines:
        if err.file != prev_file:
            print_yellow(f"Файл: {err.file}")
            prev_file = err.file

        # print_red(err.match)
        print_green(err.line_num, end=': ')
        print(err.content[:err.match.start()].lstrip(), end='')
        print_red(err.match.group(), end='')
        print(err.content[err.match.end():], end='')


def main():
    print("Проверка макросов PAWN_gender на разное значение в подставляемых значениях")

    has_errors = False

    for dlc_dir in DLC_DIR_NAMES:
        print(f"Проверка {dlc_dir}: ", end='')
        err_lines = search_bad_pawn_gender(get_xml_file_paths(dlc_dir))
        print_report(err_lines)
        has_errors |= bool(err_lines)

    if has_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
