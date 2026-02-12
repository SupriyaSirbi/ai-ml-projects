"""Base parser interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Iterator, Union
import logging

from ..models import LogEntry

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Abstract base class for log parsers."""
    
    def __init__(self, year: int = 2026):
        """
        Initialize parser.
        
        Args:
            year: Default year for timestamps (Android logs don't include year)
        """
        self.year = year
        self._parse_errors = 0
        self._total_lines = 0
    
    @abstractmethod
    def parse_line(self, line: str) -> Optional[LogEntry]:
        """
        Parse a single log line.
        
        Args:
            line: Raw log line
            
        Returns:
            LogEntry if parsing successful, None otherwise
        """
        pass
    
    def parse_file(self, filepath: Union[str, Path]) -> List[LogEntry]:
        """
        Parse an entire log file.
        
        Args:
            filepath: Path to the log file
            
        Returns:
            List of parsed LogEntry objects
        """
        filepath = Path(filepath)
        entries = []
        
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return entries
        
        logger.info(f"Parsing file: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    self._total_lines += 1
                    entry = self.parse_line(line)
                    if entry:
                        entries.append(entry)
                    else:
                        self._parse_errors += 1
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
        
        logger.info(f"Parsed {len(entries)} entries from {self._total_lines} lines")
        return entries
    
    def parse_stream(self, lines: Iterator[str]) -> Iterator[LogEntry]:
        """
        Parse a stream of log lines (generator).
        
        Args:
            lines: Iterator of log lines
            
        Yields:
            LogEntry objects
        """
        for line in lines:
            self._total_lines += 1
            entry = self.parse_line(line)
            if entry:
                yield entry
            else:
                self._parse_errors += 1
    
    def parse_directory(self, dirpath: Union[str, Path], 
                       pattern: str = "*.log") -> List[LogEntry]:
        """
        Parse all log files in a directory.
        
        Args:
            dirpath: Path to directory
            pattern: Glob pattern for log files
            
        Returns:
            Combined list of LogEntry objects, sorted by timestamp
        """
        dirpath = Path(dirpath)
        all_entries = []
        
        if not dirpath.is_dir():
            logger.error(f"Directory not found: {dirpath}")
            return all_entries
        
        log_files = list(dirpath.glob(pattern))
        logger.info(f"Found {len(log_files)} log files in {dirpath}")
        
        for log_file in log_files:
            entries = self.parse_file(log_file)
            all_entries.extend(entries)
        
        # Sort by timestamp
        all_entries.sort(key=lambda e: e.timestamp)
        
        return all_entries
    
    @property
    def error_rate(self) -> float:
        """Get the parse error rate."""
        if self._total_lines == 0:
            return 0.0
        return self._parse_errors / self._total_lines
    
    def reset_stats(self) -> None:
        """Reset parsing statistics."""
        self._parse_errors = 0
        self._total_lines = 0
