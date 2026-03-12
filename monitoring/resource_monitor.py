import psutil
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class ResourceMonitor:
    def __init__(self, cpu_threshold: float = 80.0, memory_threshold: float = 80.0):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
    
    def get_system_stats(self) -> Dict:
        """Get current system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': {
                'percent': cpu_percent,
                'count': psutil.cpu_count(),
                'threshold_exceeded': cpu_percent > self.cpu_threshold
            },
            'memory': {
                'total_mb': memory.total / (1024 * 1024),
                'used_mb': memory.used / (1024 * 1024),
                'percent': memory.percent,
                'threshold_exceeded': memory.percent > self.memory_threshold
            },
            'disk': {
                'total_gb': disk.total / (1024 * 1024 * 1024),
                'used_gb': disk.used / (1024 * 1024 * 1024),
                'percent': disk.percent
            }
        }
    
    def check_thresholds(self) -> Dict[str, bool]:
        """Check if resource thresholds are exceeded"""
        stats = self.get_system_stats()
        
        return {
            'cpu_exceeded': stats['cpu']['threshold_exceeded'],
            'memory_exceeded': stats['memory']['threshold_exceeded'],
            'action_required': stats['cpu']['threshold_exceeded'] or stats['memory']['threshold_exceeded']
        }
