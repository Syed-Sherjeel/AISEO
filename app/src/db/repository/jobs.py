
from ..connection import get_conn



def create_job(job_id: str, query: str, word_count: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO jobs (id, query, word_count, status) VALUES (?, ?, ?, 'PENDING')",
            (job_id, query, word_count),
        )

def set_job_status(job_id: str, status: str, error: str | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            """UPDATE jobs
               SET status = ?, error = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (status, error, job_id),
        )

def get_job(job_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None

def list_jobs() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]