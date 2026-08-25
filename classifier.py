"""Classifying folder structures"""

from os import walk
from os.path import join, basename, getsize, realpath
from pathlib import Path
from typing import NamedTuple
from pprint import pprint

from extrec import recognize
from database import FileInfo

IGNORE_LIST = ["node_modules", ".git", "__pycache__"]
PROJECTS_CLASSIFIERS = ["src", "build"]
FILE_PROJECTS_CLASSIFIERS = [".gitignore", ".env", "Makefile", "README",
                             "LICENSE", "Dockerfile", "package.json",
                             "requirements.txt"]
FILE_VALUE_DISTRIBUTION = 0.4
DIRECTORY_VALUE_DISTRIBUTION = 0.6


def index_file(root: str, file: str):
    canonical = join(root, file)
    parent_rel = basename(root)
    size = getsize(canonical)
    kind = recognize(file)
    FileInfo.create(kind=kind, ftype="file", size=size, path=canonical, parent_rel=parent_rel, parent=realpath(join(canonical, "..")))  # noqa: E501


def directory_indexing(path: Path):
    classification_indexes: dict[str, float] = {
        "executable": 0,
        "code": 0,
        "font": 0,
        "image": 0,
        "document": 0,
        "spreadsheet": 0,
        "presentation": 0,
        "audio": 0,
        "video": 0,
        "archive": 0,
        "project": 0,
        "unknown": 0
    }

    structure_kinds = classification_indexes.copy()
    known_dirs = []
    known_files = []
    total_files = 0
    total_size = 0
    for root, directories, files in walk(path):
        if Path(root) != path:
            break
        known_dirs.extend([Path(join(root, directory)) for directory in directories])  # noqa: E501
        known_files.extend([Path(join(root, file)) for file in files])

    for file in known_files:
        if file.name in FILE_PROJECTS_CLASSIFIERS:
            classification_indexes['project'] += FILE_VALUE_DISTRIBUTION / len(known_files)  # noqa: E501
        else:
            kind = recognize(file)
            structure_kinds[kind] += 1
        total_files += 1
        total_size += getsize(file)

    for directory in known_dirs:
        if directory.name in PROJECTS_CLASSIFIERS:
            classification_indexes['project'] += DIRECTORY_VALUE_DISTRIBUTION / len(known_dirs)  # noqa: E501
        for r, _, fs in walk(join(path, directory)):
            for f in fs:
                total_size += getsize(join(r, f))

    for key, value in structure_kinds.items():
        if total_files == 0:
            continue
        classification_indexes[key] += FILE_VALUE_DISTRIBUTION * (value / total_files)  # noqa: E501

    kind = "unknown"
    highest = 0
    for key, value in classification_indexes.items():
        if value >= highest:
            kind = key
            highest = value
    if highest <= 0.5:
        kind = "unknown"

    # print(path.name, end=" : ")
    # pprint(classification_indexes, indent=2)
    # print("Selected as " + kind)
    FileInfo.create(
            kind=kind,
            ftype="directory",
            size=total_size,
            path=str(path.resolve()),
            parent_rel=path.parent.name,
            parent=str(path.resolve().parent)
    )
