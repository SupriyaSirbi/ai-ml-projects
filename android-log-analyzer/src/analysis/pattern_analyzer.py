"""Pattern-based log analyzer."""

import re
from typing import List, Dict, Optional, Pattern
from dataclasses import dataclass
import logging

from ..models import LogEntry, AnalysisResult, Severity

logger = logging.getLogger(__name__)


@dataclass
class PatternRule:
    """Definition of a pattern to detect in logs."""
    name: str
    regex: str
    tags: List[str]
    severity: Severity
    description: str
    recommendation: str
    compiled_pattern: Optional[Pattern] = None
    
    def __post_init__(self):
        """Compile the regex pattern."""
        self.compiled_pattern = re.compile(self.regex, re.IGNORECASE)
    
    def matches(self, entry: LogEntry) -> bool:
        """Check if this rule matches a log entry."""
        # Check tag match
        if self.tags and entry.tag not in self.tags:
            tag_match = False
        else:
            tag_match = True
        
        # Check pattern match in message
        pattern_match = bool(self.compiled_pattern.search(entry.message))
        
        return pattern_match or (tag_match and self.tags)


class PatternAnalyzer:
    """Analyzer that detects patterns in log entries."""
    
    # Built-in patterns for common Android issues
    DEFAULT_PATTERNS = [
        PatternRule(
            name='anr_detected',
            regex=r'ANR in|Application Not Responding|Input dispatching timed out',
            tags=['ActivityManager', 'system_server', 'InputDispatcher'],
            severity=Severity.ERROR,
            description='Application Not Responding detected',
            recommendation='Analyze ANR traces in /data/anr/ for blocked threads'
        ),
        PatternRule(
            name='native_crash',
            regex=r'FATAL EXCEPTION|native crash|SIGSEGV|SIGABRT|SIGBUS|SIGFPE',
            tags=['DEBUG', 'crash_dump', 'tombstoned', 'libc'],
            severity=Severity.CRITICAL,
            description='Native crash or fatal exception detected',
            recommendation='Collect tombstone from /data/tombstones/ for analysis'
        ),
        PatternRule(
            name='java_exception',
            regex=r'java\.\w+Exception|android\.\w+Exception|kotlin\.\w+Exception',
            tags=[],
            severity=Severity.ERROR,
            description='Java/Kotlin exception detected',
            recommendation='Review stack trace for exception cause'
        ),
        PatternRule(
            name='out_of_memory',
            regex=r'OutOfMemoryError|Low on memory|lowmemorykiller|OOM',
            tags=['ActivityManager', 'art', 'dalvikvm', 'lowmemorykiller'],
            severity=Severity.CRITICAL,
            description='Memory exhaustion detected',
            recommendation='Analyze memory usage with dumpsys meminfo'
        ),
        PatternRule(
            name='watchdog_timeout',
            regex=r'Watchdog.*timeout|WATCHDOG KILLING SYSTEM PROCESS',
            tags=['Watchdog', 'system_server'],
            severity=Severity.CRITICAL,
            description='System watchdog timeout',
            recommendation='Check for blocked system services'
        ),
        PatternRule(
            name='service_died',
            regex=r'Service.*died|Binder.*died|Process.*died',
            tags=['ActivityManager', 'ServiceManager'],
            severity=Severity.ERROR,
            description='Service or process died unexpectedly',
            recommendation='Review process death reason and restart behavior'
        ),
        PatternRule(
            name='permission_denied',
            regex=r'Permission denied|SecurityException|PERMISSION_DENIED',
            tags=['SELinux', 'PackageManager'],
            severity=Severity.WARNING,
            description='Permission or security violation',
            recommendation='Check SELinux policies and app permissions'
        ),
        PatternRule(
            name='battery_drain',
            regex=r'excessive wake|wakelock.*held|battery drain|Excessive.*alarm',
            tags=['PowerManagerService', 'BatteryStats', 'AlarmManager'],
            severity=Severity.WARNING,
            description='Potential battery drain issue',
            recommendation='Use Battery Historian for detailed analysis'
        ),
    ]
    
    def __init__(self, custom_patterns: Optional[List[PatternRule]] = None):
        """
        Initialize pattern analyzer.
        
        Args:
            custom_patterns: Additional patterns to use
        """
        self.patterns = list(self.DEFAULT_PATTERNS)
        if custom_patterns:
            self.patterns.extend(custom_patterns)
    
    def add_pattern(self, pattern: PatternRule) -> None:
        """Add a pattern rule."""
        self.patterns.append(pattern)
    
    def analyze(self, entries: List[LogEntry]) -> List[AnalysisResult]:
        """
        Analyze log entries for pattern matches.
        
        Args:
            entries: List of log entries
            
        Returns:
            List of analysis results
        """
        results: Dict[str, AnalysisResult] = {}
        
        for entry in entries:
            for pattern in self.patterns:
                if pattern.compiled_pattern.search(entry.message):
                    self._record_match(results, pattern, entry)
        
        # Sort by severity and occurrence count
        return sorted(results.values())
    
    def _record_match(self, results: Dict[str, AnalysisResult], 
                      pattern: PatternRule, entry: LogEntry) -> None:
        """Record a pattern match in results."""
        if pattern.name not in results:
            results[pattern.name] = AnalysisResult(
                category=pattern.name,
                severity=pattern.severity,
                description=pattern.description,
                recommendation=pattern.recommendation,
                occurrences=0,
                affected_tags=[],
                affected_pids=[]
            )
        
        result = results[pattern.name]
        result.occurrences += 1
        
        # Update first/last seen
        timestamp_str = entry.timestamp_str
        if result.first_seen is None or timestamp_str < result.first_seen:
            result.first_seen = timestamp_str
        if result.last_seen is None or timestamp_str > result.last_seen:
            result.last_seen = timestamp_str
        
        # Track affected tags and PIDs
        if entry.tag not in result.affected_tags:
            result.affected_tags.append(entry.tag)
        if entry.pid not in result.affected_pids:
            result.affected_pids.append(entry.pid)
        
        # Store sample messages
        result.add_sample(entry.message)
    
    def find_pattern(self, entries: List[LogEntry], 
                    regex: str, name: str = "custom") -> List[LogEntry]:
        """
        Find entries matching a custom regex pattern.
        
        Args:
            entries: Log entries to search
            regex: Regex pattern to match
            name: Name for the pattern
            
        Returns:
            List of matching entries
        """
        pattern = re.compile(regex, re.IGNORECASE)
        return [e for e in entries if pattern.search(e.message)]
