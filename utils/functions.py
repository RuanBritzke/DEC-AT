import os, sys
from itertools import zip_longest
from itertools import accumulate
from collections import defaultdict

from utils.contants import *


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def make_parser(fieldwidths):
    cuts = tuple(cut for cut in accumulate(abs(fw) for fw in fieldwidths))
    pads = tuple(fw < 0 for fw in fieldwidths)  # bool flags for padding fields
    flds = tuple(zip_longest(pads, (0,) + cuts, cuts))[:-1]  # ignore final one
    slcs = ", ".join("line[{}:{}]".format(i, j) for pad, i, j in flds if not pad)
    parse = eval("lambda line: ({})\n".format(slcs))  # Create and compile source code.

    # Optional informational function attributes.
    parse.size = sum(abs(fw) for fw in fieldwidths)
    parse.fmtstring = " ".join(
        "{}{}".format(abs(fw), "x" if fw < 0 else "s") for fw in fieldwidths
    )
    return parse


def pwf_parser(pwf_path: os.PathLike) -> dict:
    with open(pwf_path, "r") as file:
        data = defaultdict(list)
        current_header = None

        for i, line in enumerate(file):
            line = line.rstrip()
            if line.startswith("("):
                continue

            # Check if the line corresponds to a header
            if line in CODES_DICT.keys():
                current_header = line
                continue

            # Check if the line contains "99999" (end of header domain) or starts with '(' (comment)
            if line == "99999":
                current_header = None
                continue

            # Only parse lines when a valid header is set
            if current_header:
                fieldwidths = CODES_DICT.get(current_header, ())
                if fieldwidths:
                    parser = make_parser(fieldwidths)
                    parsed_data = parser(line)
                    parsed_data_stripped = tuple(item.strip() for item in parsed_data)
                    data[current_header].append(parsed_data_stripped)
    return data
