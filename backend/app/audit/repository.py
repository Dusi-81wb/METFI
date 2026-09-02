"""
Append-Only Audit Repository Interface and Concrete Implementations.

Strict Non-Negotiable Rules:
1. Append-Only: Provide CREATE and READ operations only. No UPDATE or DELETE methods.
2. Sequence monotonicity: Sequence numbers must be strictly sequential per case.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditEventDB
from app.domain.audit import AuditEvent


class AuditRepository(ABC):
    """Abstract protocol for append-only audit persistence."""

    @abstractmethod
    async def append_event(self, event: AuditEvent) -> AuditEvent:
        """Persist a new audit event append-only."""

    @abstractmethod
    async def get_event_by_id(self, event_id: str) -> AuditEvent | None:
        """Retrieve single audit event by unique event ID."""

    @abstractmethod
    async def get_events_by_case_id(self, case_id: str) -> list[AuditEvent]:
        """Retrieve full ordered audit trail for a case ID."""

    @abstractmethod
    async def get_events_by_correlation_id(self, correlation_id: str) -> list[AuditEvent]:
        """Retrieve all events linked by a correlation ID."""

    @abstractmethod
    async def get_latest_event_for_case(self, case_id: str) -> AuditEvent | None:
        """Retrieve the latest event for a case to determine next sequence number and hash."""


class InMemoryAuditRepository(AuditRepository):
    """
    Thread-safe in-memory audit repository for rapid testing and sandboxed environments.
    """

    def __init__(self) -> None:
        self._events_by_id: dict[str, AuditEvent] = {}
        self._events_by_case: dict[str, list[AuditEvent]] = {}
        self._events_by_correlation: dict[str, list[AuditEvent]] = {}
        self._lock = asyncio.Lock()

    async def append_event(self, event: AuditEvent) -> AuditEvent:
        async with self._lock:
            # Enforce immutability / duplicate check
            if event.event_id in self._events_by_id:
                raise ValueError(f"Audit event with ID '{event.event_id}' already exists.")

            self._events_by_id[event.event_id] = event

            if event.case_id not in self._events_by_case:
                self._events_by_case[event.case_id] = []
            self._events_by_case[event.case_id].append(event)

            if event.correlation_id not in self._events_by_correlation:
                self._events_by_correlation[event.correlation_id] = []
            self._events_by_correlation[event.correlation_id].append(event)

            return event

    async def get_event_by_id(self, event_id: str) -> AuditEvent | None:
        async with self._lock:
            return self._events_by_id.get(event_id)

    async def get_events_by_case_id(self, case_id: str) -> list[AuditEvent]:
        async with self._lock:
            events = self._events_by_case.get(case_id, [])
            return sorted(events, key=lambda e: e.sequence_number)

    async def get_events_by_correlation_id(self, correlation_id: str) -> list[AuditEvent]:
        async with self._lock:
            events = self._events_by_correlation.get(correlation_id, [])
            return sorted(events, key=lambda e: (e.case_id, e.sequence_number))

    async def get_latest_event_for_case(self, case_id: str) -> AuditEvent | None:
        async with self._lock:
            events = self._events_by_case.get(case_id, [])
            if not events:
                return None
            return max(events, key=lambda e: e.sequence_number)


class SQLAlchemyAuditRepository(AuditRepository):
    """
    PostgreSQL-backed append-only audit repository.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append_event(self, event: AuditEvent) -> AuditEvent:
        db_model = AuditEventDB.from_domain(event)
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        return db_model.to_domain()

    async def get_event_by_id(self, event_id: str) -> AuditEvent | None:
        stmt = select(AuditEventDB).where(AuditEventDB.event_id == event_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        return record.to_domain() if record else None

    async def get_events_by_case_id(self, case_id: str) -> list[AuditEvent]:
        stmt = (
            select(AuditEventDB)
            .where(AuditEventDB.case_id == case_id)
            .order_by(AuditEventDB.sequence_number.asc())
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        return [r.to_domain() for r in records]

    async def get_events_by_correlation_id(self, correlation_id: str) -> list[AuditEvent]:
        stmt = (
            select(AuditEventDB)
            .where(AuditEventDB.correlation_id == correlation_id)
            .order_by(AuditEventDB.timestamp.asc())
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        return [r.to_domain() for r in records]

    async def get_latest_event_for_case(self, case_id: str) -> AuditEvent | None:
        stmt = (
            select(AuditEventDB)
            .where(AuditEventDB.case_id == case_id)
            .order_by(AuditEventDB.sequence_number.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()
        return record.to_domain() if record else None
