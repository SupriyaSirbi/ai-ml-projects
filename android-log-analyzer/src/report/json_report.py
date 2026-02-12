"""JSON report generator."""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import logging

from ..models import AnalysisResult

logger = logging.getLogger(__name__)


class JSONReportGenerator:
    """Generate JSON reports from analysis results."""
    
    def generate(self,
                 stats: Dict[str, Any],
                 analysis_results: List[AnalysisResult],
                 output_path: str,
                 automotive_summary: Dict = None,
                 include_samples: bool = True) -> None:
        """
        Generate JSON report.
        
        Args:
            stats: Statistics dictionary
            analysis_results: List of analysis results
            output_path: Path to save JSON file
            automotive_summary: Optional automotive-specific summary
            include_samples: Whether to include sample messages
        """
        report = self._build_report(stats, analysis_results, automotive_summary, include_samples)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"JSON report generated: {output_path}")
    
    def _build_report(self, 
                      stats: Dict,
                      results: List[AnalysisResult],
                      automotive_summary: Dict,
                      include_samples: bool) -> Dict:
        """Build the report dictionary."""
        report = {
            'report_info': {
                'generated_at': datetime.now().isoformat(),
                'tool_version': '1.0.0',
                'report_type': 'android_automotive_log_analysis'
            },
            'summary': {
                'total_entries': stats.get('total_entries', 0),
                'time_range': {
                    'start': stats.get('start_time'),
                    'end': stats.get('end_time'),
                    'duration': stats.get('time_range')
                },
                'level_counts': {
                    'verbose': stats.get('verbose_count', 0),
                    'debug': stats.get('debug_count', 0),
                    'info': stats.get('info_count', 0),
                    'warning': stats.get('warning_count', 0),
                    'error': stats.get('error_count', 0),
                    'fatal': stats.get('fatal_count', 0)
                },
                'rates': {
                    'logs_per_second': stats.get('logs_per_second', 0),
                    'errors_per_minute': stats.get('errors_per_minute', 0),
                    'warnings_per_minute': stats.get('warnings_per_minute', 0)
                },
                'unique_tags': stats.get('unique_tags', 0),
                'unique_pids': stats.get('unique_pids', 0)
            },
            'issues': [self._serialize_result(r, include_samples) for r in results],
            'issues_by_severity': {
                'critical': [r.category for r in results if r.severity.name == 'CRITICAL'],
                'error': [r.category for r in results if r.severity.name == 'ERROR'],
                'warning': [r.category for r in results if r.severity.name == 'WARNING'],
                'info': [r.category for r in results if r.severity.name == 'INFO']
            },
            'top_tags': stats.get('top_tags', {}),
            'top_error_tags': stats.get('top_error_tags', {}),
            'top_pids': stats.get('top_pids', {})
        }
        
        if automotive_summary:
            report['automotive'] = automotive_summary
        
        return report
    
    def _serialize_result(self, result: AnalysisResult, include_samples: bool) -> Dict:
        """Serialize an analysis result."""
        data = result.to_dict()
        
        if not include_samples:
            data.pop('sample_messages', None)
        
        return data
    
    def generate_summary_only(self,
                             stats: Dict[str, Any],
                             analysis_results: List[AnalysisResult],
                             output_path: str) -> None:
        """
        Generate a minimal summary JSON (for CI/CD integration).
        
        Args:
            stats: Statistics dictionary
            analysis_results: List of analysis results
            output_path: Path to save JSON file
        """
        # Count by severity
        severity_counts = {
            'critical': 0,
            'error': 0,
            'warning': 0,
            'info': 0
        }
        
        total_occurrences = 0
        for result in analysis_results:
            severity_counts[result.severity.name.lower()] += 1
            total_occurrences += result.occurrences
        
        summary = {
            'status': 'fail' if severity_counts['critical'] > 0 else 'pass',
            'total_logs': stats.get('total_entries', 0),
            'total_issues': len(analysis_results),
            'total_occurrences': total_occurrences,
            'severity_counts': severity_counts,
            'error_rate': stats.get('errors_per_minute', 0),
            'time_range': stats.get('time_range'),
            'top_issues': [
                {'category': r.category, 'severity': r.severity.name, 'count': r.occurrences}
                for r in analysis_results[:5]
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Summary JSON generated: {output_path}")
