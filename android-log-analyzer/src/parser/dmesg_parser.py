"""Linux dmesg/kernel log parser."""

import re
from datetime import datetime, timedelta
from typing import Optional
import logging

from .base_parser import BaseParser
from ..models import LogEntry, LogLevel

logger = logging.getLogger(__name__)


class DmesgParser(BaseParser):
    """
    Parser for kernel dmesg/kmsg logs.
    
    Supports formats:
    - [timestamp] message
    - <level>[timestamp] subsystem: message
    """
    
    # Standard dmesg format: [timestamp] message
    DMESG_PATTERN = re.compile(
        r'^\[\s*(\d+\.\d+)\]\s*(.*)$'
    )
    
    # Dmesg with level: <level>[timestamp] message
    DMESG_LEVEL_PATTERN = re.compile(
        r'^<(\d)>\[\s*(\d+\.\d+)\]\s*(.*)$'
    )
    
    # Subsystem pattern to extract tag from message
    SUBSYSTEM_PATTERN = re.compile(
        r'^([a-zA-Z0-9_-]+):\s*(.*)$'
    )
    
    # Kernel log levels to Android levels
    KERNEL_LEVEL_MAP = {
        0: LogLevel.FATAL,    # KERN_EMERG
        1: LogLevel.FATAL,    # KERN_ALERT
        2: LogLevel.FATAL,    # KERN_CRIT
        3: LogLevel.ERROR,    # KERN_ERR
        4: LogLevel.WARNING,  # KERN_WARNING
        5: LogLevel.INFO,     # KERN_NOTICE
        6: LogLevel.INFO,     # KERN_INFO
        7: LogLevel.DEBUG,    # KERN_DEBUG
    }
    
    def __init__(self, year: int = 2026, boot_time: Optional[datetime] = None):
        """
        Initialize dmesg parser.
        
        Args:
            year: Default year
            boot_time: System boot time for absolute timestamps
        """
        super().__init__(year)
        self.boot_time = boot_time or datetime.now()
    
    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a single dmesg line.
        
        Args:
            line: Raw dmesg line
            
        Returns:
            LogEntry if parsing successful, None otherwise
        """
        line = line.rstrip('\n\r')
        
        if not line:
            return None
        
        # Try format with level first
        entry = self._parse_with_level(line)
        if entry:
            return entry
        
        # Try standard format
        entry = self._parse_standard(line)
        if entry:
            return entry
        
        return None
    
    def _parse_with_level(self, line: str) -> Optional[LogEntry]:
        """Parse dmesg with level indicator."""
        match = self.DMESG_LEVEL_PATTERN.match(line)
        if not match:
            return None
        
        level_num, timestamp_str, message = match.groups()
        
        # Calculate absolute timestamp from boot-relative time
        uptime_seconds = float(timestamp_str)
        timestamp = self.boot_time + timedelta(seconds=uptime_seconds)
        
        # Map kernel level to Android level
        level = self.KERNEL_LEVEL_MAP.get(int(level_num), LogLevel.INFO)
        
        # Try to extract subsystem as tag
        tag, clean_message = self._extract_subsystem(message)
        
        return LogEntry(
            timestamp=timestamp,
            pid=0,  # Kernel logs don't have PID
            tid=0,
            level=level,
            tag=tag,
            message=clean_message,
            raw_line=line,
            metadata={'kernel_level': int(level_num), 'uptime': uptime_seconds}
        )
    
    def _parse_standard(self, line: str) -> Optional[LogEntry]:
        """Parse standard dmesg format."""
        match = self.DMESG_PATTERN.match(line)
        if not match:
            return None
        
        timestamp_str, message = match.groups()
        
        uptime_seconds = float(timestamp_str)
        timestamp = self.boot_time + timedelta(seconds=uptime_seconds)
        
        # Try to extract subsystem as tag
        tag, clean_message = self._extract_subsystem(message)
        
        # Infer level from message content
        level = self._infer_level(clean_message)
        
        return LogEntry(
            timestamp=timestamp,
            pid=0,
            tid=0,
            level=level,
            tag=tag,
            message=clean_message,
            raw_line=line,
            metadata={'uptime': uptime_seconds}
        )
    
    def _extract_subsystem(self, message: str) -> tuple:
        """Extract subsystem name as tag from message."""
        match = self.SUBSYSTEM_PATTERN.match(message)
        if match:
            return match.group(1), match.group(2)
        return "kernel", message
    
    def _infer_level(self, message: str) -> LogLevel:
        """Infer log level from message content."""
        message_lower = message.lower()
        
        if any(kw in message_lower for kw in ['error', 'fail', 'unable']):
            return LogLevel.ERROR
        if any(kw in message_lower for kw in ['warn', 'warning']):
            return LogLevel.WARNING
        if any(kw in message_lower for kw in ['panic', 'oops', 'bug']):
            return LogLevel.FATAL
        
        return LogLevel.INFO
