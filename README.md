# DocuSort

[![Tests](https://github.com/MahmoudAlmodalal/docu-sort/actions/workflows/python-tests.yml/badge.svg)](https://github.com/MahmoudAlmodalal/docu-sort/actions/workflows/python-tests.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-16a34a)](LICENSE)

**DocuSort** is a dependency-free document organizer for Windows, Linux, and Termux. It scans selected directories, copies supported documents into predictable extension-based folders, preserves existing files, and writes a machine-readable JSON report for every completed run.

> **Live demo:** [mahmoudalmodal.github.io/docu-sort](https://mahmoudalmodal.github.io/docu-sort/)

## Why DocuSort?

The project is designed for safe, repeatable organization rather than destructive file moves. By default, it scans the current user's home directory, never follows symbolic links, avoids the generated output directory, and resolves filename collisions by adding a numeric suffix such as `report_1.pdf`.

| Capability | Details |
|---|---|
| Supported formats | DOC, DOCX, TXT, RTF, ODT, PDF, XLS, XLSX, PPT, PPTX |
| Operating systems | Windows, Linux, and Termux |
| Default behavior | Copy files; never delete or move the originals |
| Collision handling | Preserve the original and create a numbered filename |
| Output | `documents/<TYPE>/` plus `organization_report.json` |
| Dependencies | Python standard library only |

## Quick start

```bash
python document_organizer.py \
  --destination ./organized \
  --root ./inbox
```

This creates the following structure:

```text
organized/
└── documents/
    ├── DOC/
    ├── DOCX/
    ├── PDF/
    ├── PPTX/
    ├── TXT/
    └── organization_report.json
```

Use a preview before copying files:

```bash
python document_organizer.py \
  --destination ./organized \
  --root ./inbox \
  --dry-run
```

Multiple source directories are supported by repeating `--root`:

```bash
python document_organizer.py \
  --destination ./organized \
  --root ~/Downloads \
  --root ~/Documents
```

The command also supports `--overwrite` when replacing same-name files is explicitly desired. Without that flag, existing files are preserved.

## Python API

```python
from pathlib import Path
from document_organizer import organize_documents

summary = organize_documents(
    destination=Path("./organized"),
    source_roots=[Path("./inbox")],
)

print(summary.copied)
```

## Web demo

The GitHub Pages site is a browser-based demonstration of the classification experience. It runs entirely in the browser: selected files are inspected by extension and displayed in their expected destination folders. The demo does not upload or modify files. For real filesystem organization, use the Python CLI above.

## Development

Run the standard-library test suite locally:

```bash
python -m unittest discover -s tests -v
```

The repository also runs the same tests automatically for every push and pull request through GitHub Actions.

## Safety notes

DocuSort copies files rather than moving them. Review the destination and the generated `organization_report.json` after each run, and use explicit `--root` values when working with sensitive or very large directories. A dry run is recommended before the first real copy operation.

## License

MIT License. See [LICENSE](LICENSE).