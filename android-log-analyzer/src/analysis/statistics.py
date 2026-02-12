"""Statistics generation for log analysis."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from ..models import LogEntry, LogLevel

logger = logging.getLogger(__name__)


class LogStatistics:
    """Generate statistics from log entries."""
    
    def __init__(self, entries: List[LogEntry]):
        """
        Initialize statistics generator.
        
        Args:
            entries: List of log entries to analyze
        """
        self.entries = entries
        self._cache: Dict[str, Any] = {}
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics.
        
        Returns:
            Dictionary containing all statistics
        """
        if not self.entries:
            return self._empty_summary()
        
        level_counts = Counter(e.level.value for e in self.entries)
        tag_counts = Counter(e.tag for e in self.entries)
        pid_counts = Counter(e.pid for e in self.entries)
        
        time_range = self.entries[-1].timestamp - self.entries[0].timestamp
        total_seconds = max(time_range.total_seconds(), 1)
        
        # Calculate rates
        error_entries = [e for e in self.entries if e.level.is_error_or_higher()]
        warning_entries = [e for e in self.entries if e.level == LogLevel.WARNING]
        
        return {
            'total_entries': len(self.entries),
            'time_range': str(time_range),
            'time_range_seconds': total_seconds,
            'start_time': self.entries[0].timestamp_str,
            'end_time': self.entries[-1].timestamp_str,
            
            # Level distribution
            'level_distribution': dict(level_counts),
            'verbose_count': level_counts.get('V', 0),
            'debug_count': level_counts.get('D', 0),
            'info_count': level_counts.get('I', 0),
            'warning_count': level_counts.get('W', 0),
            'error_count': level_counts.get('E', 0),
            'fatal_count': level_counts.get('F', 0),
            
            # Rates
            'logs_per_second': round(len(self.entries) / total_seconds, 2),
            'errors_per_minute': round(len(error_entries) / (total_seconds / 60), 2),
            'warnings_per_minute': round(len(warning_entries) / (total_seconds / 60), 2),
            
            # Tags and processes
            'top_tags': dict(tag_counts.most_common(20)),
            'top_error_tags': dict(self._get_top_tags_by_level(LogLevel.ERROR, 10)),
            'unique_tags': len(set(e.tag for e in self.entries)),
            'unique_pids': len(set(e.pid for e in self.entries)),
            'top_pids': dict(pid_counts.most_common(10)),
        }
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary when no entries."""
        return {
            'total_entries': 0,
            'time_range': '0:00:00',
            'level_distribution': {},
            'error_count': 0,
            'warning_count': 0,
            'fatal_count': 0
        }
    
    def _get_top_tags_by_level(self, level: LogLevel, limit: int = 10) -> List[tuple]:
        """Get top tags for a specific log level."""
        tag_counts = Counter(
            e.tag for e in self.entries if e.level == level
        )
        return tag_counts.most_common(limit)
    
    def get_timeline_data(self, bucket_minutes: int = 5) -> Dict[str, Dict]:
        """
        Group logs by time buckets for timeline visualization.
        
        Args:
            bucket_minutes: Size of each time bucket in minutes
            
        Returns:
            Dictionary with timestamp keys and count values
        """
        if not self.entries:
            return {}
        
        buckets = defaultdict(lambda: {
            'total': 0, 
            'errors': 0, 
            'warnings': 0,
            'debug': 0,
            'info': 0
        })
        
        for entry in self.entries:
            # Round down to bucket boundary
            bucket_time = entry.timestamp.replace(
                minute=(entry.timestamp.minute // bucket_minutes) * bucket_minutes,
                second=0,
                microsecond=0
            )
            bucket_key = bucket_time.strftime("%Y-%m-%d %H:%M")
            
            buckets[bucket_key]['total'] += 1
            
            if entry.level == LogLevel.ERROR or entry.level == LogLevel.FATAL:
                buckets[bucket_key]['errors'] += 1
            elif entry.level == LogLevel.WARNING:
                buckets[bucket_key]['warnings'] += 1
            elif entry.level == LogLevel.DEBUG:
                buckets[bucket_key]['debug'] += 1
            elif entry.level == LogLevel.INFO:
                buckets[bucket_key]['info'] += 1
        
        return dict(sorted(buckets.items()))
    
    def get_error_clusters(self, time_window_seconds: int = 60) -> List[Dict]:
        """
        Find clusters of errors within time windows.
        
        Args:
            time_window_seconds: Time window for clustering
            
        Returns:
            List of error clusters with their details
        """
        error_entries = [e for e in self.entries if e.level.is_error_or_higher()]
        
        if not error_entries:
            return []
        
        clusters = []
        current_cluster = [error_entries[0]]
        
        for entry in error_entries[1:]:
            time_diff = (entry.timestamp - current_cluster[-1].timestamp).total_seconds()
            
            if time_diff <= time_window_seconds:
                current_cluster.append(entry)
            else:
                if len(current_cluster) >= 3:  # Only report significant clusters
                    clusters.append(self._summarize_cluster(current_cluster))
                current_cluster = [entry]
        
        # Don't forget the last cluster
        if len(current_cluster) >= 3:
            clusters.append(self._summarize_cluster(current_cluster))
        
        return clusters
    
    def _summarize_cluster(self, entries: List[LogEntry]) -> Dict:
        """Summarize an error cluster."""
        return {
            'start_time': entries[0].timestamp_str,
            'end_time': entries[-1].timestamp_str,
            'count': len(entries),
            'duration_seconds': (entries[-1].timestamp - entries[0].timestamp).total_seconds(),
            'tags': list(set(e.tag for e in entries)),
            'sample_messages': [e.message for e in entries[:3]]
        }
    
    def get_tag_activity(self, tag: str) -> Dict[str, Any]:
        """
        Get detailed activity for a specific tag.
        
        Args:
            tag: Tag name to analyze
            
        Returns:
            Activity details for the tag
        """
        tag_entries = [e for e in self.entries if e.tag == tag]
        
        if not tag_entries:
            return {'tag': tag, 'count': 0}
        
        level_counts = Counter(e.level.value for e in tag_entries)
        
        return {
            'tag': tag,
            'count': len(tag_entries),
            'first_seen': tag_entries[0].timestamp_str,
            'last_seen': tag_entries[-1].timestamp_str,
            'level_distribution': dict(level_counts),
            'unique_pids': len(set(e.pid for e in tag_entries)),
            'sample_messages': [e.message for e in tag_entries[:5]]
        }
