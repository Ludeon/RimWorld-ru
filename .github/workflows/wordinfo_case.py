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

CASE_ENTITY_PATTERNS = [
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
    EntityPattern("ThingDef", main_label_pattern),
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

PLURAL_ENTITY_PATTERNS = [
    EntityPattern("MemeDef", re.compile(r"\.member$")),
    EntityPattern("OrderedTakeGroupDef", main_label_pattern),
    EntityPattern("RoyalTitleDef", re.compile(r"\.(label|labelFemale)$")),
    EntityPattern("ScenarioDef", re.compile(r"\.(xenotypeCounts|mutantCounts)\.\d+\.description$")),
    EntityPattern("ThingDef", re.compile(r"^(?!Filth_)\w+\.label$")), # main label, excluding implied "Filth_"
    EntityPattern("XenotypeDef", main_label_pattern),
    EntityPattern("Keyed", re.compile(r"^Animal$")),
    EntityPattern("Keyed", re.compile(r"^(Male|Female)$")),
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


@dataclass
class WordInfoCollection:
    dlc_name: str
    actual_groups: list[EntitiesGroup]
    required_groups: list[EntitiesGroup]


@dataclass
class DlcWordInfo:
    name: str
    plural: WordInfoCollection
    case: WordInfoCollection


def main() -> None:
    dlcs = [load_dlc_wordinfo(dlc_name) for dlc_name in DLC_DIR_NAMES]

    has_error = False
    for dlc in dlcs:
        has_error |= check_wordinfo_files(dlc, dlcs)

    if has_error:
        sys.exit(1)


def load_dlc_wordinfo(dlc_name: str) -> DlcWordInfo:
    case_path = dlc_case_path(dlc_name)
    plural_path = dlc_plural_path(dlc_name)
    definjected_path = dlc_definjected_path(dlc_name)
    keyed_path = dlc_keyed_path(dlc_name)

    plural_actual_groups = get_wordinfo_entities(plural_path, index = 0)
    plural_required_groups = get_xml_entities(PLURAL_ENTITY_PATTERNS, definjected_path, keyed_path)

    case_actual_groups = get_wordinfo_entities(case_path, index = 0)
    case_required_xml_groups = get_xml_entities(CASE_ENTITY_PATTERNS, definjected_path, keyed_path)
    case_required_plural_groups = get_wordinfo_entities(plural_path, index = 1)
    case_required_groups = merge(case_required_xml_groups, case_required_plural_groups)

    return DlcWordInfo(
        name=dlc_name,
        plural=WordInfoCollection(dlc_name, plural_actual_groups, plural_required_groups),
        case=WordInfoCollection(dlc_name, case_actual_groups, case_required_groups),
    )


def check_wordinfo_files(dlc: DlcWordInfo, all_dlcs: list[DlcWordInfo]) -> bool:
    other_dlcs = [other for other in all_dlcs if other.name != dlc.name]

    print(f"DLC {dlc.name}")
    print(f"{dlc_plural_path(dlc.name)} vs {dlc_definjected_path(dlc.name)} + {dlc_keyed_path(dlc.name)}")

    plural_issues = detect_all_issues("Plural", dlc.plural, [other.plural for other in other_dlcs])
    print_issues(plural_issues)

    case_issues = detect_all_issues("Case", dlc.case, [other.case for other in other_dlcs])
    print_issues(case_issues)

    errors_count = 0
    errors_count += sum(1 for issue in plural_issues if issue.severity == Severity.ERROR)
    errors_count += sum(1 for issue in case_issues if issue.severity == Severity.ERROR)

    return errors_count > 0


def detect_all_issues(wordinfo_collection_name: str, collection: WordInfoCollection, other_dlc_collections: list[WordInfoCollection]) -> list[Issue]:
    issues = list()
    actual_groups = collection.actual_groups
    required_groups = collection.required_groups

    for actual_group in actual_groups:
        for actual_entity in actual_group.entities:
            other_group_matches = list()
            own_group_matches = list()
            for required_group in required_groups:
                for required_entity in required_group.entities:
                    if is_match(actual_entity, required_entity):
                        if required_group.name == actual_group.name:
                            own_group_matches.append(f"'{required_entity}' ({required_group.name})")
                        else:
                            other_group_matches.append(f"'{required_entity}' ({required_group.name})")

            if len(own_group_matches) == 0:
                if len(other_group_matches) > 0:
                    issues.append(Issue(Severity.WARNING, group=actual_group.name, entity=actual_entity, message=f"Actual {wordinfo_collection_name} entity `{actual_entity}` ({actual_group.name}) matches required entity(es) in another group(s): {', '.join(other_group_matches)}"))
                    continue

                other_dlc_matches = find_required_matches_in_other_dlcs(actual_entity, other_dlc_collections)
                if len(other_dlc_matches) > 0:
                    issues.append(Issue(Severity.WARNING, group=actual_group.name, entity=actual_entity, message=f"Actual {wordinfo_collection_name} entity `{actual_entity}` ({actual_group.name}) is in wrong DLC, it matches required entity(es) in other DLC(s): {', '.join(other_dlc_matches)}"))
                else:
                    issues.append(Issue(Severity.ERROR, group=actual_group.name, entity=actual_entity, message=f"Actual {wordinfo_collection_name} entity `{actual_entity}` does not match any required entity"))

    for required_group in required_groups:
        for required_entity in required_group.entities:
            found_matches = list()
            for actual_group in actual_groups:
                matching_actual_entity = find_actual_match(required_entity=required_entity, actual_entities=actual_group.entities)
                if(matching_actual_entity != None):
                    found_matches.append(f"'{matching_actual_entity}' ({actual_group.name})")

            if len(found_matches) == 0:
                other_dlc_matches = find_actual_matches_in_other_dlcs(required_entity, other_dlc_collections)
                if len(other_dlc_matches) == 0:
                    issues.append(Issue(Severity.ERROR, group=required_group.name, entity=required_entity, message=f"Required entity `{required_entity}` ({required_group.name}) has no actual matches in {wordinfo_collection_name}"))
                elif all(is_required_in_own_dlc for _, is_required_in_own_dlc in other_dlc_matches):
                    # Otherwise the "wrong DLC" warning is already reported for the actual entity in the other DLC
                    issues.append(Issue(Severity.WARNING, group=required_group.name, entity=required_entity, message=f"Required entity `{required_entity}` ({required_group.name}) has actual matches in {wordinfo_collection_name} of other DLC(s) only: {', '.join(match for match, _ in other_dlc_matches)}"))
            elif len(found_matches) > 1:
                issues.append(Issue(Severity.INFO, group=required_group.name, entity=required_entity, message=f"Required entity `{required_entity}` ({required_group.name}) has {len(found_matches)} actual matches in {wordinfo_collection_name}: {', '.join(found_matches)}"))

    return issues


def find_required_matches_in_other_dlcs(actual_entity: str, other_dlc_collections: list[WordInfoCollection]) -> list[str]:
    matches = list()
    for other in other_dlc_collections:
        for required_group in other.required_groups:
            for required_entity in required_group.entities:
                if is_match(actual_entity, required_entity):
                    matches.append(f"'{required_entity}' ({required_group.name}, {other.dlc_name})")

    return matches


def find_actual_matches_in_other_dlcs(required_entity: str, other_dlc_collections: list[WordInfoCollection]) -> list[tuple[str, bool]]:
    """Returns matches with flags whether the matching actual entity is also required in its own DLC"""
    matches = list()
    for other in other_dlc_collections:
        for actual_group in other.actual_groups:
            matching_actual_entity = find_actual_match(required_entity=required_entity, actual_entities=actual_group.entities)
            if matching_actual_entity != None:
                is_required_in_own_dlc = any(is_match(matching_actual_entity, entity) for group in other.required_groups for entity in group.entities)
                matches.append((f"'{matching_actual_entity}' ({actual_group.name}, {other.dlc_name})", is_required_in_own_dlc))

    return matches


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


def get_wordinfo_entities(wordinfo_file_path: str, index: int) -> list[EntitiesGroup]:
    result = []
    current_group_name = UNDEFINED_GROUP_NAME
    current_group_entities = set()

    if not os.path.isfile(wordinfo_file_path):
        return result

    with open(wordinfo_file_path, encoding='utf-8') as f:
        for line in f.readlines():
            line = line.strip()

            if(line.startswith(GROUP_HEADER_PREFIX)):
                result.append(EntitiesGroup(current_group_name, current_group_entities))
                current_group_entities = set()
                current_group_name = line.removeprefix(GROUP_HEADER_PREFIX)
            elif not line:
                continue
            else:
                current_group_entities.add(line.split(';')[index].strip())

    result.append(EntitiesGroup(current_group_name, current_group_entities))

    return result


def merge(groups_left: list[EntitiesGroup], groups_right: list[EntitiesGroup]) -> list[EntitiesGroup]:
    merged = dict[str, EntitiesGroup]()

    for group in groups_left + groups_right:
        merged_group = merged.setdefault(group.name, EntitiesGroup(name=group.name, entities=set()))
        merged_group.entities |= group.entities

    return list(merged.values())


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
 

def find_actual_match(actual_entities: set[str], required_entity: str) -> str:
    for candidate in get_lookup_candidates(required_entity):
        if candidate in actual_entities:
            return candidate
        
    return None


def is_match(actual_entity: str, required_entity: str) -> bool:
    return actual_entity in get_lookup_candidates(required_entity)


def get_lookup_candidates(required_entity: str) -> Iterator[str]:
    # Logic from LanguageWorker_Russian.TryLookup
    num = len(required_entity)
    while num > 0:
        yield required_entity[:num]
        num = required_entity.rfind(' ', 0, num)


def dlc_case_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'WordInfo', 'Case.txt')


def dlc_plural_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'WordInfo', 'Plural.txt')


def dlc_definjected_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'DefInjected')


def dlc_keyed_path(dlc_name: str) -> str:
    return os.path.join(dlc_name, 'Keyed')


if __name__ == '__main__':
    main()
