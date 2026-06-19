from __future__ import annotations

import re
from pathlib import Path

from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

# SQLAlchemy interprets :word patterns as bind parameters. The JSONB default
# contains "minQuestions":6 where :6 looks like bind param '6'. Escape lone
# colons while preserving :: (PostgreSQL type cast) via negative lookbehind.
_BIND_PARAM_RE = re.compile(r"(?<!:):(\w+)")


def _statements() -> list[str]:
    sql_path = Path(__file__).with_suffix(".sql")
    return [
        statement.strip() for statement in sql_path.read_text().split(";\n") if statement.strip()
    ]


def upgrade() -> None:
    for statement in _statements():
        safe = _BIND_PARAM_RE.sub(r"\:\1", statement)
        op.execute(safe)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS session_competency_scores")
    op.execute("DROP TABLE IF EXISTS turns")
    op.execute("DROP TABLE IF EXISTS sessions")
    op.execute("DROP TABLE IF EXISTS question_pack_items")
    op.execute("DROP TABLE IF EXISTS competencies")
    op.execute("DROP TABLE IF EXISTS jobs")
    op.execute("DROP TYPE IF EXISTS competency_category")
    op.execute("DROP TYPE IF EXISTS policy_action")
    op.execute("DROP TYPE IF EXISTS answer_input_mode")
    op.execute("DROP TYPE IF EXISTS turn_role")
    op.execute("DROP TYPE IF EXISTS completion_reason")
    op.execute("DROP TYPE IF EXISTS session_status")
