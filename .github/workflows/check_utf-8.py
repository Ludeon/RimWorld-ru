import sys
import os

from helpers import DLC_DIR_NAMES, get_xml_file_paths, get_all_file_paths, print_red, print_green, print_yellow


UTF8_BOM = b"\xef\xbb\xbf"

def search_bad_encoding(files) -> tuple[list, list]:
    not_utf8_files = []
    not_bom_files = []

    for path in files:
        with open(path, 'rb') as f:
            data = f.read()
        # check if file encoded in UTF-8
        try:
            data.decode('utf-8')
        except UnicodeDecodeError:
            not_utf8_files.append(path)
            continue

        # check for BOM
        if not data.startswith(UTF8_BOM):
            not_bom_files.append(path)

    return sorted(not_utf8_files), sorted(not_bom_files)


def print_report(dir_name, not_utf8_files, not_bom_files):
    print(f"Проверка {dir_name}: ", end='')

    if not not_utf8_files and not not_bom_files:
        print_green("OK")
        return

    print_red("ERROR")

    if not_utf8_files:
        print_yellow("Файлы не в кодировке UTF-8:")
        for f in not_utf8_files:
            print("  ", f)

    if not_bom_files:
        print_yellow("Файлы UTF-8 без BOM:")
        for f in not_bom_files:
            print("  ", f)


def main():
    print("Проверка файлов перевода на валидную кодировку UTF-8 c BOM")

    has_errors = False

    for dlc_dir in DLC_DIR_NAMES:
        not_utf8_files, not_bom_files = search_bad_encoding(get_xml_file_paths(dlc_dir))
        print_report(dlc_dir, not_utf8_files, not_bom_files)
        has_errors |= bool(not_utf8_files or not_bom_files)

    # separate check of not XML files
    not_utf8_files, not_bom_files = search_bad_encoding(get_all_file_paths("RimWorldUniverse"))
    print_report("RimWorldUniverse", not_utf8_files, not_bom_files)
    has_errors |= bool(not_utf8_files or not_bom_files)

    if has_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
