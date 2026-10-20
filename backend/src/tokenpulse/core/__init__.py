"""Pure money-path logic.

Nothing in ``tokenpulse.core`` may import from ``tokenpulse.db``, ``tokenpulse.api``,
or ``tokenpulse.ingestion``. Everything here is a deterministic pure function of its
inputs plus pinned config versions (constitution Principles III and V).
"""
