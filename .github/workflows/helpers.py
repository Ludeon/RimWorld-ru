import os


DLC_DIR_NAMES = [
    'Core',
    'Royalty',
    'Ideology',
    'Biotech',
    'Anomaly',
    'Odyssey',
]


def get_xml_file_paths(dlc_dir):
    result = []
    for dirpath, _, filenames in os.walk(dlc_dir):
        for name in filenames:
            if not name.lower().endswith(".xml"):
                continue
            result.append(os.path.join(dirpath, name))

    return result
