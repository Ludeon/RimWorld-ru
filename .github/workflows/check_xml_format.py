import sys
import os
import xml.etree.ElementTree as ET

from helpers import DLC_DIR_NAMES, get_xml_file_paths


def search_bad_xml(dlc_dir):
    broken_files = []

    for path in get_xml_file_paths(dlc_dir):
        try:
            ET.parse(path)
        except Exception:
            broken_files.append(path)


def report_errors(dir_name, bad_xml_files):
    print(f"Проверка {dir_name}: ", end='')

    if bad_xml_files:
        print("\nФайлы XML с ошибкой в формате:")
        for f in bad_xml_files:
            print("  ", f)


    if not bad_xml_files:
        print("OK")

def main():
    has_errors = False

    for dlc_dir in DLC_DIR_NAMES:
        bad_xml_files = search_bad_xml(dlc_dir)
        report_errors(dlc_dir, bad_xml_files)
        has_errors |= bool(bad_xml_files)
    
    if has_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
