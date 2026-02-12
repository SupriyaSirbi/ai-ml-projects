#!/usr/bin/env python3
"""
Android Automotive Log Analyzer
Main entry point for the log analysis tool.

Usage:
    python -m src.main <log_path> [options]
    
Examples:
    python -m src.main /path/to/logcat.log
    python -m src.main /path/to/logs/ -o report.html --format html
    python -m src.main device_logs.log --json-summary summary.json
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

from .parser import LogcatParser, DmesgParser
from .analysis import LogStatistics, AutomotiveAnalyzer
from .report import HTMLReportGenerator, JSONReportGenerator


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description='Android Automotive Log Analyzer - Parse and analyze vehicle system logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s logcat.log                      Analyze single log file
  %(prog)s /data/logs/ -o report.html      Analyze directory of logs
  %(prog)s device.log --format json        Generate JSON report
  %(prog)s logs/ --json-summary ci.json    Generate CI-friendly summary
        '''
    )
    
    # Positional arguments
    parser.add_argument(
        'log_path',
        help='Path to log file or directory containing log files'
    )
    
    # Output options
    parser.add_argument(
        '-o', '--output',
        default='analysis_report.html',
        help='Output report file path (default: analysis_report.html)'
    )
    parser.add_argument(
        '--format',
        choices=['html', 'json', 'both'],
        default='html',
        help='Output format (default: html)'
    )
    parser.add_argument(
        '--json-summary',
        metavar='FILE',
        help='Also generate a minimal JSON summary (for CI/CD)'
    )
    
    # Parser options
    parser.add_argument(
        '--parser',
        choices=['logcat', 'dmesg', 'auto'],
        default='auto',
        help='Log parser to use (default: auto-detect)'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=datetime.now().year,
        help='Year for timestamps (Android logs omit year)'
    )
    parser.add_argument(
        '--pattern',
        default='*.log',
        help='Glob pattern for log files in directory (default: *.log)'
    )
    
    # Analysis options
    parser.add_argument(
        '--no-automotive',
        action='store_true',
        help='Disable automotive-specific analysis'
    )
    parser.add_argument(
        '--min-severity',
        choices=['info', 'warning', 'error', 'critical'],
        default='info',
        help='Minimum severity to report (default: info)'
    )
    
    # General options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    return parser


def detect_parser(filepath: Path) -> str:
    """Auto-detect log format."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = [f.readline() for _ in range(10)]
        
        content = '\n'.join(first_lines)
        
        # Check for dmesg format
        if '[' in content and ']' in content and any(
            line.strip().startswith('[') for line in first_lines
        ):
            return 'dmesg'
        
        # Default to logcat
        return 'logcat'
    except Exception:
        return 'logcat'


def main(args=None):
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(args)
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    log_path = Path(args.log_path)
    
    # Validate input
    if not log_path.exists():
        logger.error(f"Path not found: {log_path}")
        sys.exit(1)
    
    # Select parser
    if args.parser == 'auto':
        if log_path.is_file():
            parser_type = detect_parser(log_path)
        else:
            # Check first file in directory
            log_files = list(log_path.glob(args.pattern))
            parser_type = detect_parser(log_files[0]) if log_files else 'logcat'
    else:
        parser_type = args.parser
    
    logger.info(f"Using {parser_type} parser")
    
    # Create parser
    if parser_type == 'dmesg':
        log_parser = DmesgParser(year=args.year)
    else:
        log_parser = LogcatParser(year=args.year)
    
    # Parse logs
    logger.info(f"Parsing logs from: {log_path}")
    
    if log_path.is_file():
        entries = log_parser.parse_file(log_path)
    else:
        entries = log_parser.parse_directory(log_path, args.pattern)
    
    if not entries:
        logger.error("No log entries parsed")
        sys.exit(1)
    
    logger.info(f"Parsed {len(entries):,} log entries")
    
    # Generate statistics
    logger.info("Generating statistics...")
    stats = LogStatistics(entries).generate_summary()
    
    # Run analysis
    logger.info("Running analysis...")
    analyzer = AutomotiveAnalyzer()
    analysis_results = analyzer.analyze(entries)
    
    # Get automotive summary
    automotive_summary = None
    if not args.no_automotive:
        automotive_summary = analyzer.get_automotive_summary(entries)
    
    logger.info(f"Found {len(analysis_results)} issues")
    
    # Generate reports
    output_path = Path(args.output)
    
    if args.format in ('html', 'both'):
        html_path = output_path if args.format == 'html' else output_path.with_suffix('.html')
        HTMLReportGenerator().generate(
            stats, analysis_results, str(html_path),
            automotive_summary=automotive_summary
        )
        logger.info(f"HTML report: {html_path}")
    
    if args.format in ('json', 'both'):
        json_path = output_path if args.format == 'json' else output_path.with_suffix('.json')
        JSONReportGenerator().generate(
            stats, analysis_results, str(json_path),
            automotive_summary=automotive_summary
        )
        logger.info(f"JSON report: {json_path}")
    
    if args.json_summary:
        JSONReportGenerator().generate_summary_only(
            stats, analysis_results, args.json_summary
        )
        logger.info(f"Summary JSON: {args.json_summary}")
    
    # Print summary to console
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total log entries: {stats['total_entries']:,}")
    print(f"Time range: {stats.get('time_range', 'N/A')}")
    print(f"Errors: {stats.get('error_count', 0) + stats.get('fatal_count', 0)}")
    print(f"Warnings: {stats.get('warning_count', 0)}")
    print(f"Issues detected: {len(analysis_results)}")
    
    if analysis_results:
        print("\nTop issues:")
        for result in analysis_results[:5]:
            print(f"  [{result.severity.name}] {result.title}: {result.occurrences} occurrences")
    
    print("="*60 + "\n")
    
    # Exit with error code if critical issues found
    critical_count = sum(1 for r in analysis_results if r.severity.name == 'CRITICAL')
    if critical_count > 0:
        logger.warning(f"Found {critical_count} critical issues!")
        sys.exit(2)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
