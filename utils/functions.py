import os, sys, math
from itertools import zip_longest, accumulate, combinations
from collections import defaultdict

from utils.contants import *


def resource_path(relative_path):
    """
    The function `resource_path` returns the absolute path to a resource, taking into account whether
    the code is running in development or as a PyInstaller executable.
    
    :param relative_path: The relative path of the resource file or folder that you want to get the
    absolute path for
    :return: the absolute path to a resource file.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def make_parser(fieldwidths):
    """
    The make_parser function takes a list of field widths and returns a parser function that can be used
    to parse fixed-width records.
    
    :param fieldwidths: The fieldwidths parameter is a list of integers that specifies the width of each
    field in a fixed-width file. Each integer in the list represents the number of characters in a field
    """
    
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
    """
    The `pwf_parser` function reads a file and parses it into a dictionary based on specific headers and
    field widths defined in `CODES_DICT`.
    
    :param pwf_path: The `pwf_path` parameter is the path to the PWF file that you want to parse. It
    should be a valid file path in the operating system
    :type pwf_path: os.PathLike
    :return: The function `pwf_parser` returns a dictionary containing parsed data from a file specified
    by `pwf_path`. The keys of the dictionary correspond to different headers in the file, and the
    values are lists of parsed data for each header.
    """
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


def power_set(entities, max_size=math.inf):
    """
    The function `power_set` generates all possible subsets of a given list of entities up to a
    specified maximum size.
    
    :param entities: The "entities" parameter is a list of elements for which we want to generate the
    power set
    :param max_size: The `max_size` parameter is an optional parameter that specifies the maximum size
    of the subsets in the power set. By default, it is set to `math.inf`, which means there is no
    maximum size limit. However, you can provide a specific value to limit the size of the subsets
    generated in
    """
    n = min(len(entities), max_size)
    for i in range(1, n + 1):
        yield from combinations(entities, r=i)


def line_length(X, B):
    """
    The function line_length calculates the approximate length of a line in kilometers using the formula
    7.8 * sqrt(X * B), where X and B are input parameters.
    
    :param X: The parameter X represents one of the reactanse of the line
    :param B: The parameter B represents the permeance of the line
    :return: the approximate length of a line in kilometers.
    """
    if math.isnan(X) or math.isnan(B):
        return 0
    return 7.8 * math.sqrt(X * B)
