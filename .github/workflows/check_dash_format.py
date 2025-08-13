#!/usr/bin/env python3
import os
import re
import sys
from dataclasses import dataclass

from helpers import DLC_DIR_NAMES, get_xml_file_paths, print_red, print_green, print_yellow

# ANSI colors
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
GREEN = "\033[1;32m"
RESET = "\033[0m"

NBSP = "\u00A0"  # Неразрывный пробел
EM_DASH = "—"     # Длинное тире


@dataclass
class ErrorReason:
    file: str
    reason: str
    line_num: int
    content: str


def check_file(filepath):
    err_reasons = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, start=1):
            if re.match(r"^\s*<!--", line):
                continue
            line = re.sub(r"<!--.*$", "", line)

            if re.search(f"[^{NBSP}]- ", line):
                err_reasons.append(ErrorReason(filepath, "Неразрывный пробел и дефис (нужно длинное тире — (Alt+0151))", i, line))
            if re.search(r" - ", line):
                err_reasons.append(ErrorReason(filepath, "Пробел и дефис (нужны неразрывный пробел и длинное тире (Alt+0160 + Alt+0151))", i, line))
            if re.search(f" {EM_DASH} ", line):
                err_reasons.append(ErrorReason(filepath, "Обычный пробел перед тире (нужен неразрывный пробел (Alt+0160))", i, line))

    return err_reasons


def search_bad_dash_format_file_lines(files) -> list[ErrorReason]:
    err_reasons = []
    for f in files:
        err_reasons.extend(check_file(f))
    return err_reasons


def report_errors(dir_name, err_reasons: list[ErrorReason]):
    print(f"Проверка {dir_name}: ", end='')

    if not err_reasons:
        print_green("OK")
        return

    print_red("ERROR")

    err_reasons = sorted(err_reasons, key=lambda v: v.file)

    prev_file = ""
    for err in err_reasons:
        if err.file != prev_file:
            print_yellow(f"\nФайл: {err.file}")
            prev_file = err.file

        print_red(err.reason)
        print_green(err.line_num, end=': ')
        print(err.content.strip())


def main():
    print("Проверка XML файлов на форматирование неразрывного пробела и тире")

    has_errors = False

    for dlc_dir in DLC_DIR_NAMES:
        err_reasons = search_bad_dash_format_file_lines(get_xml_file_paths(dlc_dir))
        report_errors(dlc_dir, err_reasons)
        has_errors |= bool(err_reasons)

    if has_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
