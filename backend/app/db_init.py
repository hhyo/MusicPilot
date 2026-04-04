"""Manual database bootstrap entrypoint for the current SQLite runtime."""

from __future__ import annotations

import argparse
import json

from .core.db import rebuild_sqlite_database
from .services.metadata import bootstrap_metadata_storage


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize, reseed, or rebuild the MusicPilot SQLite database.")
    parser.add_argument(
        "--reseed",
        action="store_true",
        help="Clear current data tables and re-import the local seed catalog.",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete the current SQLite file and recreate the schema from scratch.",
    )
    args = parser.parse_args()

    if args.rebuild:
        rebuild_sqlite_database()
    result = bootstrap_metadata_storage(reseed=args.reseed)
    print(
        json.dumps(
            {
                "database_url": result.database_url,
                "provider": result.provider,
                "source_type": result.source_type,
                "seeded": result.seeded,
                "counts": result.counts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
