import json 

from ..schema import STAGE_ORDER
from ..connection import get_conn
 
 
def save_checkpoint(job_id: str, stage: str, data: dict) -> None:
    """Upsert a checkpoint. `data` is already model_dump()'d."""
    payload = json.dumps(data, default=str)   # default=str handles datetime etc.
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO checkpoints (job_id, stage, payload)
               VALUES (?, ?, ?)
               ON CONFLICT(job_id, stage) DO UPDATE SET
                   payload  = excluded.payload,
                   saved_at = datetime('now')""",
            (job_id, stage, payload),
        )

def load_checkpoint(job_id: str, stage: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT payload FROM checkpoints WHERE job_id = ? AND stage = ?",
            (job_id, stage),
        ).fetchone()
        return json.loads(row["payload"]) if row else None

def last_completed_stage(job_id: str) -> str:
    """Return the latest stage that has a saved checkpoint (or 'PENDING')."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT stage FROM checkpoints WHERE job_id = ?", (job_id,)
        ).fetchall()
    completed = {r["stage"] for r in rows}
    # walk STAGE_ORDER in reverse, return first match
    for stage in reversed(STAGE_ORDER):
        if stage in completed:
            return stage
    return "PENDING"