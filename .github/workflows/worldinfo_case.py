import sys

from helpers import print_red, get_xml_file_paths, print_yellow, DLC_DIR_NAMES
import xml.etree.ElementTree as ET
from dataclasses import dataclass
import os


@dataclass
class EntitiesGroup:
    name: str
    entities: set[str]
    

def parse_group(lines, start_index) -> tuple[EntitiesGroup | None, int]:
    lines = lines[start_index:]
    
    group_name = ""
    entities = []
    if not lines[0].startswith('// '):
        print_red(f"При чтении строки {start_index} "
                  "ожидалось, что будет указано имя файла в виде комментария `// ...`, "
                  "но оно не было указано! Пропускаем всю группу.")
        # skip all lines to the next group
        for i, line in enumerate(lines):
            if line.startswith('// '):
                return None, start_index + i
   
    for i, line in enumerate(lines):
        line = line.strip()
        if i == 0:
            group_name = line.replace('// ', '')
            continue
        if not line:
            continue

        if line.startswith('// '):
            break
        
        entities.append(line.split(';')[0])

    if not entities:
        print_red(f"При чтении группы строки {start_index} до строки {start_index + i} ожидалось, что будет собран список сущностей для {group_name}, но их не было!")
        return None, start_index + i
    
    return EntitiesGroup(group_name, set(entities)), start_index + i


def parse_case_file(path) -> list[EntitiesGroup]:
    result = []
    
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()
    
    next_group_start_idx = 0
    while next_group_start_idx < (len(lines) - 1):
        group, next_group_start_idx = parse_group(lines, next_group_start_idx)
        if group:
            result.append(group)
    
    return result


def extract_xml_labels(definjected_folder, group_dir) -> set[str]:
    xml_files = get_xml_file_paths(os.path.join(definjected_folder, group_dir))

    labels = []
    for path in xml_files:
        root = ET.parse(path)
        for elem in root.iter():
            if (elem.tag.endswith("abel")  
                    or elem.tag.endswith(".labelMale") 
                    or elem.tag.endswith(".labelFemale")
                    or elem.tag.endswith(".labelPlural")
                    or elem.tag.endswith(".labelShort")
            ):
                labels.append(elem.text)
    return set(labels)


def detect_entites_errors(group: EntitiesGroup, xml_groups: list[EntitiesGroup]) -> bool:
    has_error = False

    group_name_current = ""
    
    for entity in group.entities:
        matched = False
        xml_group_for_entity = None
        for xml_group in xml_groups:
            if entity in xml_group.entities:
                xml_group_for_entity = xml_group
                if group.name == xml_group.name:
                    matched = True
                    continue
                break
        if matched:
            continue

        has_error = True
        
        # print group name once
        if group_name_current == group.name:
            group_name = "        "
        else:
            group_name = f"    - группа {group.name}:\n        "
            group_name_current = group.name
        
        if xml_group_for_entity:
            print_yellow(group_name + 
                         f"`{entity}` описан в файле Case.txt в группе {group.name}, но находится в папке {xml_group_for_entity.name}")
        else:
            print_red(group_name +
                         f"`{entity}` есть в файле Case.txt, но её нет ни в одном XML файле")

        # for entity in xml_entities:
        #     if entity not in group.entities:
        #         print_yellow(f"Сущность {entity} есть в {group.name}, "
        #                      f"но её нет файле Case.txt")
    return has_error


def parse_definjected_files(definjected_folder) -> list[EntitiesGroup]:
    result = []
    for group_dir in os.listdir(definjected_folder):
        labels = extract_xml_labels(definjected_folder, group_dir)
        result.append(EntitiesGroup(name=group_dir, entities=labels))
    return result
    
def check_case_file(dlc_name) -> bool:
    print(f"DLC {dlc_name}")
    print(dlc_case_path(dlc_name) + "  vs  " + dlc_definjected_path(dlc_name))
    case_file_groups = parse_case_file(dlc_case_path(dlc_name))
    xml_files_groups = parse_definjected_files(dlc_definjected_path(dlc_name))
    
    has_error = False
    for group in case_file_groups:
        has_error |= detect_entites_errors(group, xml_files_groups)
    return has_error

def dlc_case_path(dlc_name):
    return os.path.join(dlc_name, 'WordInfo', 'Case.txt')

def dlc_definjected_path(dlc_name):
    return os.path.join(dlc_name, 'DefInjected')

def main():
    has_error = False
    for dlc_name in DLC_DIR_NAMES[:1]:
        has_error |= check_case_file(dlc_name)
    
    if has_error:
        sys.exit(1)


if __name__ == '__main__':
    main()
