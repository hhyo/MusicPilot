"""Manual database bootstrap entrypoint for Phase 2."""

from __future__ import annotations

import argparse
import json

from .services.metadata import bootstrap_metadata_storage


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize or reseed the MusicPilot Phase 2 SQLite database.")
    parser.add_argument(
        "--reseed",
        action="store_true",
        help="Clear current Phase 2 metadata tables and re-import the local seed catalog.",
    )
    args = parser.parse_args()

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
