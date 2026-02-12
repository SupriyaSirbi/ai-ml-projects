"""Android logcat log parser."""

import re
from datetime import datetime
from typing import Optional
import logging

from .base_parser import BaseParser
from ..models import LogEntry, LogLevel

logger = logging.getLogger(__name__)


class LogcatParser(BaseParser):
    """
    Parser for Android logcat output.
    
    Supports multiple logcat formats:
    - threadtime: MM-DD HH:MM:SS.mmm PID TID LEVEL TAG: MESSAGE
    - brief: LEVEL/TAG(PID): MESSAGE
    - time: MM-DD HH:MM:SS.mmm LEVEL/TAG(PID): MESSAGE
    """
    
    # Threadtime format (most common): MM-DD HH:MM:SS.mmm PID TID LEVEL TAG: MESSAGE
    THREADTIME_PATTERN = re.compile(
        r'^(\d{2}-\d{2})\s+'           # Date: MM-DD
        r'(\d{2}:\d{2}:\d{2}\.\d{3})\s+'  # Time: HH:MM:SS.mmm
        r'(\d+)\s+'                     # PID
        r'(\d+)\s+'                     # TID
        r'([VDIWEF])\s+'               # Level
        r'([^:]+):\s*'                 # Tag
        r'(.*)$'                        # Message
    )
    
    # Brief format: LEVEL/TAG(PID): MESSAGE
    BRIEF_PATTERN = re.compile(
        r'^([VDIWEF])/([^(]+)\(\s*(\d+)\):\s*(.*)$'
    )
    
    # Time format: MM-DD HH:MM:SS.mmm LEVEL/TAG(PID): MESSAGE
    TIME_PATTERN = re.compile(
        r'^(\d{2}-\d{2})\s+'
        r'(\d{2}:\d{2}:\d{2}\.\d{3})\s+'
        r'([VDIWEF])/([^(]+)\(\s*(\d+)\):\s*(.*)$'
    )
    
    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a single logcat line.
        
        Args:
            line: Raw logcat line
            
        Returns:
            LogEntry if parsing successful, None otherwise
        """
        line = line.rstrip('\n\r')
        
        if not line:
            return None
        
        # Try threadtime format first (most common)
        entry = self._parse_threadtime(line)
        if entry:
            return entry
        
        # Try time format
        entry = self._parse_time_format(line)
        if entry:
            return entry
        
        # Try brief format
        entry = self._parse_brief(line)
        if entry:
            return entry
        
        return None
    
    def _parse_threadtime(self, line: str) -> Optional[LogEntry]:
        """Parse threadtime format."""
        match = self.THREADTIME_PATTERN.match(line)
        if not match:
            return None
        
        date_str, time_str, pid, tid, level, tag, message = match.groups()
        
        try:
            timestamp = datetime.strptime(
                f"{self.year}-{date_str} {time_str}",
                "%Y-%m-%d %H:%M:%S.%f"
            )
        except ValueError:
            return None
        
        return LogEntry(
            timestamp=timestamp,
            pid=int(pid),
            tid=int(tid),
            level=LogLevel.from_char(level),
            tag=tag.strip(),
            message=message,
            raw_line=line
        )
    
    def _parse_time_format(self, line: str) -> Optional[LogEntry]:
        """Parse time format."""
        match = self.TIME_PATTERN.match(line)
        if not match:
            return None
        
        date_str, time_str, level, tag, pid, message = match.groups()
        
        try:
            timestamp = datetime.strptime(
                f"{self.year}-{date_str} {time_str}",
                "%Y-%m-%d %H:%M:%S.%f"
            )
        except ValueError:
            return None
        
        return LogEntry(
            timestamp=timestamp,
            pid=int(pid),
            tid=int(pid),  # TID not available in this format
            level=LogLevel.from_char(level),
            tag=tag.strip(),
            message=message,
            raw_line=line
        )
    
    def _parse_brief(self, line: str) -> Optional[LogEntry]:
        """Parse brief format."""
        match = self.BRIEF_PATTERN.match(line)
        if not match:
            return None
        
        level, tag, pid, message = match.groups()
        
        return LogEntry(
            timestamp=datetime.now(),  # No timestamp in brief format
            pid=int(pid),
            tid=int(pid),  # TID not available
            level=LogLevel.from_char(level),
            tag=tag.strip(),
            message=message,
            raw_line=line
        )
