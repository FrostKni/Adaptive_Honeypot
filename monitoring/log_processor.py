import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from core.models import AttackEvent, AttackSeverity
import logging

logger = logging.getLogger(__name__)

class LogProcessor:
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Patterns for log parsing
        self.patterns = {
            'login_attempt': re.compile(r'login attempt \[(.+?)/(.+?)\] failed'),
            'command': re.compile(r'CMD: (.+)'),
            'connection': re.compile(r'New connection: (.+?):(\d+)'),
            'session': re.compile(r'Session: (\w+)'),
        }
    
    def parse_cowrie_log(self, log_file: Path) -> List[AttackEvent]:
        events = []
        
        if not log_file.exists():
            return events
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        event = self._parse_log_entry(log_entry)
                        if event:
                            events.append(event)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.error(f"Failed to parse log {log_file}: {e}")
        
        return events
    
    def _parse_log_entry(self, entry: Dict) -> Optional[AttackEvent]:
        event_id = entry.get('eventid')
        
        if event_id == 'cowrie.login.failed':
            return AttackEvent(
                timestamp=datetime.fromisoformat(entry['timestamp']),
                honeypot_id=entry.get('sensor', 'unknown'),
                source_ip=entry.get('src_ip', '0.0.0.0'),
                source_port=entry.get('src_port', 0),
                username=entry.get('username'),
                password=entry.get('password'),
                commands=[],
                session_id=entry.get('session', 'unknown'),
                severity=AttackSeverity.LOW,
                attack_type='brute_force'
            )
        
        elif event_id == 'cowrie.command.input':
            return AttackEvent(
                timestamp=datetime.fromisoformat(entry['timestamp']),
                honeypot_id=entry.get('sensor', 'unknown'),
                source_ip=entry.get('src_ip', '0.0.0.0'),
                source_port=entry.get('src_port', 0),
                commands=[entry.get('input', '')],
                session_id=entry.get('session', 'unknown'),
                severity=self._classify_command_severity(entry.get('input', '')),
                attack_type='command_execution'
            )
        
        elif event_id == 'cowrie.session.connect':
            return AttackEvent(
                timestamp=datetime.fromisoformat(entry['timestamp']),
                honeypot_id=entry.get('sensor', 'unknown'),
                source_ip=entry.get('src_ip', '0.0.0.0'),
                source_port=entry.get('src_port', 0),
                commands=[],
                session_id=entry.get('session', 'unknown'),
                severity=AttackSeverity.INFO,
                attack_type='connection'
            )
        
        return None
    
    def _classify_command_severity(self, command: str) -> AttackSeverity:
        dangerous_patterns = [
            r'rm\s+-rf',
            r'wget|curl.*http',
            r'nc\s+.*\s+-e',
            r'bash\s+-i',
            r'/bin/sh',
            r'chmod\s+\+x',
            r'python.*-c',
            r'perl.*-e'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return AttackSeverity.HIGH
        
        if any(cmd in command.lower() for cmd in ['cat', 'ls', 'pwd', 'whoami']):
            return AttackSeverity.LOW
        
        return AttackSeverity.MEDIUM
    
    def aggregate_events(self, events: List[AttackEvent]) -> Dict:
        if not events:
            return {}
        
        # Group by source IP
        by_ip = {}
        for event in events:
            if event.source_ip not in by_ip:
                by_ip[event.source_ip] = []
            by_ip[event.source_ip].append(event)
        
        # Calculate statistics
        stats = {
            'total_events': len(events),
            'unique_ips': len(by_ip),
            'attack_types': {},
            'severity_distribution': {},
            'top_attackers': [],
            'common_commands': {},
            'time_range': {
                'start': min(e.timestamp for e in events).isoformat(),
                'end': max(e.timestamp for e in events).isoformat()
            }
        }
        
        # Attack types
        for event in events:
            if event.attack_type:
                stats['attack_types'][event.attack_type] = \
                    stats['attack_types'].get(event.attack_type, 0) + 1
        
        # Severity distribution
        for event in events:
            stats['severity_distribution'][event.severity] = \
                stats['severity_distribution'].get(event.severity, 0) + 1
        
        # Top attackers
        stats['top_attackers'] = sorted(
            [{'ip': ip, 'count': len(events)} for ip, events in by_ip.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:10]
        
        # Common commands
        for event in events:
            for cmd in event.commands:
                stats['common_commands'][cmd] = \
                    stats['common_commands'].get(cmd, 0) + 1
        
        return stats
    
    def watch_logs(self, honeypot_id: str) -> List[AttackEvent]:
        """Watch and parse logs for a specific honeypot"""
        log_file = self.log_dir / honeypot_id / "cowrie.json"
        return self.parse_cowrie_log(log_file)
