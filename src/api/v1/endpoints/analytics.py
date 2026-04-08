"""
Analytics endpoints.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, select, distinct, case
import requests
import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from src.core.security import AuthContext, get_current_auth
from src.core.db import get_db, get_db_context, HoneypotStatus
from src.core.db.models import Honeypot, Session, AttackEvent, Adaptation
from src.core.db.repositories import (
    HoneypotRepository,
    SessionRepository,
    AdaptationRepository,
)


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
    auth: AuthContext = Depends(get_current_auth),
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
            select(func.count()).select_from(Session).where(Session.ended_at.is_(None))
        )
        active_sessions = active_sessions_result.scalar() or 0

        # Attacks today (last 24h)
        attacks_today_result = await session.execute(
            select(func.count())
            .select_from(AttackEvent)
            .where(AttackEvent.timestamp >= since)
        )
        attacks_today = attacks_today_result.scalar() or 0

        # Attacks by type (from sessions)
        attacks_by_type_result = await session.execute(
            select(Session.attack_type, func.count().label("count"))
            .where(Session.started_at >= since)
            .group_by(Session.attack_type)
        )
        attacks_by_type = {}
        for row in attacks_by_type_result:
            if row[0]:
                attacks_by_type[
                    row[0].value if hasattr(row[0], "value") else str(row[0])
                ] = row[1]

        # Attacks by severity (from attack events)
        attacks_by_severity_result = await session.execute(
            select(AttackEvent.severity, func.count().label("count"))
            .where(AttackEvent.timestamp >= since)
            .group_by(AttackEvent.severity)
        )
        attacks_by_severity = {}
        for row in attacks_by_severity_result:
            if row[0]:
                attacks_by_severity[
                    row[0].value if hasattr(row[0], "value") else str(row[0])
                ] = row[1]

        # Top attackers (by source IP)
        top_attackers_result = await session.execute(
            select(Session.source_ip, func.count().label("count"))
            .where(Session.started_at >= since)
            .group_by(Session.source_ip)
            .order_by(func.count().desc())
            .limit(5)
        )
        top_attackers = [
            {"ip": row[0], "count": row[1]} for row in top_attackers_result
        ]

        # Attack timeline (hourly for last 24h)
        attack_timeline = []
        for i in range(24):
            hour_start = datetime.utcnow() - timedelta(hours=23 - i)
            hour_end = hour_start + timedelta(hours=1)

            count_result = await session.execute(
                select(func.count())
                .select_from(AttackEvent)
                .where(AttackEvent.timestamp >= hour_start)
                .where(AttackEvent.timestamp < hour_end)
            )
            count = count_result.scalar() or 0
            attack_timeline.append({"time": hour_start.isoformat(), "count": count})

        # Honeypot health (from database or Docker)
        honeypots_result = await session.execute(select(Honeypot))
        honeypots = honeypots_result.scalars().all()
        honeypot_health = [
            {
                "id": h.id,
                "name": h.name,
                "health": 100 if h.status == HoneypotStatus.RUNNING else 50,
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
    async with get_db_context() as session:
        since = datetime.utcnow() - timedelta(hours=hours)

        # Determine interval in minutes
        interval_minutes = {"minute": 1, "hour": 60, "day": 1440}[interval]

        # Calculate number of data points
        num_points = min((hours * 60) // interval_minutes, 500)

        data_points = []

        # Generate time buckets
        for i in range(num_points):
            bucket_start = datetime.utcnow() - timedelta(
                minutes=interval_minutes * (num_points - i - 1)
            )
            bucket_end = bucket_start + timedelta(minutes=interval_minutes)

            # Query based on metric
            if metric == "attacks":
                result = await session.execute(
                    select(func.count())
                    .select_from(AttackEvent)
                    .where(AttackEvent.timestamp >= bucket_start)
                    .where(AttackEvent.timestamp < bucket_end)
                )
                value = float(result.scalar() or 0)

            elif metric == "sessions":
                result = await session.execute(
                    select(func.count())
                    .select_from(Session)
                    .where(Session.started_at >= bucket_start)
                    .where(Session.started_at < bucket_end)
                )
                value = float(result.scalar() or 0)

            elif metric == "unique_ips":
                result = await session.execute(
                    select(func.count(distinct(Session.source_ip)))
                    .where(Session.started_at >= bucket_start)
                    .where(Session.started_at < bucket_end)
                )
                value = float(result.scalar() or 0)

            elif metric == "severity_avg":
                # Calculate average severity score
                result = await session.execute(
                    select(
                        func.avg(
                            case(
                                (AttackEvent.severity == "critical", 4),
                                (AttackEvent.severity == "high", 3),
                                (AttackEvent.severity == "medium", 2),
                                (AttackEvent.severity == "low", 1),
                                else_=0,
                            )
                        )
                    )
                    .select_from(AttackEvent)
                    .where(AttackEvent.timestamp >= bucket_start)
                    .where(AttackEvent.timestamp < bucket_end)
                )
                value = float(result.scalar() or 0)

            else:
                # Unknown metric, return 0
                value = 0.0

            data_points.append(TimeSeriesPoint(timestamp=bucket_start, value=value))

        return TimeSeriesData(
            metric=metric,
            data=data_points,
        )


@router.get("/geographic", response_model=List[GeographicData])
async def get_geographic_data(
    hours: int = Query(24, ge=1, le=168),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get geographic attack distribution."""
    async with get_db_context() as session:
        since = datetime.utcnow() - timedelta(hours=hours)

        # Query sessions grouped by country
        result = await session.execute(
            select(
                Session.source_country,
                func.count(Session.id).label("count"),
                func.sum(case((Session.severity == "critical", 1), else_=0)).label(
                    "critical"
                ),
                func.sum(case((Session.severity == "high", 1), else_=0)).label("high"),
                func.sum(case((Session.severity == "medium", 1), else_=0)).label(
                    "medium"
                ),
                func.sum(case((Session.severity == "low", 1), else_=0)).label("low"),
            )
            .where(Session.started_at >= since)
            .where(Session.source_country.isnot(None))
            .group_by(Session.source_country)
            .order_by(func.count(Session.id).desc())
            .limit(50)
        )

        geographic_data = []
        for row in result:
            # Map country codes to names (basic mapping)
            country_names = {
                "US": "United States",
                "CN": "China",
                "RU": "Russia",
                "BR": "Brazil",
                "IN": "India",
                "DE": "Germany",
                "GB": "United Kingdom",
                "FR": "France",
                "JP": "Japan",
                "KR": "South Korea",
                "NL": "Netherlands",
                "AU": "Australia",
                "CA": "Canada",
                "IT": "Italy",
                "ES": "Spain",
            }

            country_code = row.source_country or "XX"
            geographic_data.append(
                GeographicData(
                    country_code=country_code,
                    country_name=country_names.get(country_code, country_code),
                    count=row.count,
                    severity_distribution={
                        "critical": int(row.critical or 0),
                        "high": int(row.high or 0),
                        "medium": int(row.medium or 0),
                        "low": int(row.low or 0),
                    },
                )
            )

        return geographic_data


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
                func.count(Session.id).label("attack_count"),
                func.max(Session.started_at).label("last_attack"),
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
                attack_type = row[1].value if hasattr(row[1], "value") else str(row[1])
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

            if not geo or geo.get("lat") is None:
                continue

            # Determine severity based on attack count
            if row.attack_count >= 100:
                severity = "critical"
            elif row.attack_count >= 50:
                severity = "high"
            elif row.attack_count >= 10:
                severity = "medium"
            else:
                severity = "low"

            attack_types = attack_types_by_ip.get(ip, [])

            attack_locations.append(
                AttackLocation(
                    ip=ip,
                    lat=geo["lat"],
                    lng=geo["lng"],
                    country=geo.get("country", row.source_country or "Unknown"),
                    city=geo.get("city"),
                    attack_count=row.attack_count,
                    last_attack=row.last_attack or datetime.utcnow(),
                    attack_types=attack_types[:5],
                    severity=severity,
                )
            )

        return attack_locations


@router.get("/timeline", response_model=AttackTimeline)
async def get_attack_timeline(
    hours: int = Query(24, ge=1, le=168),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get attack timeline."""
    async with get_db_context() as session:
        since = datetime.utcnow() - timedelta(hours=hours)

        # Get detailed attack events with session info
        result = await session.execute(
            select(
                AttackEvent.id,
                AttackEvent.event_type,
                AttackEvent.timestamp,
                AttackEvent.severity,
                AttackEvent.data,
                Session.source_ip,
                Session.attack_type,
                Session.honeypot_id,
            )
            .join(Session, AttackEvent.session_id == Session.id, isouter=True)
            .where(AttackEvent.timestamp >= since)
            .order_by(AttackEvent.timestamp.desc())
            .limit(100)
        )

        events = []
        for row in result:
            event_data = {
                "id": row.id,
                "event_type": row.event_type,
                "timestamp": row.timestamp.isoformat(),
                "severity": row.severity.value
                if hasattr(row.severity, "value")
                else str(row.severity),
                "source_ip": row.source_ip,
                "attack_type": row.attack_type.value
                if row.attack_type and hasattr(row.attack_type, "value")
                else str(row.attack_type)
                if row.attack_type
                else None,
                "honeypot_id": row.honeypot_id,
                "details": row.data or {},
            }
            events.append(event_data)

        return AttackTimeline(
            events=events,
            start=since,
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
    async with get_db_context() as session:
        since = datetime.utcnow() - timedelta(hours=hours)

        # Get sessions with commands
        result = await session.execute(
            select(Session.commands, Session.source_ip)
            .where(Session.started_at >= since)
            .where(Session.commands != [])
        )

        # Aggregate commands
        command_counts = {}
        command_ips = {}

        for row in result:
            commands = row.commands or []
            source_ip = row.source_ip

            for cmd in commands:
                if isinstance(cmd, str):
                    # Normalize command (remove arguments, get base command)
                    base_cmd = cmd.split()[0] if cmd.split() else cmd

                    if base_cmd not in command_counts:
                        command_counts[base_cmd] = 0
                        command_ips[base_cmd] = set()

                    command_counts[base_cmd] += 1
                    command_ips[base_cmd].add(source_ip)

        # Sort by count and get top N
        sorted_commands = sorted(
            command_counts.items(), key=lambda x: x[1], reverse=True
        )[:limit]

        commands = [
            {
                "command": cmd,
                "count": count,
                "unique_sources": len(command_ips.get(cmd, set())),
            }
            for cmd, count in sorted_commands
        ]

        return {"commands": commands}


@router.get("/credentials/top")
async def get_top_credentials(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(get_current_auth),
):
    """Get most frequently attempted credentials."""
    async with get_db_context() as session:
        since = datetime.utcnow() - timedelta(hours=hours)

        # Get sessions with credentials
        result = await session.execute(
            select(Session.credentials_tried, Session.source_ip).where(
                Session.started_at >= since
            )
        )

        # Aggregate credentials
        credential_counts = {}
        credential_ips = {}
        success_counts = {}

        for row in result:
            credentials = row.credentials_tried or []
            source_ip = row.source_ip

            for cred in credentials:
                if isinstance(cred, dict):
                    username = cred.get("username", "")
                    password = cred.get("password", "")
                    success = cred.get("success", False)

                    # Create key for username/password pair
                    key = f"{username}:{password}"

                    if key not in credential_counts:
                        credential_counts[key] = 0
                        credential_ips[key] = set()
                        success_counts[key] = 0

                    credential_counts[key] += 1
                    credential_ips[key].add(source_ip)
                    if success:
                        success_counts[key] += 1

        # Sort by count and get top N
        sorted_credentials = sorted(
            credential_counts.items(), key=lambda x: x[1], reverse=True
        )[:limit]

        credentials = [
            {
                "username": cred.split(":")[0] if ":" in cred else cred,
                "password": cred.split(":")[1]
                if ":" in cred and len(cred.split(":")) > 1
                else "",
                "count": count,
                "unique_sources": len(credential_ips.get(cred, set())),
                "successful_attempts": success_counts.get(cred, 0),
            }
            for cred, count in sorted_credentials
        ]

        return {"credentials": credentials}


class ServerLocation(BaseModel):
    """Server geolocation information."""
    ip: str
    city: str
    country: str
    country_code: str
    region: str
    lat: float
    lng: float
    isp: str
    timezone: str


# Cache for server location (refresh every hour)
_server_location_cache: Optional[ServerLocation] = None
_server_location_timestamp: Optional[datetime] = None


def get_server_location() -> ServerLocation:
    """Get the server's geolocation using external IP."""
    global _server_location_cache, _server_location_timestamp
    
    # Check cache (refresh every hour)
    if _server_location_cache and _server_location_timestamp:
        if datetime.now() - _server_location_timestamp < timedelta(hours=1):
            return _server_location_cache
    
    try:
        # Get external IP
        ip_response = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip_data = ip_response.json()
        server_ip = ip_data['ip']
        
        # Get geolocation for the IP
        geo_response = requests.get(
            f'http://ip-api.com/json/{server_ip}',
            timeout=5
        )
        geo_data = geo_response.json()
        
        if geo_data.get('status') == 'success':
            _server_location_cache = ServerLocation(
                ip=server_ip,
                city=geo_data.get('city', 'Unknown'),
                country=geo_data.get('country', 'Unknown'),
                country_code=geo_data.get('countryCode', 'XX'),
                region=geo_data.get('regionName', 'Unknown'),
                lat=geo_data.get('lat', 0.0),
                lng=geo_data.get('lon', 0.0),
                isp=geo_data.get('isp', 'Unknown'),
                timezone=geo_data.get('timezone', 'UTC'),
            )
            _server_location_timestamp = datetime.now()
            
            logger.info(
                f"Server location detected: {_server_location_cache.city}, "
                f"{_server_location_cache.country} [{server_ip}]"
            )
            return _server_location_cache
    except Exception as e:
        logger.warning(f"Failed to get server location: {e}")
    
    # Fallback to a default location if geolocation fails
    return ServerLocation(
        ip='unknown',
        city='Unknown',
        country='Unknown',
        country_code='XX',
        region='Unknown',
        lat=0.0,
        lng=0.0,
        isp='Unknown',
        timezone='UTC',
    )


@router.get("/server-location", response_model=ServerLocation)
async def get_server_geolocation(
    auth: AuthContext = Depends(get_current_auth),
):
    """
    Get the server's actual geolocation based on its public IP address.
    
    This endpoint detects the server's real location and returns:
    - IP address
    - City and country
    - Geographic coordinates (lat/lng)
    - ISP information
    - Timezone
    
    The location is cached for 1 hour to avoid excessive API calls.
    """
    return get_server_location()
