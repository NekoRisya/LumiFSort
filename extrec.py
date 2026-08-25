"""
ext_recognizer.py

A small utility for classifying files by extension into logical
"target" categories (e.g. images, documents, code, archives) and
suggesting a destination path for organizing them.

Usage:
    from ext_recognizer import recognize, sort_destination

    recognize("photo.JPG")            -> "image"
    recognize("notes.md")             -> "document"
    recognize("archive.tar.gz")       -> "archive"
    recognize("weird.xyz123")         -> "unknown"

    sort_destination("photo.jpg", base="/sorted")
        -> "/sorted/image/photo.jpg"
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


# ---------------------------------------------------------------------------
# Category definitions
# ---------------------------------------------------------------------------
# Extensions are stored without the leading dot, lowercase.
# Multi-part extensions (e.g. "tar.gz") are matched specially in `recognize`.

CATEGORY_MAP: dict[str, set] = {
    "image": {
        "jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "tiff", "tif",
        "ico", "heic", "raw",
    },
    "document": {
        "txt", "md", "rst", "doc", "docx", "odt", "pdf", "rtf", "tex",
        "log",
    },
    "spreadsheet": {
        "xls", "xlsx", "csv", "tsv", "ods",
    },
    "presentation": {
        "ppt", "pptx", "odp", "key",
    },
    "audio": {
        "mp3", "wav", "flac", "aac", "ogg", "wma", "m4a",
    },
    "video": {
        "mp4", "mkv", "avi", "mov", "wmv", "flv", "webm", "m4v",
    },
    "archive": {
        "zip", "rar", "7z", "tar", "gz", "bz2", "xz", "tar.gz", "tar.bz2",
    },
    "code": {
        "py", "js", "ts", "jsx", "tsx", "java", "c", "cpp", "h", "hpp",
        "cs", "go", "rs", "rb", "php", "swift", "kt", "sh", "bat", "ps1",
        "sql", "html", "css", "json", "yaml", "yml", "xml", "toml",
    },
    "font": {
        "ttf", "otf", "woff", "woff2",
    },
    "executable": {
        "exe", "msi", "apk", "app", "deb", "rpm", "jar",
    },
}

# Reverse lookup: extension -> category, built once at import time.
_EXT_TO_CATEGORY: dict[str, str] = {
    ext: category
    for category, exts in CATEGORY_MAP.items()
    for ext in exts
}

# Multi-part extensions need to be checked before the single-part fallback.
_MULTI_PART_EXTS = sorted(
    (ext for ext in _EXT_TO_CATEGORY if "." in ext),
    key=len,
    reverse=True,  # check longest/most-specific first (e.g. tar.gz before gz)
)


def _extract_extension(filename: str) -> str:
    """
    Return the lowercase extension of `filename`, handling multi-part
    extensions like '.tar.gz'. Returns "" if there is no extension.
    """
    name = os.path.basename(filename).lower()

    for multi_ext in _MULTI_PART_EXTS:
        if name.endswith("." + multi_ext):
            return multi_ext

    suffix = Path(name).suffix  # includes leading dot, or ""
    return suffix[1:] if suffix else ""


def recognize(filename: str, default: str = "unknown") -> str:
    """
    Classify `filename` into a category based on its extension.

    Args:
        filename: file name or path (only the extension matters).
        default: category returned when the extension isn't recognized.

    Returns:
        Category name, e.g. "image", "document", "code", or `default`.
    """
    ext = _extract_extension(filename)
    return _EXT_TO_CATEGORY.get(ext, default)


def sort_destination(filename: str, base: str = "sorted", default: str = "misc") -> str:  # noqa: E501
    """
    Build a suggested destination path for `filename`, grouping it under
    a subfolder named after its category.

    Example:
        sort_destination("song.mp3", base="/home/user/sorted")
        -> "/home/user/sorted/audio/song.mp3"
    """
    category = recognize(filename, default=default)
    return str(Path(base) / category / os.path.basename(filename))


@dataclass
class BatchResult:
    """Result of classifying a batch of files."""
    by_category: dict[str, list] = field(default_factory=dict)

    def add(self, category: str, filename: str) -> None:
        self.by_category.setdefault(category, []).append(filename)

    def summary(self) -> str:
        lines = []
        for category, files in sorted(self.by_category.items()):
            lines.append(f"{category} ({len(files)}):")
            for f in files:
                lines.append(f"  - {f}")
        return "\n".join(lines)


def recognize_batch(filenames: Iterable[str], default: str = "unknown") -> BatchResult:  # noqa: E501
    """Classify multiple files at once and group them by category."""
    result = BatchResult()
    for name in filenames:
        result.add(recognize(name, default=default), name)
    return result


def register_extension(extension: str, category: str) -> None:
    """
    Add or override an extension's category at runtime.

    Example:
        register_extension("psd", "image")
    """
    ext = extension.lower().lstrip(".")
    CATEGORY_MAP.setdefault(category, set()).add(ext)
    _EXT_TO_CATEGORY[ext] = category
    if "." in ext and ext not in _MULTI_PART_EXTS:
        _MULTI_PART_EXTS.append(ext)
        _MULTI_PART_EXTS.sort(key=len, reverse=True)


# ---------------------------------------------------------------------------
# Simple CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ext_recognizer.py <file1> [file2 ...]")
        sys.exit(1)

    result = recognize_batch(sys.argv[1:])
    print(result.summary())


if __name__ == "__main__":
    _main()
