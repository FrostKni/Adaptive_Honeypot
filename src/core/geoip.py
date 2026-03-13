"""
GeoIP service for IP geolocation.
Uses free GeoIP databases and APIs for IP to location resolution.
"""
import asyncio
import aiohttp
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import lru_cache

logger = logging.getLogger(__name__)


class GeoIPService:
    """Service for resolving IP addresses to geographic locations."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = timedelta(hours=24)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _is_cached(self, ip: str) -> bool:
        """Check if IP is in cache and not expired."""
        if ip not in self._cache:
            return False
        cached = self._cache[ip]
        return datetime.utcnow() - cached['timestamp'] < self._cache_ttl
    
    async def lookup(self, ip: str) -> Optional[Dict[str, Any]]:
        """
        Look up geographic information for an IP address.
        
        Returns dict with:
            - lat: latitude
            - lng: longitude
            - country: country name
            - country_code: ISO country code
            - city: city name (if available)
            - region: region/state (if available)
        """
        # Check cache first
        if self._is_cached(ip):
            return self._cache[ip]['data']
        
        # Skip private/local IPs - return deterministic location immediately
        if self._is_private_ip(ip):
            result = self._get_default_location(ip)
            # Cache the result
            self._cache[ip] = {
                'data': result,
                'timestamp': datetime.utcnow()
            }
            return result
        
        result = None
        
        # Try ip-api.com (free, no API key needed, 45 requests/min)
        try:
            result = await self._lookup_ip_api_com(ip)
        except Exception as e:
            logger.debug(f"ip-api.com lookup failed for {ip}: {e}")
        
        # Fallback to ipapi.co if first fails
        if not result:
            try:
                result = await self._lookup_ipapi_co(ip)
            except Exception as e:
                logger.debug(f"ipapi.co lookup failed for {ip}: {e}")
        
        # Cache the result
        if result:
            self._cache[ip] = {
                'data': result,
                'timestamp': datetime.utcnow()
            }
        
        return result
    
    async def _lookup_ip_api_com(self, ip: str) -> Optional[Dict[str, Any]]:
        """Lookup using ip-api.com (free tier)."""
        session = await self._get_session()
        url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,region,city,lat,lon"
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('status') == 'success':
                    return {
                        'lat': data.get('lat'),
                        'lng': data.get('lon'),
                        'country': data.get('country', 'Unknown'),
                        'country_code': data.get('countryCode', 'XX'),
                        'city': data.get('city'),
                        'region': data.get('region'),
                    }
        return None
    
    async def _lookup_ipapi_co(self, ip: str) -> Optional[Dict[str, Any]]:
        """Lookup using ipapi.co (free tier)."""
        session = await self._get_session()
        url = f"https://ipapi.co/{ip}/json/"
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status == 200:
                data = await response.json()
                if 'error' not in data:
                    return {
                        'lat': data.get('latitude'),
                        'lng': data.get('longitude'),
                        'country': data.get('country_name', 'Unknown'),
                        'country_code': data.get('country_code', 'XX'),
                        'city': data.get('city'),
                        'region': data.get('region'),
                    }
        return None
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is private/local."""
        if not ip:
            return True
        
        # Check for localhost
        if ip in ('127.0.0.1', 'localhost', '::1'):
            return True
        
        # Check for private ranges
        parts = ip.split('.')
        if len(parts) == 4:
            try:
                first = int(parts[0])
                second = int(parts[1])
                
                # 10.0.0.0/8
                if first == 10:
                    return True
                # 172.16.0.0/12
                if first == 172 and 16 <= second <= 31:
                    return True
                # 192.168.0.0/16
                if first == 192 and second == 168:
                    return True
                # Docker default
                if first == 172 and second >= 16:
                    return True
            except ValueError:
                pass
        
        # Check for IPv6 local
        if ip.startswith('::') or ip.startswith('fe80::'):
            return True
        
        return False
    
    def _get_default_location(self, ip: str) -> Dict[str, Any]:
        """Get default location for private IPs (deterministic based on IP hash)."""
        import hashlib
        
        # For private IPs, generate deterministic location based on IP hash
        # This ensures the same IP always gets the same location
        ip_hash = int(hashlib.md5(ip.encode()).hexdigest(), 16)
        
        # Generate deterministic but varied coordinates
        lat = (ip_hash % 120) - 60  # Range: -60 to 60
        lng = ((ip_hash >> 16) % 360) - 180  # Range: -180 to 180
        
        return {
            'lat': lat,
            'lng': lng,
            'country': 'Unknown',
            'country_code': 'XX',
            'city': None,
            'region': None,
            'is_private': True,
        }
    
    async def bulk_lookup(self, ips: list[str]) -> Dict[str, Dict[str, Any]]:
        """Look up multiple IPs with rate limiting."""
        results = {}
        
        # Rate limit: 45 requests per minute for ip-api.com free tier
        # Process in batches of 40 with delays
        batch_size = 40
        for i in range(0, len(ips), batch_size):
            batch = ips[i:i + batch_size]
            
            # Lookup each IP in the batch
            tasks = [self.lookup(ip) for ip in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for ip, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to lookup {ip}: {result}")
                    results[ip] = None
                else:
                    results[ip] = result
            
            # Wait between batches to respect rate limits
            if i + batch_size < len(ips):
                await asyncio.sleep(60)  # Wait 1 minute between batches
        
        return results


# Singleton instance
_geoip_service: Optional[GeoIPService] = None


def get_geoip_service() -> GeoIPService:
    """Get or create the GeoIP service singleton."""
    global _geoip_service
    if _geoip_service is None:
        _geoip_service = GeoIPService()
    return _geoip_service