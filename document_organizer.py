"""Sort supported document files into extension-based folders.

The module exposes a small Python API and a command-line interface. It is
intentionally dependency-free so it can run on desktop Linux, Windows, and
Termux without a package installation step.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import string
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


EXTENSION_TO_FOLDER: dict[str, str] = {
    ".doc": "DOC",
    ".docx": "DOCX",
    ".txt": "TXT",
    ".rtf": "RTF",
    ".odt": "ODT",
    ".pdf": "PDF",
    ".xls": "XLS",
    ".xlsx": "XLSX",
    ".ppt": "PPT",
    ".pptx": "PPTX",
}


@dataclass
class OrganizationSummary:
    """Metrics and messages produced by one organization run."""

    scanned: int = 0
    supported: int = 0
    copied: int = 0
    skipped: int = 0
    errors: int = 0
    copied_files: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


class OrganizerError(Exception):
    """Raised when the requested organization run cannot be started."""


def default_source_roots() -> list[Path]:
    """Return safe, platform-aware roots to scan when none are provided."""

    if os.name == "nt":
        return [
            Path(f"{drive}:/")
            for drive in string.ascii_uppercase
            if Path(f"{drive}:/").exists()
        ]

    termux_shared = Path("/data/data/com.termux/files/home/storage/shared")
    if termux_shared.exists():
        return [termux_shared]

    # Scanning the user's home directory is safer than scanning the whole OS.
    return [Path.home()]


def _is_within(path: Path, roots: Sequence[Path]) -> bool:
    """Return whether *path* is equal to or nested below one of *roots*."""

    candidate = path.resolve(strict=False)
    return any(candidate == root or root in candidate.parents for root in roots)


def iter_files(root: Path, excluded_roots: Sequence[Path] = ()) -> Iterable[Path]:
    """Yield regular files below *root*, ignoring inaccessible directories."""

    if not root.exists() or not root.is_dir():
        return

    excluded = [item.resolve(strict=False) for item in excluded_roots]
    if _is_within(root, excluded):
        return

    for current, directories, filenames in os.walk(
        root, topdown=True, followlinks=False
    ):
        current_path = Path(current)
        directories[:] = [
            directory
            for directory in directories
            if not _is_within(current_path / directory, excluded)
        ]
        for filename in filenames:
            candidate = current_path / filename
            try:
                if candidate.is_symlink() or not candidate.is_file():
                    continue
            except OSError:
                continue
            yield candidate


def _unique_destination(target: Path, overwrite: bool) -> Path:
    """Choose a collision-safe destination for an already-used filename."""

    if not target.exists() or overwrite:
        return target

    stem, suffix = target.stem, target.suffix
    counter = 1
    while True:
        candidate = target.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _copy_file(source: Path, folder: Path, overwrite: bool) -> Path | None:
    """Copy a file into *folder* and return the created path when copied."""

    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / source.name
    if destination.exists():
        try:
            if destination.samefile(source):
                return None
        except OSError:
            pass
        if overwrite:
            shutil.copy2(source, destination)
            return destination
        destination = _unique_destination(destination, overwrite=False)

    shutil.copy2(source, destination)
    return destination


def write_report(output_dir: Path, summary: OrganizationSummary) -> Path:
    """Write a machine-readable report and return its path."""

    report_path = output_dir / "organization_report.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": asdict(summary),
    }
    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report_path


def organize_documents(
    destination: Path,
    source_roots: Sequence[Path] | None = None,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
    output_folder_name: str = "documents",
    create_report: bool = True,
) -> OrganizationSummary:
    """Organize supported documents found below the requested source roots.

    ``destination`` is the parent directory in which the output folder is
    created. Existing files are preserved by default; name collisions receive
    a numeric suffix such as ``report_1.pdf``.
    """

    if not destination.exists():
        if not dry_run:
            destination.mkdir(parents=True, exist_ok=True)
    elif not destination.is_dir():
        raise OrganizerError(f"Destination is not a directory: {destination}")

    output_dir = destination / output_folder_name
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        for folder_name in sorted(set(EXTENSION_TO_FOLDER.values())):
            (output_dir / folder_name).mkdir(exist_ok=True)

    roots = list(source_roots or default_source_roots())
    roots = [root.expanduser().resolve(strict=False) for root in roots]
    excluded_roots = [output_dir]
    summary = OrganizationSummary()

    for root in roots:
        for source in iter_files(root, excluded_roots):
            summary.scanned += 1
            folder_name = EXTENSION_TO_FOLDER.get(source.suffix.lower())
            if folder_name is None:
                continue
            summary.supported += 1
            if dry_run:
                summary.copied += 1
                summary.copied_files.append(str(source))
                continue

            try:
                created = _copy_file(source, output_dir / folder_name, overwrite)
                if created is None:
                    summary.skipped += 1
                    summary.messages.append(f"Skipped existing file: {source}")
                else:
                    summary.copied += 1
                    summary.copied_files.append(str(created))
            except (OSError, shutil.Error) as error:
                summary.errors += 1
                summary.messages.append(f"Could not copy {source}: {error}")

    if create_report and not dry_run:
        write_report(output_dir, summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        description="Safely organize documents by file extension."
    )
    parser.add_argument(
        "-d",
        "--destination",
        type=Path,
        help="Parent directory for the generated documents/ folder.",
    )
    parser.add_argument(
        "-r",
        "--root",
        action="append",
        type=Path,
        help="Source directory to scan; repeat the option for multiple roots.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview supported files without copying anything.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace destination files with the same name instead of suffixing them.",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Do not write organization_report.json.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    args = build_parser().parse_args(argv)
    destination = args.destination
    if destination is None:
        destination = Path(input("Destination parent directory: ").strip()).expanduser()
    if not str(destination):
        print("A destination directory is required.")
        return 2

    try:
        summary = organize_documents(
            destination,
            args.root,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
            create_report=not args.no_report,
        )
    except (OrganizerError, OSError) as error:
        print(f"Error: {error}")
        return 1

    mode = "Preview" if args.dry_run else "Completed"
    print(f"{mode}: scanned {summary.scanned} files; found {summary.supported} supported documents.")
    print(f"Copied: {summary.copied} | Skipped: {summary.skipped} | Errors: {summary.errors}")
    if not args.dry_run:
        print(f"Output: {destination / 'documents'}")
    return 0 if summary.errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
