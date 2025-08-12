import os


DLC_DIR_NAMES = [
    'Core',
    'Royalty',
    'Ideology',
    'Biotech',
    'Anomaly',
    'Odyssey',
]


def get_all_file_paths(dlc_dir):
    result = []
    for dirpath, _, filenames in os.walk(dlc_dir):
        for name in filenames:
            result.append(os.path.join(dirpath, name))
    return result


def get_xml_file_paths(dlc_dir):
    return [path for path in get_all_file_paths(dlc_dir) if path.lower().endswith(".xml")]
