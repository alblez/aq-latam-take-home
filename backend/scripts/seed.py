from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db import make_engine  # noqa: E402


def main() -> int:
    """Execute seed_data.sql against DATABASE_URL."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is required", file=sys.stderr)
        return 1

    seed_file = BACKEND_ROOT / "seed_data.sql"
    if not seed_file.exists():
        print(f"ERROR: seed file not found: {seed_file}", file=sys.stderr)
        return 1

    sql = seed_file.read_text()
    engine = make_engine(database_url)

    with engine.begin() as conn:
        conn.execute(text(sql))

    print(f"seed complete: {seed_file.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
