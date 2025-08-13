import os
import re
import sys
from dataclasses import dataclass

from helpers import DLC_DIR_NAMES, get_xml_file_paths, get_all_file_paths, print_red, print_green, print_yellow


# regexp to search for tag ends with reportString with dot in the end of the content
pattern = re.compile(r".*\.reportString>([^<]*)\.<\/")


@dataclass
class ErrorLine:
    file: str
    line_num: int
    content: str


def check_file(filepath) -> list[ErrorLine]:
    err_lines = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, start=1):
            # ignore comments
            if re.match(r"^\s*<!--", line):
                continue

            # remove comments at the end
            line = re.sub(r"<!--.*$", "", line)

            if pattern.search(line):
                err_lines.append(ErrorLine(filepath, i, line))
    return err_lines


def search_dot_report_string(files) -> list[ErrorLine]:
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

        print_green(err.line_num, end=': ')
        print(err.content.strip())


def main():
    print("Проверка XML файлов на отсутствие точки в конце reportString")

    has_errors = False

    for dlc_dir in DLC_DIR_NAMES:
        print(f"Проверка {dlc_dir}: ", end='')
        err_lines = search_dot_report_string(get_xml_file_paths(dlc_dir))
        print_report(err_lines)
        has_errors |= bool(err_lines)

    if has_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
