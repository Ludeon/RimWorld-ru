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

# BodyDef,BodyPartDef,BodyPartGroupDef,HediffDef,PawnCapacityDef,PawnKindDef,ThingDef,SitePartDef,ToolCapacityDef

# Core:
# ApparelLayerDef?
# BiomeDef?
# CultureDef? 
# DesignatorDropdownGroupDef?
# GatheringDef? GeneDef GoodwillSituationDef HairDef HediffDef HediffGiverSetDef HistoryAutoRecorderDef HistoryAutoRecorderGroupDef HistoryEventDef IncidentDef InfectionPathwayDef InspirationDef InstructionDef InteractionDef IssueDef JobDef JoyKindDef KeyBindingCategoryDef KeyBindingDef LifeStageDef MainButtonDef MechWeightClassDef MeditationFocusDef MentalBreakDef MentalStateDef NeedDef OptionCategoryDef OrderedTakeGroupDef PawnCapacityDef PawnColumnDef PawnKindDef PawnRelationDef PawnRenderTreeDef PawnsArrivalModeDef PlanetLayerDef PlanetLayerSettingsDef PreceptDef PrisonerInteractionModeDef QuestScriptDef RaidStrategyDef RecipeDef RecordDef ResearchProjectDef ResearchTabDef RitualOutcomeEffectDef RiverDef RoadDef RoofDef RoomRoleDef RoomStatDef RulePackDef ScenarioDef ScenPartDef SitePartDef SkillDef SpecialThingFilterDef StatCategoryDef StatDef StorytellerDef StuffCategoryDef StyleItemCategoryDef SurgeryOutcomeEffectDef TaleDef TattooDef TerrainAffordanceDef TerrainDef TerrainTemplateDef ThingCategoryDef ThingDef ThinkTreeDef ThoughtDef TileMutatorDef TimeAssignmentDef TipSetDef ToolCapacityDef TraderKindDef TrainabilityDef TrainableDef TraitDef TransferableSorterDef WeaponClassDef WeatherDef WorkGiverDef WorkTypeDef WorldObjectDef

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
    EntityPattern("RoomRoleDef", main_label_pattern),
    EntityPattern("RoyalTitleDef", re.compile(r"\.(label|labelFemale)$")),
    EntityPattern("ScenarioDef", re.compile(r"\.(xenotypeCounts|mutantCounts)\.\d+\.description$")), # Описание в xenotypeCounts/mutantCounts сценария подставляется в KINDLABEL ключа PawnCount.
    EntityPattern("SitePartDef", main_label_pattern),
    EntityPattern("SkillDef", main_label_pattern),
    EntityPattern("StyleCategoryDef", main_label_pattern),
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

    # for cased_group in cased_groups:
    #     for cased_entity in cased_group.entities:
    #         other_groups = set()

    #         for xml_group in xml_groups:
    #             if xml_group.name == cased_group.name:
    #                 if cased_entity in xml_group.entities:
    #                     continue # cased entity is in correct XML group - OK
    #             else:
    #                 if cased_entity in xml_group.entities:
    #                     other_groups.add(xml_group.name)

    #         if len(other_groups) > 0:
    #             issues.append(Issue(Severity.WARNING, group=cased_group.name, message=f"`{cased_entity}` есть в файле Case.txt в группе {cased_group.name}, но находится в папках {', '.join(other_groups)}"))
    #         else:
    #             issues.append(Issue(Severity.ERROR, group=cased_group.name, message=f"`{cased_entity}` есть в файле Case.txt, но её нет ни в одном XML файле"))

    for xml_group in xml_groups:
        for xml_entity in xml_group.entities:
            found_in_cased = 0
            for cased_group in cased_groups:
                if xml_entity in cased_group.entities:
                    found_in_cased += 1

            if found_in_cased == 0:
                issues.append(Issue(Severity.ERROR, group=xml_group.name, message=f"`{xml_entity}` есть в папке {xml_group.name}, но её нет в файле Case.txt"))
            elif found_in_cased > 1:
                issues.append(Issue(Severity.MESSAGE, group=xml_group.name, message=f"`{xml_entity}` упомянута в файле Case.txt {found_in_cased} раз"))

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


def parse_group(lines: list[str], start_index: int) -> tuple[EntitiesGroup | None, int]:
    """Parses one group of Case.txt starting at `start_index`.

    Returns the parsed group (or None on error) and the index of the next group header.
    """
    group_lines = lines[start_index:]

    first_line = group_lines[0].strip()

    group_name = first_line.removeprefix(GROUP_HEADER_PREFIX) if first_line.startswith(GROUP_HEADER_PREFIX) else UNDEFINED_GROUP_NAME
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
            if elem.text is not None and is_label_tag(group_dir, elem.tag):
                labels.add(elem.text)
    return labels


def is_label_tag(def_injected_group: str, def_injected_tag: str) -> bool:
    return any(
        pattern.def_injected_group == def_injected_group and 
        pattern.tag_pattern.search(def_injected_tag) 
        for pattern in ENTITY_PATTERNS)


def dlc_case_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'WordInfo', 'Case.txt')


def dlc_definjected_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'DefInjected')


if __name__ == '__main__':
    main()
