from collections.abc import Iterator
import os
import sys
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from itertools import groupby
from enum import Enum
from re import Pattern
from helpers import print_red, print_yellow, get_xml_file_paths, DLC_DIR_NAMES


GROUP_HEADER_PREFIX = '// '

UNDEFINED_GROUP_NAME = "Undefined"

@dataclass
class EntityPattern:
    def_injected_group: str
    tag_pattern: Pattern[str]

main_label_pattern = re.compile(r"^\w+\.label$")

ENTITY_PATTERNS = [
    EntityPattern("AbilityDef", re.compile(r"\.(label|verbProperties\.label)$")),
    EntityPattern("BodyDef", re.compile(r"\.customLabel$")),
    EntityPattern("BodyPartDef", re.compile(r"\.(label|labelShort)$")),
    EntityPattern("BodyPartGroupDef", re.compile(r"\.(label|labelShort)$")),
    EntityPattern("ChemicalDef", main_label_pattern),
    EntityPattern("DamageDef", main_label_pattern),
    EntityPattern("FactionDef", re.compile(r"\.(pawnsPlural|pawnSingular|royalFavorLabel|leaderTitle|leaderTitleFemale)$")),
    EntityPattern("GameConditionDef", main_label_pattern),
    EntityPattern("GeneDef", main_label_pattern),
    EntityPattern("HediffDef", re.compile(r"^\w+\.(label|overrideLabel)$")),
    EntityPattern("IssueDef", main_label_pattern),
    EntityPattern("MapGeneratorDef", main_label_pattern),
    EntityPattern("MemeDef", re.compile(r"\.(label|worshipRoomLabel|member)$")),
    EntityPattern("MutantDef", re.compile(r"\.(label|labelNoLocation)$")),
    EntityPattern("PawnCapacityDef", re.compile(r"\.label")),
    EntityPattern("PawnKindDef", re.compile(r"\.(label|labelMale|labelFemale|labelPlural|labelMalePlural|labelFemalePlural)$")),
    EntityPattern("PlanetLayerDef", main_label_pattern),
    EntityPattern("PreceptDef", re.compile(r"IdeoRole_.*?\.label$")),
    EntityPattern("RecipeDef", re.compile(r"ingredients\.\d+\.filter\.customSummary$")), # MessageOutOfNearbyFuelFor, FUEL
    EntityPattern("ThingCategoryDef", main_label_pattern), # MessageOutOfNearbyFuelFor, FUEL
    EntityPattern("RoomRoleDef", main_label_pattern),
    EntityPattern("RoyalTitleDef", re.compile(r"\.(label|labelFemale)$")),
    EntityPattern("ScenarioDef", re.compile(r"\.(xenotypeCounts|mutantCounts)\.\d+\.description$")), # Описание в xenotypeCounts/mutantCounts сценария подставляется в KINDLABEL ключа PawnCount.
    EntityPattern("SitePartDef", main_label_pattern),
    EntityPattern("SkillDef", main_label_pattern),
    EntityPattern("StyleCategoryDef", main_label_pattern),
    EntityPattern("ThingDef", main_label_pattern), # main label, excluding implied "Frame_"
    EntityPattern("ThingDef", re.compile(r"^(?!Frame_)\w+\.label$")), # main label, excluding implied "Frame_"
    EntityPattern("ThingDef", re.compile(r"\.comps\.\w+\.chargeNoun$")),
    EntityPattern("ThingDef", re.compile(r"\.comps\.\w+\.label$")),  # For BiosculpterPod_*Cycle
    EntityPattern("ThingDef", re.compile(r"\.tools\.\w+\.label$")),  # For combat logs
    EntityPattern("ToolCapacityDef", main_label_pattern),
    EntityPattern("WorldObjectDef", main_label_pattern),
    EntityPattern("XenotypeDef", main_label_pattern),
]

@dataclass
class EntitiesGroup:
    name: str
    entities: set[str]

class Severity(Enum):
    ERROR = 0
    WARNING = 1
    MESSAGE = 2

@dataclass
class Issue:
    severity: Severity
    group: str
    message: str


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
    cased_groups = parse_case_file(case_path)
    xml_groups = parse_definjected_files(definjected_path)

    issues = detect_all_issues(cased_groups, xml_groups)
    print_issues(issues);

    return len(issues) > 0


def detect_all_issues(cased_groups: list[EntitiesGroup], xml_groups: list[EntitiesGroup]) -> list[Issue]:
    issues = list()

    for cased_group in cased_groups:
        for cased_entity in cased_group.entities:
            other_groups = set()
            own_groups = set()
            for xml_group in xml_groups:
                if any(entry_fits_key(cased_entity, xml_entity) for xml_entity in xml_group.entities):
                    if xml_group.name == cased_group.name:
                        own_groups.add(xml_group.name)
                    else:
                        other_groups.add(xml_group.name)

            if len(own_groups) == 0:
                if len(other_groups) > 0:
                    issues.append(Issue(Severity.WARNING, group=cased_group.name, message=f"Entity `{cased_entity}` exists in Case.txt in group `{cased_group.name}`, but defined in folder(s): {', '.join(other_groups)}"))
                else:
                    issues.append(Issue(Severity.ERROR, group=cased_group.name, message=f"Entity `{cased_entity}` exists in Case.txt, but not defined in any XML file"))

    for xml_group in xml_groups:
        for xml_entity in xml_group.entities:
            cased_groups_with_entity = set()
            for cased_group in cased_groups:
                if contains_key(xml_key=xml_entity, cased_entries=cased_group.entities):
                    cased_groups_with_entity.add(cased_group.name)

            if len(cased_groups_with_entity) == 0:
                issues.append(Issue(Severity.ERROR, group=xml_group.name, message=f"Entity `{xml_entity}` defined in folder {xml_group.name}, but does not exist in Case.txt"))
            elif len(cased_groups_with_entity) > 1:
                issues.append(Issue(Severity.MESSAGE, group=xml_group.name, message=f"Entity `{xml_entity}` is mentioned in Case.txt {len(cased_groups_with_entity)} times in groups: {', '.join(cased_groups_with_entity)}"))

    return issues


def print_issues(issues: list[Issue]):
    issues_sorted = sorted(issues, key=lambda issue: issue.group)
    grouped = groupby(issues_sorted, key=lambda issue: issue.group)

    for group_name, group_issues in grouped:
        print(f"    - группа {group_name}:")
        for issue in group_issues:
            prefix = "        "
            if issue.severity == Severity.ERROR:
                print_red(prefix + issue.message)
            elif issue.severity == Severity.WARNING:
                print_yellow(prefix + issue.message)
            else:
                print(prefix + issue.message)


def parse_case_file(path: str) -> list[EntitiesGroup]:
    result = []
    current_group_name = UNDEFINED_GROUP_NAME
    current_group_entities = set()

    with open(path, encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip()

            if(line.startswith(GROUP_HEADER_PREFIX)):
                result.append(EntitiesGroup(current_group_name, current_group_entities))
                current_group_entities = set()
                current_group_name = line.removeprefix(GROUP_HEADER_PREFIX)
            elif not line:
                continue
            else:
                current_group_entities.add(line.split(';')[0].strip())

    result.append(EntitiesGroup(current_group_name, current_group_entities))

    return result


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
            if elem.text is not None and is_label_tag(group_dir, elem.tag):
                labels.add(elem.text)
    return labels


def is_label_tag(def_injected_group: str, def_injected_tag: str) -> bool:
    return any(
        pattern.def_injected_group == def_injected_group and 
        pattern.tag_pattern.search(def_injected_tag) 
        for pattern in ENTITY_PATTERNS)


def contains_key(cased_entries: set[str], xml_key: str) -> bool:
    return any(key in cased_entries for key in _lookup_candidates(xml_key))


def entry_fits_key(cased_entry: str, xml_key: str) -> bool:
    return cased_entry in _lookup_candidates(xml_key)


def _lookup_candidates(xml_key: str) -> Iterator[str]:
    # Logic from LanguageWorker_Russian.TryLookup
    num = len(xml_key)
    while num > 0:
        yield xml_key[:num]
        num = xml_key.rfind(' ', 0, num)


def dlc_case_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'WordInfo', 'Case.txt')


def dlc_definjected_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'DefInjected')


if __name__ == '__main__':
    main()
