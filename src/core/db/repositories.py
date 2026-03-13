"""
Repository pattern for database access.
"""
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.db.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get a record by ID."""
        pk_column = list(self.model.__table__.primary_key.columns)[0]
        result = await self.session.execute(
            select(self.model).where(pk_column == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """Get a record by a specific field."""
        result = await self.session.execute(
            select(self.model).where(getattr(self.model, field) == value)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        descending: bool = False,
    ) -> List[ModelType]:
        """Get all records with pagination."""
        query = select(self.model)
        
        if order_by:
            column = getattr(self.model, order_by)
            if descending:
                column = column.desc()
            query = query.order_by(column)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        """Update a record by ID."""
        pk_column = list(self.model.__table__.primary_key.columns)[0]
        await self.session.execute(
            update(self.model).where(pk_column == id).values(**kwargs)
        )
        return await self.get_by_id(id)
    
    async def delete(self, id: Any) -> bool:
        """Delete a record by ID."""
        pk_column = list(self.model.__table__.primary_key.columns)[0]
        result = await self.session.execute(
            delete(self.model).where(pk_column == id)
        )
        return result.rowcount > 0
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for field, value in filters.items():
                query = query.where(getattr(self.model, field) == value)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def exists(self, **kwargs) -> bool:
        """Check if a record exists."""
        query = select(func.count()).select_from(self.model)
        for field, value in kwargs.items():
            query = query.where(getattr(self.model, field) == value)
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0


class HoneypotRepository(BaseRepository):
    """Repository for Honeypot model."""
    
    def __init__(self, session: AsyncSession):
        from src.core.db.models import Honeypot
        super().__init__(Honeypot, session)
    
    async def get_active(self) -> List[ModelType]:
        """Get all active honeypots."""
        from src.core.db.models import HoneypotStatus
        result = await self.session.execute(
            select(self.model).where(self.model.status == HoneypotStatus.RUNNING)
        )
        return list(result.scalars().all())
    
    async def get_with_sessions(self, honeypot_id: str):
        """Get honeypot with sessions loaded."""
        result = await self.session.execute(
            select(self.model)
            .options(selectinload(self.model.sessions))
            .where(self.model.id == honeypot_id)
        )
        return result.scalar_one_or_none()


class SessionRepository(BaseRepository):
    """Repository for Session model."""
    
    def __init__(self, session: AsyncSession):
        from src.core.db.models import Session
        super().__init__(Session, session)
    
    async def get_by_ip(self, ip: str, limit: int = 100):
        """Get sessions by source IP."""
        result = await self.session.execute(
            select(self.model)
            .where(self.model.source_ip == ip)
            .order_by(self.model.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_active(self, honeypot_id: str):
        """Get active sessions for a honeypot."""
        result = await self.session.execute(
            select(self.model)
            .where(self.model.honeypot_id == honeypot_id)
            .where(self.model.ended_at.is_(None))
        )
        return list(result.scalars().all())
    
    async def count_by_ip(self, ip: str) -> int:
        """Count sessions by IP."""
        result = await self.session.execute(
            select(func.count())
            .select_from(self.model)
            .where(self.model.source_ip == ip)
        )
        return result.scalar() or 0


class AttackEventRepository(BaseRepository):
    """Repository for AttackEvent model."""
    
    def __init__(self, session: AsyncSession):
        from src.core.db.models import AttackEvent
        super().__init__(AttackEvent, session)
    
    async def get_recent(self, hours: int = 24, limit: int = 100):
        """Get recent events."""
        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.session.execute(
            select(self.model)
            .where(self.model.timestamp >= since)
            .order_by(self.model.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class AdaptationRepository(BaseRepository):
    """Repository for Adaptation model."""
    
    def __init__(self, session: AsyncSession):
        from src.core.db.models import Adaptation
        super().__init__(Adaptation, session)
    
    async def get_for_honeypot(self, honeypot_id: str, limit: int = 50):
        """Get adaptations for a honeypot."""
        result = await self.session.execute(
            select(self.model)
            .where(self.model.honeypot_id == honeypot_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class AlertRepository(BaseRepository):
    """Repository for Alert model."""
    
    def __init__(self, session: AsyncSession):
        from src.core.db.models import Alert
        super().__init__(Alert, session)
    
    async def get_pending(self, limit: int = 100):
        """Get pending alerts."""
        from src.core.db.models import AlertStatus
        result = await self.session.execute(
            select(self.model)
            .where(self.model.status == AlertStatus.PENDING)
            .order_by(self.model.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_unacknowledged(self, limit: int = 100):
        """Get unacknowledged alerts."""
        from src.core.db.models import AlertStatus
        result = await self.session.execute(
            select(self.model)
            .where(self.model.status.in_([AlertStatus.PENDING, AlertStatus.SENT]))
            .order_by(self.model.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ThreatIntelRepository(BaseRepository):
    """Repository for ThreatIntelligence model."""
    
    def __init__(self, session: AsyncSession):
        from src.core.db.models import ThreatIntelligence
        super().__init__(ThreatIntelligence, session)
    
    async def lookup_ip(self, ip: str):
        """Look up threat intelligence for an IP."""
        result = await self.session.execute(
            select(self.model)
            .where(self.model.indicator_type == "ip")
            .where(self.model.indicator_value == ip)
        )
        return result.scalar_one_or_none()
    
    async def add_indicator(
        self,
        indicator_type: str,
        indicator_value: str,
        **kwargs
    ):
        """Add or update threat indicator."""
        existing = await self.session.execute(
            select(self.model)
            .where(self.model.indicator_type == indicator_type)
            .where(self.model.indicator_value == indicator_value)
        )
        existing = existing.scalar_one_or_none()
        
        if existing:
            # Update last_seen
            from datetime import datetime
            existing.last_seen = datetime.utcnow()
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return existing
        else:
            return await self.create(
                indicator_type=indicator_type,
                indicator_value=indicator_value,
                **kwargs
            )


class APIKeyRepository(BaseRepository):
    """Repository for APIKey model."""
    
    def __init__(self, session: AsyncSession):
        from src.core.db.models import APIKey
        super().__init__(APIKey, session)
    
    async def get_by_prefix(self, prefix: str):
        """Get API key by prefix."""
        result = await self.session.execute(
            select(self.model).where(self.model.key_prefix == prefix)
        )
        return result.scalar_one_or_none()
    
    async def record_usage(self, key_id: int):
        """Record API key usage."""
        from datetime import datetime
        await self.session.execute(
            update(self.model)
            .where(self.model.id == key_id)
            .values(
                last_used=datetime.utcnow(),
                total_requests=self.model.total_requests + 1
            )
        )