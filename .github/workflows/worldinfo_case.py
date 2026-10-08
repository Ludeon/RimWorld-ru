import sys

from helpers import print_red, get_xml_file_paths, print_yellow, DLC_DIR_NAMES
import xml.etree.ElementTree as ET
from dataclasses import dataclass
import os
import re


# Шаблоны из Keyed, по которым игра сама генерирует названия предметов из названий существ
# (ThingDefGenerator_Meat, ThingDefGenerator_Corpses). {0} — родительный падеж названия.
GENERATED_LABEL_TEMPLATES = [
    "мясо {0}",
    "труп {0}",
]

# Поля дефов (последний сегмент пути инъекции), названия которых попадают в падежный словарь
LABEL_FIELDS = {
    "leaderTitle",
    "pawnSingular",
    "pawnsPlural",
    "chargeNoun",
}

# Пути инъекции полей, которые не называются label, но склоняются как названия.
# Описание в xenotypeCounts/mutantCounts сценария подставляется в KINDLABEL ключа PawnCount.
LABEL_TAG_PATTERNS = [
    re.compile(r"\.(xenotypeCounts|mutantCounts)\.\d+\.description$"),
]


@dataclass
class EntitiesGroup:
    name: str
    entities: set[str]


def group_folder(group_name: str) -> str:
    """Имя папки DefInjected (или `Keyed`) из заголовка группы.

    Заголовок может содержать уточнение: `// ThingDef.chargeNoun`, `// MemeDef label`,
    `// Keyed - Dialogs_Various`.
    """
    return re.split(r"[.\s]", group_name, maxsplit=1)[0]


def parse_group(lines, start_index) -> tuple[EntitiesGroup | None, int]:
    lines = lines[start_index:]

    group_name = ""
    entities = []
    if not lines[0].startswith('// '):
        print_red(f"При чтении строки {start_index + 1} "
                  "ожидалось, что будет указано имя файла в виде комментария `// ...`, "
                  "но оно не было указано! Пропускаем всю группу.")
        # skip all lines to the next group
        for i, line in enumerate(lines):
            if line.startswith('// '):
                return None, start_index + i
        return None, start_index + len(lines)

    for i, line in enumerate(lines):
        line = line.strip()
        if i == 0:
            group_name = line.replace('// ', '')
            continue
        if not line:
            continue

        if line.startswith('// '):
            break

        # Игра ищет слова в словаре без учёта регистра (LanguageWordInfo.RegisterLut)
        entities.append(line.split(';')[0].strip().lower())
    else:
        i = len(lines)

    if not entities:
        print_red(f"При чтении группы строки {start_index + 1} до строки {start_index + i} ожидалось, что будет собран список сущностей для {group_name}, но их не было!")
        return None, start_index + i

    return EntitiesGroup(group_name, set(entities)), start_index + i


def parse_case_file(path) -> list[EntitiesGroup]:
    result = []

    with open(path, encoding='utf-8-sig') as f:
        lines = f.readlines()

    next_group_start_idx = 0
    while next_group_start_idx < len(lines):
        group, next_group_start_idx = parse_group(lines, next_group_start_idx)
        if group:
            result.append(group)

    return result


def parse_word_pairs_file(path) -> dict[str, list[str]]:
    """Читает файл вида `слово; форма1; форма2; ...` (Case.txt, Plural.txt)."""
    result = {}
    if not os.path.isfile(path):
        return result
    with open(path, encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            parts = [part.strip().lower() for part in line.split(';')]
            result[parts[0]] = parts[1:]
    return result


def is_label_tag(tag: str) -> bool:
    field = tag.rsplit('.', 1)[-1]
    return (field.lower().endswith("label")
            or field.startswith("label")
            or field in LABEL_FIELDS
            or any(pattern.search(tag) for pattern in LABEL_TAG_PATTERNS))


def extract_xml_labels(definjected_folder, group_dir) -> set[str]:
    xml_files = get_xml_file_paths(os.path.join(definjected_folder, group_dir))

    labels = []
    for path in xml_files:
        root = ET.parse(path)
        for elem in root.iter():
            if elem.text and is_label_tag(elem.tag):
                labels.append(elem.text.strip().lower())
    return set(labels)


def extract_keyed_strings(dlc_name) -> set[str]:
    strings = []
    for path in get_xml_file_paths(os.path.join(dlc_name, 'Keyed')):
        root = ET.parse(path)
        for elem in root.iter():
            if elem.text:
                strings.append(elem.text.strip().lower())
    return set(strings)


def add_derived_forms(group: EntitiesGroup, plurals: dict[str, list[str]], cases: dict[str, list[str]]):
    """Добавляет формы, которые игра получает из названий: множественное число и сгенерированные названия."""
    derived = set()
    for label in group.entities:
        derived.update(plurals.get(label, []))
    if group.name == "ThingDef":
        for label in group.entities:
            forms = cases.get(label)
            if forms:
                genitive = forms[0]
                derived.update(template.format(genitive) for template in GENERATED_LABEL_TEMPLATES)
    group.entities |= derived


def detect_entites_errors(group: EntitiesGroup, xml_groups: list[EntitiesGroup],
                          other_dlc_groups: dict[str, list[EntitiesGroup]]) -> bool:
    has_error = False

    group_name_current = ""
    folder = group_folder(group.name)
    own_group = next((g for g in xml_groups if g.name == folder), None)

    for entity in sorted(group.entities):
        if own_group and entity in own_group.entities:
            continue

        has_error = True

        # print group name once
        if group_name_current == group.name:
            group_name = "        "
        else:
            group_name = f"    - группа {group.name}:\n        "
            group_name_current = group.name

        found_in = [g.name for g in xml_groups if entity in g.entities]
        found_in_dlc = [f"{dlc}/{g.name}"
                        for dlc, groups in other_dlc_groups.items()
                        for g in groups if entity in g.entities]
        if found_in:
            print_yellow(group_name +
                         f"`{entity}` описан в файле Case.txt в группе {group.name}, но находится в папке {', '.join(found_in)}")
        elif found_in_dlc:
            print_yellow(group_name +
                         f"`{entity}` описан в файле Case.txt, но находится в другой части игры: {', '.join(found_in_dlc)}")
        else:
            print_red(group_name +
                      f"`{entity}` есть в файле Case.txt, но её нет ни в одном XML файле")

    return has_error


def parse_definjected_files(dlc_name, plurals, cases) -> list[EntitiesGroup]:
    definjected_folder = dlc_definjected_path(dlc_name)
    result = []
    if os.path.isdir(definjected_folder):
        for group_dir in os.listdir(definjected_folder):
            labels = extract_xml_labels(definjected_folder, group_dir)
            result.append(EntitiesGroup(name=group_dir, entities=labels))
    result.append(EntitiesGroup(name="Keyed", entities=extract_keyed_strings(dlc_name)))
    for group in result:
        add_derived_forms(group, plurals, cases)
    return result


def check_case_file(dlc_name, all_xml_groups) -> bool:
    print(f"DLC {dlc_name}")
    print(dlc_case_path(dlc_name) + "  vs  " + dlc_definjected_path(dlc_name))
    case_file_groups = parse_case_file(dlc_case_path(dlc_name))
    xml_files_groups = all_xml_groups[dlc_name]
    other_dlc_groups = {dlc: groups for dlc, groups in all_xml_groups.items() if dlc != dlc_name}

    has_error = False
    for group in case_file_groups:
        has_error |= detect_entites_errors(group, xml_files_groups, other_dlc_groups)
    return has_error


def dlc_case_path(dlc_name):
    return os.path.join(dlc_name, 'WordInfo', 'Case.txt')


def dlc_plural_path(dlc_name):
    return os.path.join(dlc_name, 'WordInfo', 'Plural.txt')


def dlc_definjected_path(dlc_name):
    return os.path.join(dlc_name, 'DefInjected')


def main():
    # Словари всех частей игры загружаются вместе, поэтому формы ищем по всем сразу
    plurals = {}
    cases = {}
    for dlc_name in DLC_DIR_NAMES:
        plurals.update(parse_word_pairs_file(dlc_plural_path(dlc_name)))
        cases.update(parse_word_pairs_file(dlc_case_path(dlc_name)))

    all_xml_groups = {dlc_name: parse_definjected_files(dlc_name, plurals, cases)
                      for dlc_name in DLC_DIR_NAMES}

    has_error = False
    for dlc_name in DLC_DIR_NAMES:
        if os.path.isfile(dlc_case_path(dlc_name)):
            has_error |= check_case_file(dlc_name, all_xml_groups)

    if has_error:
        sys.exit(1)


if __name__ == '__main__':
    main()
