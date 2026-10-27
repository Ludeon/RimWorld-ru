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
    group: str
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
    EntityPattern("HediffDef", re.compile(r"\.comps\.\w+\.permanentLabel$")),
    EntityPattern("IssueDef", main_label_pattern),
    EntityPattern("MapGeneratorDef", main_label_pattern),
    EntityPattern("MemeDef", re.compile(r"\.(label|worshipRoomLabel|member)$")),
    EntityPattern("MutantDef", re.compile(r"\.(label|labelNoLocation)$")),
    EntityPattern("OrderedTakeGroupDef", main_label_pattern),
    EntityPattern("PawnCapacityDef", re.compile(r"\.(label|labelDrones|labelMechanoids|labelAnomalyEntity)$")),
    EntityPattern("PawnKindDef", re.compile(r"\.(label|labelMale|labelFemale|labelPlural|labelMalePlural|labelFemalePlural)$")),
    EntityPattern("PlanetLayerDef", main_label_pattern),
    EntityPattern("PreceptDef", re.compile(r"IdeoRole_.*?\.label$")),
    EntityPattern("RoomRoleDef", main_label_pattern),
    EntityPattern("RoyalTitleDef", re.compile(r"\.(label|labelFemale)$")),
    EntityPattern("ScenarioDef", re.compile(r"\.(xenotypeCounts|mutantCounts)\.\d+\.description$")), # Описание в xenotypeCounts/mutantCounts сценария подставляется в KINDLABEL ключа PawnCount.
    EntityPattern("SitePartDef", main_label_pattern),
    EntityPattern("SkillDef", main_label_pattern),
    EntityPattern("StyleCategoryDef", main_label_pattern),
    EntityPattern("ThingDef", main_label_pattern), # main label, excluding implied "Frame_"
    EntityPattern("ThingDef", re.compile(r"\.meatLabel$")),
    EntityPattern("ThingDef", re.compile(r"\.comps\.\w+\.chargeNoun$")),
    EntityPattern("ThingDef", re.compile(r"\.comps\.\w+\.label$")),  # For BiosculpterPod_*Cycle
    EntityPattern("ThingDef", re.compile(r"\.tools\.\w+\.label$")),  # For combat logs
    EntityPattern("ToolCapacityDef", main_label_pattern),
    EntityPattern("WorldObjectDef", main_label_pattern),
    EntityPattern("XenotypeDef", main_label_pattern),
    EntityPattern("Keyed", re.compile(r"^(SomeonesRoom|CouplesRoom)$")),    # For CleanRoom
    EntityPattern("Keyed", re.compile(r"^Animal$")),                        # For CommandBedSetOwnerDesc
    EntityPattern("Keyed", re.compile(r"^CaravanLeaderCaravanName$")),      # For GiveToCaravan
    EntityPattern("Keyed", re.compile(r"^AnElectricalConduit$")),           # For ShortCircuit/ShortCircuitStartedFire
    EntityPattern("Keyed", re.compile(r"^NamedXenogerm$")),                 # For InspectGenesDesc
    EntityPattern("Keyed", re.compile(r"^(GenepackPlural|XenotypeName)$")), # For CannotSaveXenogermTemplate
    EntityPattern("Keyed", re.compile(r"^(Slave|Colonist)$")),              # For RemainX and LetterChildLegalStatus
    EntityPattern("Keyed", re.compile(r"^AreaLower$")),                     # For CannotGenericWork, PrioritizeGeneric, UsingVerb, RulePackDef.Event_AbilityUsed, JobDef.reportString
    EntityPattern("Keyed", re.compile(r"^Burying$")),                       # For CannotGenericWork, PrioritizeGeneric
    EntityPattern("Keyed", re.compile(r"^Quadrum(Aprimay|Jugust|Septober|Decembary)$")),   # For DateReadout
    EntityPattern("Keyed", re.compile(r"^Season(Permanent)?(Spring|Summer|Fall|Winter)$")),         # For DateReadout
    EntityPattern("Keyed", re.compile(r"^Location$")),                      # For ReleasingEntity, DoWorkAtThing, RopedToThing, UsingVerb, JumpToTargetCustom, 
    EntityPattern("Keyed", re.compile(r"^(AnimalsLower|RelicLower|RelicsLower|ItemsLower|People)$")),   # For ChooseThingsDesc
    EntityPattern("Keyed", re.compile(r"^(Male|Female|All)$")),             # For PreceptDef ApparelDesired_*.description, GameConditionDef PsychicSuppression description/letterText
]

@dataclass
class EntitiesGroup:
    name: str
    entities: set[str]


class Severity(Enum):
    ERROR = 0
    WARNING = 1
    INFO = 2

@dataclass
class Issue:
    severity: Severity
    group: str
    entity: str
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
    keyed_path = dlc_keyed_path(dlc_name)

    print(f"DLC {dlc_name}")
    print(f"{case_path} vs {definjected_path} + {keyed_path}")
    cased_groups = parse_case_file(case_path)
    xml_groups = get_xml_entities(ENTITY_PATTERNS, definjected_path, keyed_path)

    issues = detect_all_issues(cased_groups, xml_groups)
    print_issues(issues);

    errors_count = sum(1 for issue in issues if issue.severity == Severity.ERROR)

    return errors_count > 0


def detect_all_issues(cased_groups: list[EntitiesGroup], xml_groups: list[EntitiesGroup]) -> list[Issue]:
    issues = list()

    for cased_group in cased_groups:
        for cased_entity in cased_group.entities:
            other_entries = list()
            own_entries = list()
            for xml_group in xml_groups:
                for xml_entity in xml_group.entities:
                    if entry_fits_key(cased_entity, xml_entity):
                        if xml_group.name == cased_group.name:
                            own_entries.append(f"'{xml_entity}' ({xml_group.name})")
                        else:
                            other_entries.append(f"'{xml_entity}' ({xml_group.name})")

            if len(own_entries) == 0:
                if len(other_entries) > 0:
                    issues.append(Issue(Severity.WARNING, group=cased_group.name, entity=cased_entity, message=f"Cased entity `{cased_entity}` ({cased_group.name}) fits XML entity(es) in another folder(s): {', '.join(other_entries)}"))
                else:
                    issues.append(Issue(Severity.ERROR, group=cased_group.name, entity=cased_entity, message=f"Cased entity `{cased_entity}` does not fit any XML entity"))

    for xml_group in xml_groups:
        for xml_entity in xml_group.entities:
            found_entries = list()
            for cased_group in cased_groups:
                fitting_cased_entry = find_fitting_entry(xml_key=xml_entity, cased_entries=cased_group.entities)
                if(fitting_cased_entry != None):
                    found_entries.append(f"'{fitting_cased_entry}' ({cased_group.name})")

            if len(found_entries) == 0:
                issues.append(Issue(Severity.ERROR, group=xml_group.name, entity=xml_entity, message=f"XML entity `{xml_entity}` ({xml_group.name}) has no matches in Case.txt"))
            elif len(found_entries) > 1:
                issues.append(Issue(Severity.INFO, group=xml_group.name, entity=xml_entity, message=f"XML entity `{xml_entity}` ({xml_group.name}) has {len(found_entries)} matches in Case.txt: {', '.join(found_entries)}"))

    return issues


def print_issues(issues: list[Issue]):
    issues = sorted(issues, key=lambda issue: issue.message)
    issues = sorted(issues, key=lambda issue: issue.entity)
    issues = sorted(issues, key=lambda issue: issue.severity.value)
    issues = sorted(issues, key=lambda issue: issue.group)
    grouped = groupby(issues, key=lambda issue: issue.group)

    for group_name, group_issues in grouped:
        print(f"    Group {group_name}:")
        for issue in group_issues:
            print(f"        {issue.severity.name}: {issue.message}")


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


def get_xml_entities(entityPatterns: list[EntityPattern], definjected_folder: str, keyed_folder: str) -> list[EntitiesGroup]:
    entity_groups = dict[str, EntitiesGroup]()

    for entityPattern in entityPatterns:
        folder = keyed_folder if entityPattern.group == "Keyed" else os.path.join(definjected_folder, entityPattern.group)

        group = entity_groups.setdefault(entityPattern.group, EntitiesGroup(name=entityPattern.group, entities=set()))
             
        for xml_file in get_xml_file_paths(folder):
            collect_entities_from_xml(entityPattern, xml_file, group.name, group.entities)

    return list(entity_groups.values())


def collect_entities_from_xml(entityPattern: EntityPattern, xml_file_path: str, group: str, entities: set[str]):
    tree = ET.parse(xml_file_path)
    for elem in tree.iter():
        if elem.text is not None and is_entity_tag(entityPattern, group, elem.tag):
            entities.add(elem.text)


def is_entity_tag(entityPattern: EntityPattern, group: str, def_injected_tag: str) -> bool:
    return entityPattern.group == group and entityPattern.tag_pattern.search(def_injected_tag)
 

def find_fitting_entry(cased_entries: set[str], xml_key: str) -> str:
    for key in _lookup_candidates(xml_key):
        if key in cased_entries:
            return key
        
    return None


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


def dlc_keyed_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'Keyed')


if __name__ == '__main__':
    main()
