#!/usr/bin/env python3
"""
disorganizer.py

Generates a fake, jumbled-up "Downloads"-style folder full of junk test
files, meant as a testing sandbox for file-sorter applications.

Contents are FAKE STUBS: each file has a real, correct extension but its
body is just junk bytes / placeholder text (not a valid parseable file of
that type). This is fast and great for testing extension/name-based
sorting logic. It is NOT meant to test "is this actually a valid PDF"
style content validators.

Usage:
    python disorganizer.py
    python disorganizer.py --out ./MessyDownloads --count 300
    python disorganizer.py --seed 42 --clean

Run --help for all options.
"""

import argparse
import random
import shutil
import string
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Data pools
# --------------------------------------------------------------------------

EXTENSIONS = [
    # images
    "jpg", "jpeg", "png", "gif", "webp", "heic", "bmp", "svg",
    # documents
    "pdf", "docx", "doc", "txt", "rtf", "odt", "md",
    # spreadsheets / data
    "xlsx", "csv", "tsv", "json", "xml",
    # slides
    "pptx",
    # archives
    "zip", "rar", "7z", "tar", "gz",
    # audio/video
    "mp3", "wav", "mp4", "mov", "mkv",
    # code
    "py", "js", "html", "css", "java", "cpp",
    # misc / junk-drawer
    "exe", "dmg", "apk", "iso", "log", "tmp", "bak", "ini", "torrent",
]

WORDY_NAME_PARTS = [
    "IMG", "Screenshot", "Screen Shot", "Document", "Resume", "resume_final",
    "invoice", "Invoice", "receipt", "notes", "Notes", "untitled", "Untitled",
    "New Document", "Copy of", "draft", "Draft", "report", "Report",
    "presentation", "vacation", "photo", "meme", "download", "Download",
    "backup", "old", "final", "FINAL", "final_v2", "final_FINAL",
    "project", "assignment", "homework", "syllabus", "contract", "scan",
    "Scan", "export", "data", "config", "setup", "installer", "video",
    "clip", "recording", "voice_memo", "chart", "graph", "budget",
    "taxes", "2023", "2024", "2025", "temp", "test", "sample", "misc",
]

SEPARATORS = ["_", "-", " ", ""]

UNICODE_NAME_PARTS = [
    "café", "naïve", "résumé", "日本語", "文件", "документ", "über",
    "π_value", "emoji_😀_pic", "français", "español_niño", "ünïcödé",
    "北京", "мама", "hello_世界",
]

LONG_WORD_CHUNK = "supercalifragilisticexpialidocious_reallyreallylongfilenamethatgoesonandonandon"

DUPLICATE_SUFFIXES = ["", " (1)", " (2)", " (3)", "_copy", "_copy2", " - Copy", " - Copy (2)"]

NESTED_FOLDER_NAMES = [
    "New Folder", "Old Stuff", "unsorted", "misc", "backup", "2024",
    "school", "work", "random", "temp", "New Folder (1)", "New Folder (2)",
    "important", "DO NOT DELETE", "archive",
]

FAKE_MAGIC_BYTES = {
    "jpg": b"\xff\xd8\xff\xe0",
    "jpeg": b"\xff\xd8\xff\xe0",
    "png": b"\x89PNG\r\n\x1a\n",
    "gif": b"GIF89a",
    "pdf": b"%PDF-1.4\n",
    "zip": b"PK\x03\x04",
    "docx": b"PK\x03\x04",
    "xlsx": b"PK\x03\x04",
    "pptx": b"PK\x03\x04",
    "rar": b"Rar!\x1a\x07\x00",
    "7z": b"7z\xbc\xaf\x27\x1c",
    "exe": b"MZ",
    "gz": b"\x1f\x8b\x08",
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def random_junk_bytes(rng: random.Random, min_size: int = 16, max_size: int = 2048) -> bytes:
    size = rng.randint(min_size, max_size)
    return bytes(rng.getrandbits(8) for _ in range(size))


def build_file_body(rng: random.Random, ext: str) -> bytes:
    """Fake stub content: correct-looking magic bytes (when we know them)
    followed by junk, OR plain junk/text for unknown types."""
    magic = FAKE_MAGIC_BYTES.get(ext.lower(), b"")
    if ext.lower() in {"txt", "md", "csv", "tsv", "json", "xml", "html",
                        "css", "py", "js", "java", "cpp", "log", "ini"}:
        # text-ish junk so it's at least openable as text
        lines = [
            "This is placeholder test content generated for sorter testing.",
            f"Fake {ext} file — not real data.",
            "".join(rng.choices(string.ascii_letters + string.digits + "    ", k=40)),
        ]
        return ("\n".join(lines) + "\n").encode("utf-8")
    return magic + random_junk_bytes(rng)


def random_case(s: str, rng: random.Random) -> str:
    choice = rng.random()
    if choice < 0.15:
        return s.upper()
    if choice < 0.30:
        return s.lower()
    return s


def make_messy_name(rng: random.Random, used_names: set, force_style: str = None) -> str:
    """Build a messy base filename (no extension)."""
    style = force_style or rng.choices(
        ["normal", "unicode", "long", "spaces_dots", "numbers_only", "no_words"],
        weights=[45, 12, 8, 15, 10, 10],
        k=1,
    )[0]

    if style == "unicode":
        part = rng.choice(UNICODE_NAME_PARTS)
        suffix = str(rng.randint(1, 999)) if rng.random() < 0.4 else ""
        base = f"{part}{suffix}"

    elif style == "long":
        base = LONG_WORD_CHUNK
        if rng.random() < 0.5:
            base += "_" + str(rng.randint(1000, 9999))

    elif style == "spaces_dots":
        parts = rng.sample(WORDY_NAME_PARTS, k=rng.randint(2, 4))
        base = " . ".join(parts) + " "  # trailing space + odd dots, classic mess

    elif style == "numbers_only":
        base = "".join(rng.choices(string.digits, k=rng.randint(3, 10)))
        if rng.random() < 0.3:
            base = "IMG" + base
        if rng.random() < 0.3:
            base = "VID" + base

    elif style == "no_words":
        base = "".join(rng.choices(string.ascii_lowercase + string.digits, k=8))

    else:  # normal
        n_parts = rng.randint(1, 3)
        parts = rng.sample(WORDY_NAME_PARTS, k=n_parts)
        sep = rng.choice(SEPARATORS)
        base = sep.join(random_case(p.replace(" ", sep if sep else "_"), rng) for p in parts)
        if rng.random() < 0.35:
            base += sep + str(rng.randint(1, 9999))

    base = base.strip()
    if not base:
        base = "file"

    return base


def unique_path(folder: Path, base: str, ext: str) -> Path:
    """Avoid accidental real collisions on disk (not the same as intentional
    'duplicate' files, which get their own explicit (1)/(2)/copy suffixes)."""
    candidate = folder / (f"{base}.{ext}" if ext else base)
    n = 1
    while candidate.exists():
        candidate = folder / (f"{base}_{n}.{ext}" if ext else f"{base}_{n}")
        n += 1
    return candidate


# --------------------------------------------------------------------------
# Generation
# --------------------------------------------------------------------------

def generate(
    out_dir: Path,
    count: int,
    rng: random.Random,
    duplicate_ratio: float = 0.12,
    no_ext_ratio: float = 0.06,
    empty_ratio: float = 0.05,
    nested_ratio: float = 0.25,
    max_nest_depth: int = 3,
):
    out_dir.mkdir(parents=True, exist_ok=True)

    created = []
    duplicate_pool = []  # (base, ext, body) tuples eligible for duplication later

    for i in range(count):
        # Decide destination folder: root or nested
        dest = out_dir
        if rng.random() < nested_ratio:
            depth = rng.randint(1, max_nest_depth)
            for _ in range(depth):
                dest = dest / rng.choice(NESTED_FOLDER_NAMES)
            dest.mkdir(parents=True, exist_ok=True)

        # Decide extension / no-extension
        has_ext = rng.random() >= no_ext_ratio
        ext = rng.choice(EXTENSIONS) if has_ext else ""

        base = make_messy_name(rng, used_names=set())
        path = unique_path(dest, base, ext)

        is_empty = rng.random() < empty_ratio
        body = b"" if is_empty else build_file_body(rng, ext)

        path.write_bytes(body)
        created.append(path)

        if not is_empty and rng.random() < duplicate_ratio:
            duplicate_pool.append((dest, base, ext, body))

    # Create intentional duplicates (same content, "(1)", "copy", etc. names)
    for dest, base, ext, body in duplicate_pool:
        n_dupes = rng.randint(1, 2)
        for _ in range(n_dupes):
            suffix = rng.choice(DUPLICATE_SUFFIXES)
            dup_base = f"{base}{suffix}"
            dup_path = unique_path(dest, dup_base, ext)
            dup_path.write_bytes(body)  # identical bytes = true duplicate
            created.append(dup_path)

    return created


def print_summary(created, out_dir: Path):
    ext_counts = {}
    no_ext = 0
    empty = 0
    nested = 0
    for p in created:
        if p.suffix:
            ext = p.suffix[1:].lower()
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        else:
            no_ext += 1
        try:
            if p.stat().st_size == 0:
                empty += 1
        except FileNotFoundError:
            pass
        if p.parent != out_dir:
            nested += 1

    print(f"\nGenerated {len(created)} files in: {out_dir.resolve()}")
    print(f"  Nested in subfolders : {nested}")
    print(f"  No extension         : {no_ext}")
    print(f"  Empty files          : {empty}")
    print(f"  Distinct extensions  : {len(ext_counts)}")
    top = sorted(ext_counts.items(), key=lambda kv: -kv[1])[:8]
    if top:
        print("  Top extensions       :", ", ".join(f"{e}({c})" for e, c in top))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a jumbled, fake Downloads-style folder for testing sorter apps."
    )
    parser.add_argument("--out", type=str, default="./MessyDownloads",
                         help="Output directory (default: ./MessyDownloads)")
    parser.add_argument("--count", type=int, default=200,
                         help="Number of base files to generate before duplicates (default: 200)")
    parser.add_argument("--seed", type=int, default=None,
                         help="Random seed for reproducible output")
    parser.add_argument("--clean", action="store_true",
                         help="Delete the output directory first if it already exists")
    parser.add_argument("--duplicate-ratio", type=float, default=0.12,
                         help="Fraction of files that get duplicate copies (default: 0.12)")
    parser.add_argument("--no-ext-ratio", type=float, default=0.06,
                         help="Fraction of files with no extension (default: 0.06)")
    parser.add_argument("--empty-ratio", type=float, default=0.05,
                         help="Fraction of files that are 0 bytes (default: 0.05)")
    parser.add_argument("--nested-ratio", type=float, default=0.25,
                         help="Fraction of files placed in nested junk folders (default: 0.25)")
    parser.add_argument("--max-depth", type=int, default=3,
                         help="Max nesting depth for subfolders (default: 3)")

    args = parser.parse_args()
    out_dir = Path(args.out)

    if args.clean and out_dir.exists():
        shutil.rmtree(out_dir)

    rng = random.Random(args.seed)

    created = generate(
        out_dir=out_dir,
        count=args.count,
        rng=rng,
        duplicate_ratio=args.duplicate_ratio,
        no_ext_ratio=args.no_ext_ratio,
        empty_ratio=args.empty_ratio,
        nested_ratio=args.nested_ratio,
        max_nest_depth=args.max_depth,
    )

    print_summary(created, out_dir)


if __name__ == "__main__":
    sys.exit(main())
