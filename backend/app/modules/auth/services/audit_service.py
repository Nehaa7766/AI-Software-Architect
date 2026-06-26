"""Durable audit logging that survives a request-transaction rollback.

Failed logins raise an exception (rolling back the request session), so their
audit entry must be written in its own committed transaction. Only use this for
events whose referenced user (if any) already exists committed in the DB — for
new-entity events, prefer same-session logging to stay FK-consistent.
"""
from app.db.session import AsyncSessionLocal
from app.models.user import AuthAuditLog


async def record_audit(
    *,
    event: str,
    user_id: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> None:
    async with AsyncSessionLocal() as session:
        session.add(
            AuthAuditLog(event=event, user_id=user_id, ip=ip, user_agent=user_agent)
        )
        await session.commit()
