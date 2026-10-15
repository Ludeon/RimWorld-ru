import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from helpers import print_red, print_yellow, get_xml_file_paths, DLC_DIR_NAMES


GROUP_HEADER_PREFIX = '// '

LABEL_TAG_SUFFIXES = (
    "abel",
    ".labelMale",
    ".labelFemale",
    ".labelPlural",
    ".labelShort",
)


@dataclass
class EntitiesGroup:
    name: str
    entities: set[str]


def main() -> None:
    has_error = False
    for dlc_name in DLC_DIR_NAMES[:1]:
        has_error |= check_case_file(dlc_name)

    if has_error:
        sys.exit(1)


def check_case_file(dlc_name: str) -> bool:
    case_path = dlc_case_path(dlc_name)
    definjected_path = dlc_definjected_path(dlc_name)

    print(f"DLC {dlc_name}")
    print(case_path + "  vs  " + definjected_path)
    case_file_groups = parse_case_file(case_path)
    xml_files_groups = parse_definjected_files(definjected_path)

    has_error = False
    for group in case_file_groups:
        has_error |= detect_entities_errors(group, xml_files_groups)
    return has_error


def parse_case_file(path: str) -> list[EntitiesGroup]:
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()

    result = []
    next_group_start_idx = 0
    while next_group_start_idx < (len(lines) - 1):
        group, next_group_start_idx = parse_group(lines, next_group_start_idx)
        if group:
            result.append(group)

    return result


def parse_group(lines: list[str], start_index: int) -> tuple[EntitiesGroup | None, int]:
    """Parses one group of Case.txt starting at `start_index`.

    Returns the parsed group (or None on error) and the index of the next group header.
    """
    group_lines = lines[start_index:]

    header = group_lines[0].strip()
    if not header.startswith(GROUP_HEADER_PREFIX):
        print_red(f"При чтении строки {start_index} "
                  "ожидалось, что будет указано имя файла в виде комментария `// ...`, "
                  "но оно не было указано! Пропускаем всю группу.")
        # skip all lines to the next group
        for offset, line in enumerate(group_lines):
            if line.startswith(GROUP_HEADER_PREFIX):
                return None, start_index + offset
        return None, len(lines)

    group_name = header.removeprefix(GROUP_HEADER_PREFIX)
    entities = set()
    offset = 0
    for offset, line in enumerate(group_lines[1:], start=1):
        line = line.strip()
        if not line:
            continue
        if line.startswith(GROUP_HEADER_PREFIX):
            break
        entities.add(line.split(';')[0])

    next_group_index = start_index + offset
    if not entities:
        print_red(f"При чтении группы строки {start_index} до строки {next_group_index} ожидалось, что будет собран список сущностей для {group_name}, но их не было!")
        return None, next_group_index

    return EntitiesGroup(group_name, entities), next_group_index


def parse_definjected_files(definjected_folder: str) -> list[EntitiesGroup]:
    return [
        EntitiesGroup(name=group_dir, entities=extract_xml_labels(definjected_folder, group_dir))
        for group_dir in os.listdir(definjected_folder)
    ]


def extract_xml_labels(definjected_folder: str, group_dir: str) -> set[str]:
    xml_files = get_xml_file_paths(os.path.join(definjected_folder, group_dir))

    labels = set()
    for path in xml_files:
        tree = ET.parse(path)
        for elem in tree.iter():
            if elem.text is not None and elem.tag.endswith(LABEL_TAG_SUFFIXES):
                labels.add(elem.text)
    return labels


def detect_entities_errors(group: EntitiesGroup, xml_groups: list[EntitiesGroup]) -> bool:
    has_error = False
    header_printed = False

    for entity in group.entities:
        in_own_group = any(
            xml_group.name == group.name and entity in xml_group.entities
            for xml_group in xml_groups
        )
        if in_own_group:
            continue

        has_error = True

        # print group name once
        if header_printed:
            prefix = "        "
        else:
            prefix = f"    - группа {group.name}:\n        "
            header_printed = True

        other_group = next(
            (xml_group for xml_group in xml_groups if entity in xml_group.entities),
            None,
        )
        if other_group:
            print_yellow(prefix +
                         f"`{entity}` описан в файле Case.txt в группе {group.name}, но находится в папке {other_group.name}")
        else:
            print_red(prefix +
                      f"`{entity}` есть в файле Case.txt, но её нет ни в одном XML файле")

        # for entity in xml_entities:
        #     if entity not in group.entities:
        #         print_yellow(f"Сущность {entity} есть в {group.name}, "
        #                      f"но её нет файле Case.txt")
    return has_error


def dlc_case_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'WordInfo', 'Case.txt')


def dlc_definjected_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'DefInjected')


if __name__ == '__main__':
    main()
