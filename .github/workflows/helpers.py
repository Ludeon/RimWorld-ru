import os


DLC_DIR_NAMES = [
    'Core',
    'Royalty',
    'Ideology',
    'Biotech',
    'Anomaly',
    'Odyssey',
]


TERM_COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "reset": "\033[0m"
}


def get_all_file_paths(dlc_dir):
    result = []
    for dirpath, _, filenames in os.walk(dlc_dir):
        for name in filenames:
            result.append(os.path.join(dirpath, name))
    return result


def get_xml_file_paths(dlc_dir):
    return [path for path in get_all_file_paths(dlc_dir) if path.lower().endswith(".xml")]


def color_text(text, color):
    return f"{TERM_COLORS.get(color, TERM_COLORS['reset'])}{text}{TERM_COLORS['reset']}"

def print_red(text, **argv):
    print(color_text(text, "red"), **argv)

def print_green(text, **argv):
    print(color_text(text, "green"), **argv)

def print_yellow(text, **argv):
    print(color_text(text, "yellow"), **argv)
