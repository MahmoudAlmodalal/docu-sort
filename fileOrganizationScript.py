
"""Compatibility entry point for older users of DocuSort.

Use ``document_organizer.py`` for the current command-line interface.
"""

from document_organizer import main


if __name__ == "__main__":
    raise SystemExit(main())
