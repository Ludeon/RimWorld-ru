#!/usr/bin/env python3
import sys
import os

from helpers import DLC_DIR_NAMES


UTF8_BOM = b"\xef\xbb\xbf"

def search_bad_encoding(root_dir) -> tuple[list, list]:
    not_utf8_files = []
    not_bom_files = []

    for dirpath, _, filenames in os.walk(root_dir):
        for name in filenames:
            if name.lower().endswith(".xml"):
                path = os.path.join(dirpath, name)
                with open(path, 'rb') as f:
                    data = f.read()

                # check for BOM
                if not data.startswith(UTF8_BOM):
                    not_bom_files.append(path)

                try:
                    # check if remaining is UTF-8
                    data[len(UTF8_BOM):].decode('utf-8')
                except UnicodeDecodeError:
                    not_utf8_files.append(path)

    not_bom_files = sorted(list(set(not_bom_files) - set(not_utf8_files)))
    not_utf8_files = sorted(not_utf8_files)

    return not_bom_files, not_utf8_files


if __name__ == "__main__":
    has_error = False
    for dlc_dir in DLC_DIR_NAMES + ["RimWorldUniverse"]:
        print(f"Проверка {dlc_dir}: ", end='')

        not_utf8_files, not_bom_files = search_bad_encoding(dlc_dir)

        if not not_utf8_files and not not_utf8_files:
            print("OK")
            continue

        if not_utf8_files:
            print("\nФайлы не в кодировке UTF-8:")
            for f in not_utf8_files:
                print("  ", f)

        if not_bom_files:
            print("\nФайлы UTF-8 без BOM:")
            for f in not_bom_files:
                print(" ", f)

    if not_utf8_files or not_bom_files:
        sys.exit(1)
    sys.exit(0)