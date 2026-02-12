"""Log entry data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class LogLevel(Enum):
    """Android log levels."""
    VERBOSE = 'V'
    DEBUG = 'D'
    INFO = 'I'
    WARNING = 'W'
    ERROR = 'E'
    FATAL = 'F'
    
    @classmethod
    def from_char(cls, char: str) -> 'LogLevel':
        """Convert single character to LogLevel."""
        for level in cls:
            if level.value == char.upper():
                return level
        return cls.DEBUG  # Default fallback
    
    def is_error_or_higher(self) -> bool:
        """Check if this level is ERROR or FATAL."""
        return self in (LogLevel.ERROR, LogLevel.FATAL)
    
    def is_warning_or_higher(self) -> bool:
        """Check if this level is WARNING or higher."""
        return self in (LogLevel.WARNING, LogLevel.ERROR, LogLevel.FATAL)


@dataclass
class LogEntry:
    """Represents a single log entry from Android logcat."""
    
    timestamp: datetime
    pid: int
    tid: int
    level: LogLevel
    tag: str
    message: str
    raw_line: str = ""
    
    # Optional metadata for enriched entries
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize fields after initialization."""
        if isinstance(self.level, str):
            self.level = LogLevel.from_char(self.level)
        self.tag = self.tag.strip() if self.tag else ""
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error-level log."""
        return self.level.is_error_or_higher()
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning-level log."""
        return self.level == LogLevel.WARNING
    
    @property
    def timestamp_str(self) -> str:
        """Get formatted timestamp string."""
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def matches_tag(self, *tags: str) -> bool:
        """Check if log entry matches any of the given tags."""
        return self.tag in tags
    
    def contains(self, *keywords: str, case_sensitive: bool = False) -> bool:
        """Check if message contains any of the keywords."""
        message = self.message if case_sensitive else self.message.lower()
        return any(
            (kw if case_sensitive else kw.lower()) in message 
            for kw in keywords
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp_str,
            'pid': self.pid,
            'tid': self.tid,
            'level': self.level.value,
            'tag': self.tag,
            'message': self.message,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """String representation matching logcat format."""
        return f"{self.timestamp_str} {self.pid:5d} {self.tid:5d} {self.level.value} {self.tag}: {self.message}"
