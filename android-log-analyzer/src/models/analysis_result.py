"""Analysis result data model."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class Severity(Enum):
    """Severity levels for analysis results."""
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    
    def __lt__(self, other: 'Severity') -> bool:
        return self.value < other.value
    
    def __le__(self, other: 'Severity') -> bool:
        return self.value <= other.value
    
    @property
    def color(self) -> str:
        """Get color code for this severity."""
        colors = {
            Severity.INFO: '#17a2b8',
            Severity.WARNING: '#ffc107',
            Severity.ERROR: '#fd7e14',
            Severity.CRITICAL: '#dc3545'
        }
        return colors.get(self, '#6c757d')
    
    @property
    def css_class(self) -> str:
        """Get CSS class name for this severity."""
        return f"severity-{self.name.lower()}"


@dataclass
class AnalysisResult:
    """Represents a detected issue or pattern from log analysis."""
    
    category: str
    severity: Severity
    description: str
    occurrences: int = 0
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    affected_tags: List[str] = field(default_factory=list)
    affected_pids: List[int] = field(default_factory=list)
    recommendation: str = ""
    sample_messages: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def title(self) -> str:
        """Get human-readable title."""
        return self.category.replace('_', ' ').title()
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical issue."""
        return self.severity == Severity.CRITICAL
    
    @property
    def is_error_or_higher(self) -> bool:
        """Check if this is an error or critical issue."""
        return self.severity >= Severity.ERROR
    
    def add_sample(self, message: str, max_samples: int = 5) -> None:
        """Add a sample message if under the limit."""
        if len(self.sample_messages) < max_samples:
            self.sample_messages.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'category': self.category,
            'title': self.title,
            'severity': self.severity.name,
            'severity_value': self.severity.value,
            'description': self.description,
            'occurrences': self.occurrences,
            'first_seen': self.first_seen,
            'last_seen': self.last_seen,
            'affected_tags': self.affected_tags,
            'affected_pids': self.affected_pids,
            'recommendation': self.recommendation,
            'sample_messages': self.sample_messages,
            'metadata': self.metadata
        }
    
    def __lt__(self, other: 'AnalysisResult') -> bool:
        """Compare by severity (higher severity first) then by occurrences."""
        if self.severity != other.severity:
            return self.severity > other.severity  # Higher severity first
        return self.occurrences > other.occurrences
