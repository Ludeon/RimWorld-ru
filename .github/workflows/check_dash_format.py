import os
import re
import sys
from dataclasses import dataclass

from helpers import DLC_DIR_NAMES, get_xml_file_paths, print_red, print_green, print_yellow


NBSP = "\u00A0"
EM_DASH = "—"


@dataclass
class ErrorLine:
    file: str
    line_num: int
    content: str
    reason: str
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

            if match := re.search(f"{NBSP}- ", line):
                err_lines.append(ErrorLine(filepath, i, line, "Неразрывный пробел и дефис (нужно длинное тире — (Alt+0151))", match))
            if match := re.search(r" - ", line):
                err_lines.append(ErrorLine(filepath, i, line, "Пробел и дефис (нужны неразрывный пробел и длинное тире (Alt+0160 + Alt+0151))", match))
            if match := re.search(f" {EM_DASH} ", line):
                err_lines.append(ErrorLine(filepath, i, line, "Обычный пробел перед тире (нужен неразрывный пробел (Alt+0160))", match))

    return err_lines


def search_bad_dash_format_file_lines(files) -> list[ErrorLine]:
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

        print_red(err.reason)
        print_green(err.line_num, end=': ')
        print(err.content[:err.match.start()].lstrip(), end='')
        print_red(err.match.group(), end='')
        print(err.content[err.match.end():], end='')


def main():
    print("Проверка XML файлов на форматирование неразрывного пробела и тире")

    has_errors = False

    for dlc_dir in DLC_DIR_NAMES:
        print(f"Проверка {dlc_dir}: ", end='')
        err_lines = search_bad_dash_format_file_lines(get_xml_file_paths(dlc_dir))
        print_report(err_lines)
        has_errors |= bool(err_lines)

    if has_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
