"""
Analytics endpoints.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, select, distinct

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from src.core.security import AuthContext, get_current_auth
from src.core.db import get_db, get_db_context, HoneypotStatus
from src.core.db.models import Honeypot, Session, AttackEvent, Adaptation
from src.core.db.repositories import HoneypotRepository, SessionRepository, AdaptationRepository


router = APIRouter()


class DashboardStats(BaseModel):
    """Dashboard statistics."""
    total_attacks: int
    active_honeypots: int
    active_sessions: int
    attacks_today: int
    attacks_by_type: dict
    attacks_by_severity: dict
    top_attackers: List[dict]
    attack_timeline: List[dict]
    honeypot_health: List[dict]


class TimeSeriesPoint(BaseModel):
    """Time series data point."""
    timestamp: datetime
    value: float


class TimeSeriesData(BaseModel):
    """Time series data."""
    metric: str
    data: List[TimeSeriesPoint]


class GeographicData(BaseModel):
    """Geographic attack data."""
    country_code: str
    country_name: str
    count: int
    severity_distribution: dict


class AttackLocation(BaseModel):
    """Attack location with coordinates for map visualization."""
    ip: str
    lat: float
    lng: float
    country: str
    city: Optional[str] = None
    attack_count: int
    last_attack: datetime
    attack_types: List[str]
    severity: str  # low, medium, high, critical


class AttackTimeline(BaseModel):
    """Attack timeline."""
    events: List[dict]
    start: datetime
    end: datetime
    interval: str  # hour, day, week


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    auth: AuthContext=Depends(get_current_auth),
):
    """Get dashboard statistics from real database data."""
    async with get_db_context() as session:
        # Get active honeypots count
        hp_repo = HoneypotRepository(session)
        active_honeypots = await hp_repo.count({"status": HoneypotStatus.RUNNING})
        
        # If no running, count all honeypots
        if active_honeypots == 0:
            total_hps = await hp_repo.count()
            active_honeypots = total_hps  # Show total if none marked as running
        
        # Get sessions from last 24h
        since = datetime.utcnow() - timedelta(hours=24)
        
        # Total attacks (all time)
        total_attacks_result = await session.execute(
            select(func.count()).select_from(AttackEvent)
        )
        total_attacks = total_attacks_result.scalar() or 0
        
        # Active sessions (not ended)
        active_sessions_result = await session.execute(
            select(func.count()).select_from(Session)
            .where(Session.ended_at.is_(None))
        )
        active_sessions = active_sessions_result.scalar() or 0
        
        # Attacks today (last 24h)
        attacks_today_result = await session.execute(
            select(func.count()).select_from(AttackEvent)
            .where(AttackEvent.timestamp >= since)
        )
        attacks_today = attacks_today_result.scalar() or 0
        
        # Attacks by type (from sessions)
        attacks_by_type_result = await session.execute(
            select(Session.attack_type, func.count().label('count'))
            .where(Session.started_at >= since)
            .group_by(Session.attack_type)
        )
        attacks_by_type = {}
        for row in attacks_by_type_result:
            if row[0]:
                attacks_by_type[row[0].value if hasattr(row[0], 'value') else str(row[0])] = row[1]
        
        # Attacks by severity (from attack events)
        attacks_by_severity_result = await session.execute(
            select(AttackEvent.severity, func.count().label('count'))
            .where(AttackEvent.timestamp >= since)
            .group_by(AttackEvent.severity)
        )
        attacks_by_severity = {}
        for row in attacks_by_severity_result:
            if row[0]:
                attacks_by_severity[row[0].value if hasattr(row[0], 'value') else str(row[0])] = row[1]
        
        # Top attackers (by source IP)
        top_attackers_result = await session.execute(
            select(Session.source_ip, func.count().label('count'))
            .where(Session.started_at >= since)
            .group_by(Session.source_ip)
            .order_by(func.count().desc())
            .limit(5)
        )
        top_attackers = [{"ip": row[0], "count": row[1]} for row in top_attackers_result]
        
        # Attack timeline (hourly for last 24h)
        attack_timeline = []
        for i in range(24):
            hour_start = datetime.utcnow() - timedelta(hours=23-i)
            hour_end = hour_start + timedelta(hours=1)
            
            count_result = await session.execute(
                select(func.count()).select_from(AttackEvent)
                .where(AttackEvent.timestamp >= hour_start)
                .where(AttackEvent.timestamp < hour_end)
            )
            count = count_result.scalar() or 0
            attack_timeline.append({
                "time": hour_start.isoformat(),
                "count": count
            })
        
        # Honeypot health (from database or Docker)
        honeypots_result = await session.execute(
            select(Honeypot)
        )
        honeypots = honeypots_result.scalars().all()
        honeypot_health = [
            {
                "id": h.id,
                "name": h.name,
                "health": 100 if h.status == HoneypotStatus.RUNNING else 50
            }
            for h in honeypots
        ]
        
        return DashboardStats(
            total_attacks=total_attacks,
            active_honeypots=active_honeypots,
            active_sessions=active_sessions,
            attacks_today=attacks_today,
            attacks_by_type=attacks_by_type,
            attacks_by_severity=attacks_by_severity,
            top_attackers=top_attackers,
            attack_timeline=attack_timeline,
            honeypot_health=honeypot_health,
        )


@router.get("/timeseries/{metric}", response_model=TimeSeriesData)
async def get_timeseries(
    metric: str,
    hours: int = Query(24, ge=1, le=168),
    interval: str = Query("hour", pattern="^(minute|hour|day)$"),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get time series data for a metric."""
    # TODO: Calculate from database
    
    return TimeSeriesData(
        metric=metric,
        data=[],
    )


@router.get("/geographic", response_model=List[GeographicData])
async def get_geographic_data(
    hours: int = Query(24, ge=1, le=168),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get geographic attack distribution."""
    # TODO: Calculate from database
    
    return []


@router.get("/attack-locations", response_model=List[AttackLocation])
async def get_attack_locations(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=500),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get attack locations with coordinates for map visualization."""
    from src.core.geoip import get_geoip_service

    async with get_db_context() as session:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get unique IPs with attack counts (SQLite compatible)
        result = await session.execute(
            select(
                Session.source_ip,
                func.count(Session.id).label('attack_count'),
                func.max(Session.started_at).label('last_attack'),
                Session.source_country,
            )
            .where(Session.started_at >= since)
            .where(Session.source_ip.isnot(None))
            .group_by(Session.source_ip, Session.source_country)
            .order_by(func.count(Session.id).desc())
            .limit(limit)
        )
        
        rows = result.fetchall()
        
        # Get attack types for all IPs in a single query
        unique_ips = [row.source_ip for row in rows if row.source_ip]
        attack_types_by_ip = {}
        
        if unique_ips:
            # Single query to get all attack types for all IPs
            types_result = await session.execute(
                select(Session.source_ip, Session.attack_type)
                .where(Session.source_ip.in_(unique_ips))
                .where(Session.started_at >= since)
                .distinct()
            )
            
            # Group attack types by IP
            for row in types_result.fetchall():
                ip = row[0]
                attack_type = row[1].value if hasattr(row[1], 'value') else str(row[1])
                if ip not in attack_types_by_ip:
                    attack_types_by_ip[ip] = []
                if len(attack_types_by_ip[ip]) < 5:  # Limit to 5 types per IP
                    attack_types_by_ip[ip].append(attack_type)
        
        # Bulk geolocate IPs
        geoip = get_geoip_service()
        locations = await geoip.bulk_lookup(unique_ips)
        
        attack_locations = []
        for row in rows:
            ip = row.source_ip
            geo = locations.get(ip)
            
            if not geo or geo.get('lat') is None:
                continue
            
            # Determine severity based on attack count
            if row.attack_count >= 100:
                severity = 'critical'
            elif row.attack_count >= 50:
                severity = 'high'
            elif row.attack_count >= 10:
                severity = 'medium'
            else:
                severity = 'low'
            
            attack_types = attack_types_by_ip.get(ip, [])
            
            attack_locations.append(AttackLocation(
                ip=ip,
                lat=geo['lat'],
                lng=geo['lng'],
                country=geo.get('country', row.source_country or 'Unknown'),
                city=geo.get('city'),
                attack_count=row.attack_count,
                last_attack=row.last_attack or datetime.utcnow(),
                attack_types=attack_types[:5],
                severity=severity,
            ))
        
        return attack_locations


@router.get("/timeline", response_model=AttackTimeline)
async def get_attack_timeline(
    hours: int = Query(24, ge=1, le=168),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get attack timeline."""
    # TODO: Calculate from database
    
    return AttackTimeline(
        events=[],
        start=datetime.utcnow() - timedelta(hours=hours),
        end=datetime.utcnow(),
        interval="hour",
    )


@router.get("/commands/top")
async def get_top_commands(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get most frequently used commands."""
    # TODO: Calculate from database
    
    return {"commands": []}


@router.get("/credentials/top")
async def get_top_credentials(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get most frequently attempted credentials."""
    # TODO: Calculate from database
    
    return {"credentials": []}