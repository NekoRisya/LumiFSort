from os import mkdir, walk
from shutil import move as mv
from os.path import exists, basename, join
from pathlib import Path

from argh import dispatch_command
from tqdm import tqdm
from time import sleep

from classifier import directory_indexing, index_file
from database import FileInfo

STATE = {
    "should_log": False,
    "debug": False
}
TEMPLATE = {
    "audio": "{path}/Audios",
    "video": "{path}/Videos",
    "image": "{path}/Images",
    "executable": "{path}/Programs",
    "code": "{path}/Programs/Codes",
    "document": "{path}/Documents",
    "font": "{path}/Documents/Fonts",
    "archive": "{path}/Archives",
    "presentation": "{path}/Documents/Presentations",
    "spreadsheet": "{path}/Documents/Spreadsheets",
    "project": "{path}/Projects"
}
TEMPLATE_DEFAULT = "{path}/AnyKind"


def move(src: FileInfo, root: Path, target: Path, dryrun: bool = False, should_log: bool = False):  # noqa: E501
    """Move files from here and there"""
    include_parent = Path(src.parent) != root
    parent = "" if not include_parent else src.parent_rel
    kind_dst = Path(TEMPLATE.get(src.kind, TEMPLATE_DEFAULT).format(path=target))  # noqa: E501
    rel_dst = Path(TEMPLATE.get(src.kind, TEMPLATE_DEFAULT).format(path="$TARGET"))  # noqa: E501
    dst = kind_dst / parent / basename(src.path)

    if dryrun:
        if should_log:
            print(f"Moving {basename(src.path)!r} to {rel_dst!s}")
        sleep(0.0001)
        return
    if not dst.parent.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
    mv(src.path, dst)


def main(path: str, target: str = "", dryrun: bool = False, log: bool = False):
    """Sort directory contents based on apparent paths."""
    if not target:
        target = path
    if Path(target).parent == Path(path):
        print("Deep scanning will conflict with current state. Target path must not be a child of the source path")  # noqa: E501
        return
    if not exists(target):
        print(f"Target [{basename(target)}] Doesn't exists... trying to mkdir...")  # noqa: E501
        mkdir(target)
    ignore_checks = [value.format(path=target) for value in TEMPLATE.values()]  # noqa: E501
    ignore_checks.append(TEMPLATE_DEFAULT.format(path=target))

    count = 0
    print(f"Indexing... ({count})", end='\r', flush=True)
    for root, directories, files in walk(path):
        if root != path:
            break
        for directory in directories:
            absdir = Path(join(root, directory))
            if str(absdir) in ignore_checks:
                print(absdir)
                continue
            directory_indexing(absdir)
            count += 1
            print(f"Indexing... ({count})", end="\r", flush=True)

        for file in files:
            index_file(root, file)
            count += 1
            print(f"Indexing... ({count})", end="\r", flush=True)

    entries = FileInfo.all()
    for entry in tqdm(entries, "Moving...", unit="files"):
        move(entry, Path(path), Path(target), dryrun, log)


if __name__ == "__main__":
    dispatch_command(main)
