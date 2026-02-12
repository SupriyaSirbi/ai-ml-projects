"""Tests for the log analyzer."""

import unittest
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import LogcatParser
from src.analysis import LogStatistics, AutomotiveAnalyzer, PatternAnalyzer
from src.models import LogEntry, LogLevel, AnalysisResult, Severity


class TestLogcatParser(unittest.TestCase):
    """Test cases for logcat parser."""
    
    def setUp(self):
        self.parser = LogcatParser(year=2026)
    
    def test_parse_threadtime_format(self):
        """Test parsing threadtime format."""
        line = "01-15 08:00:00.123  1234  5678 I TestTag: Test message"
        entry = self.parser.parse_line(line)
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.pid, 1234)
        self.assertEqual(entry.tid, 5678)
        self.assertEqual(entry.level, LogLevel.INFO)
        self.assertEqual(entry.tag, "TestTag")
        self.assertEqual(entry.message, "Test message")
    
    def test_parse_error_level(self):
        """Test parsing error level logs."""
        line = "01-15 08:00:00.123  1234  5678 E ErrorTag: Error occurred"
        entry = self.parser.parse_line(line)
        
        self.assertIsNotNone(entry)
        self.assertEqual(entry.level, LogLevel.ERROR)
        self.assertTrue(entry.is_error)
    
    def test_parse_invalid_line(self):
        """Test handling invalid log lines."""
        line = "This is not a valid log line"
        entry = self.parser.parse_line(line)
        
        self.assertIsNone(entry)
    
    def test_parse_empty_line(self):
        """Test handling empty lines."""
        entry = self.parser.parse_line("")
        self.assertIsNone(entry)


class TestLogStatistics(unittest.TestCase):
    """Test cases for statistics generation."""
    
    def setUp(self):
        self.entries = [
            LogEntry(
                timestamp=datetime(2026, 1, 15, 8, 0, 0),
                pid=1000, tid=1000,
                level=LogLevel.INFO,
                tag="TestTag",
                message="Info message"
            ),
            LogEntry(
                timestamp=datetime(2026, 1, 15, 8, 0, 1),
                pid=1000, tid=1000,
                level=LogLevel.ERROR,
                tag="ErrorTag",
                message="Error message"
            ),
            LogEntry(
                timestamp=datetime(2026, 1, 15, 8, 0, 2),
                pid=2000, tid=2000,
                level=LogLevel.WARNING,
                tag="WarnTag",
                message="Warning message"
            ),
        ]
    
    def test_generate_summary(self):
        """Test summary generation."""
        stats = LogStatistics(self.entries).generate_summary()
        
        self.assertEqual(stats['total_entries'], 3)
        self.assertEqual(stats['error_count'], 1)
        self.assertEqual(stats['warning_count'], 1)
        self.assertEqual(stats['info_count'], 1)
        self.assertEqual(stats['unique_pids'], 2)
    
    def test_empty_entries(self):
        """Test handling empty entry list."""
        stats = LogStatistics([]).generate_summary()
        
        self.assertEqual(stats['total_entries'], 0)


class TestPatternAnalyzer(unittest.TestCase):
    """Test cases for pattern analysis."""
    
    def test_detect_anr(self):
        """Test ANR detection."""
        entries = [
            LogEntry(
                timestamp=datetime(2026, 1, 15, 8, 0, 0),
                pid=1000, tid=1000,
                level=LogLevel.ERROR,
                tag="ActivityManager",
                message="ANR in com.example.app"
            )
        ]
        
        analyzer = PatternAnalyzer()
        results = analyzer.analyze(entries)
        
        self.assertTrue(any(r.category == 'anr_detected' for r in results))
    
    def test_detect_native_crash(self):
        """Test native crash detection."""
        entries = [
            LogEntry(
                timestamp=datetime(2026, 1, 15, 8, 0, 0),
                pid=1000, tid=1000,
                level=LogLevel.FATAL,
                tag="DEBUG",
                message="SIGSEGV in native code"
            )
        ]
        
        analyzer = PatternAnalyzer()
        results = analyzer.analyze(entries)
        
        self.assertTrue(any(r.category == 'native_crash' for r in results))


class TestAutomotiveAnalyzer(unittest.TestCase):
    """Test cases for automotive-specific analysis."""
    
    def test_detect_vehicle_hal_error(self):
        """Test Vehicle HAL error detection."""
        entries = [
            LogEntry(
                timestamp=datetime(2026, 1, 15, 8, 0, 0),
                pid=2000, tid=2001,
                level=LogLevel.ERROR,
                tag="VehicleHal",
                message="VehicleHal error reading property"
            )
        ]
        
        analyzer = AutomotiveAnalyzer()
        results = analyzer.analyze(entries)
        
        self.assertTrue(any('vehicle_hal' in r.category for r in results))
    
    def test_detect_can_bus_error(self):
        """Test CAN bus error detection."""
        entries = [
            LogEntry(
                timestamp=datetime(2026, 1, 15, 8, 0, 0),
                pid=2000, tid=2010,
                level=LogLevel.ERROR,
                tag="CanBusService",
                message="CAN bus busoff state detected"
            )
        ]
        
        analyzer = AutomotiveAnalyzer()
        results = analyzer.analyze(entries)
        
        self.assertTrue(any('can_bus' in r.category for r in results))
    
    def test_automotive_summary(self):
        """Test automotive summary generation."""
        entries = [
            LogEntry(
                timestamp=datetime(2026, 1, 15, 8, 0, 0),
                pid=2000, tid=2000,
                level=LogLevel.INFO,
                tag="CarService",
                message="CarService started"
            ),
            LogEntry(
                timestamp=datetime(2026, 1, 15, 8, 0, 1),
                pid=2000, tid=2001,
                level=LogLevel.ERROR,
                tag="VehicleHal",
                message="Vehicle property error"
            )
        ]
        
        analyzer = AutomotiveAnalyzer()
        summary = analyzer.get_automotive_summary(entries)
        
        self.assertIn('subsystem_activity', summary)
        self.assertIn('vehicle', summary['subsystem_activity'])


if __name__ == '__main__':
    unittest.main()
