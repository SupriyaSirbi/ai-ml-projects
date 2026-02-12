"""HTML report generator."""

import json
from pathlib import Path
from typing import Dict, List, Any
import logging

from ..models import AnalysisResult, Severity

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Generate HTML reports from analysis results."""
    
    def generate(self, 
                 stats: Dict[str, Any], 
                 analysis_results: List[AnalysisResult],
                 output_path: str,
                 title: str = "Android Automotive Log Analysis Report",
                 automotive_summary: Dict = None) -> None:
        """
        Generate HTML report.
        
        Args:
            stats: Statistics dictionary
            analysis_results: List of analysis results
            output_path: Path to save HTML file
            title: Report title
            automotive_summary: Optional automotive-specific summary
        """
        html_content = self._build_html(stats, analysis_results, title, automotive_summary)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_path}")
    
    def _build_html(self, stats: Dict, results: List[AnalysisResult], 
                    title: str, automotive_summary: Dict = None) -> str:
        """Build the HTML content."""
        
        # Count issues by severity
        critical_count = sum(1 for r in results if r.severity == Severity.CRITICAL)
        error_count = sum(1 for r in results if r.severity == Severity.ERROR)
        warning_count = sum(1 for r in results if r.severity == Severity.WARNING)
        
        issues_html = ''.join(self._render_issue(r) for r in results)
        automotive_section = self._render_automotive_summary(automotive_summary) if automotive_summary else ''
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f0f2f5; 
            color: #1a1a2e;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        
        header {{
            background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        header h1 {{ font-size: 28px; margin-bottom: 5px; }}
        header .subtitle {{ opacity: 0.9; font-size: 14px; }}
        
        .card {{
            background: white;
            padding: 24px;
            margin: 16px 0;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .card h2 {{
            font-size: 18px;
            color: #1a73e8;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e8eaed;
        }}
        
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            transition: transform 0.2s;
        }}
        .stat-box:hover {{ transform: translateY(-2px); }}
        .stat-value {{
            font-size: 36px;
            font-weight: 700;
            color: #1a73e8;
        }}
        .stat-value.critical {{ color: #dc3545; }}
        .stat-value.error {{ color: #fd7e14; }}
        .stat-value.warning {{ color: #ffc107; }}
        .stat-label {{
            color: #5f6368;
            font-size: 13px;
            margin-top: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .issue {{
            padding: 16px;
            margin: 12px 0;
            border-radius: 8px;
            border-left: 4px solid #ccc;
            background: #fafafa;
        }}
        .issue.severity-critical {{ border-left-color: #dc3545; background: #fff5f5; }}
        .issue.severity-error {{ border-left-color: #fd7e14; background: #fff8f0; }}
        .issue.severity-warning {{ border-left-color: #ffc107; background: #fffef0; }}
        .issue.severity-info {{ border-left-color: #17a2b8; background: #f0f9ff; }}
        
        .issue-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .issue-title {{ font-weight: 600; font-size: 16px; }}
        .issue-count {{
            background: #e8eaed;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
        }}
        .issue-description {{ color: #5f6368; margin-bottom: 8px; }}
        .issue-meta {{ font-size: 12px; color: #80868b; margin-bottom: 8px; }}
        .issue-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 8px;
        }}
        .tag {{
            background: #e8f0fe;
            color: #1a73e8;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .recommendation {{
            background: #e6f4ea;
            border-left: 3px solid #34a853;
            padding: 10px 14px;
            border-radius: 0 6px 6px 0;
            font-size: 13px;
        }}
        .recommendation strong {{ color: #137333; }}
        
        .sample-messages {{
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 11px;
            max-height: 150px;
            overflow-y: auto;
        }}
        .sample-messages div {{
            padding: 4px 0;
            border-bottom: 1px solid #e8eaed;
            word-break: break-all;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}
        .chart-container {{
            position: relative;
            height: 300px;
        }}
        
        .automotive-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
        }}
        .subsystem-box {{
            padding: 16px;
            background: #f8f9fa;
            border-radius: 8px;
            text-align: center;
        }}
        .subsystem-name {{ font-weight: 600; margin-bottom: 8px; text-transform: capitalize; }}
        .subsystem-stats {{ font-size: 13px; color: #5f6368; }}
        .subsystem-errors {{ color: #dc3545; font-weight: 600; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e8eaed;
        }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        tr:hover {{ background: #f8f9fa; }}
        
        @media (max-width: 768px) {{
            .stat-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .charts-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="subtitle">Generated: {stats.get('end_time', 'N/A')} | Analyzed: {stats.get('total_entries', 0):,} log entries</div>
        </header>
        
        <div class="card">
            <h2>Summary Overview</h2>
            <div class="stat-grid">
                <div class="stat-box">
                    <div class="stat-value">{stats.get('total_entries', 0):,}</div>
                    <div class="stat-label">Total Log Entries</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value critical">{critical_count}</div>
                    <div class="stat-label">Critical Issues</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value error">{stats.get('error_count', 0) + stats.get('fatal_count', 0)}</div>
                    <div class="stat-label">Errors & Fatals</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value warning">{stats.get('warning_count', 0)}</div>
                    <div class="stat-label">Warnings</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{stats.get('errors_per_minute', 0)}</div>
                    <div class="stat-label">Errors/Minute</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{stats.get('unique_tags', 0)}</div>
                    <div class="stat-label">Unique Tags</div>
                </div>
            </div>
            <p><strong>Time Range:</strong> {stats.get('start_time', 'N/A')} to {stats.get('end_time', 'N/A')} ({stats.get('time_range', 'N/A')})</p>
        </div>
        
        {automotive_section}
        
        <div class="card">
            <h2>Detected Issues ({len(results)})</h2>
            {issues_html if issues_html else '<p style="color:#5f6368">No significant issues detected.</p>'}
        </div>
        
        <div class="card">
            <h2>Log Distribution</h2>
            <div class="charts-grid">
                <div>
                    <h3 style="font-size:14px;margin-bottom:10px;">Log Level Distribution</h3>
                    <div class="chart-container">
                        <canvas id="levelChart"></canvas>
                    </div>
                </div>
                <div>
                    <h3 style="font-size:14px;margin-bottom:10px;">Top Tags by Frequency</h3>
                    <div class="chart-container">
                        <canvas id="tagChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>Top 15 Log Sources</h2>
            <table>
                <thead>
                    <tr>
                        <th>Tag</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    {self._render_top_tags_table(stats)}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Level distribution chart
        const levelCtx = document.getElementById('levelChart').getContext('2d');
        const levelData = {json.dumps(stats.get('level_distribution', {}))};
        new Chart(levelCtx, {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(levelData),
                datasets: [{{
                    data: Object.values(levelData),
                    backgroundColor: ['#6c757d', '#17a2b8', '#28a745', '#ffc107', '#dc3545', '#343a40']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'right' }}
                }}
            }}
        }});
        
        // Top tags chart
        const tagCtx = document.getElementById('tagChart').getContext('2d');
        const tagData = {json.dumps(dict(list(stats.get('top_tags', {}).items())[:10]))};
        new Chart(tagCtx, {{
            type: 'bar',
            data: {{
                labels: Object.keys(tagData),
                datasets: [{{
                    label: 'Log Count',
                    data: Object.values(tagData),
                    backgroundColor: '#1a73e8'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    def _render_issue(self, result: AnalysisResult) -> str:
        """Render a single issue card."""
        severity_class = result.severity.css_class
        tags_html = ''.join(f'<span class="tag">{tag}</span>' for tag in result.affected_tags[:8])
        
        samples_html = ''
        if result.sample_messages:
            samples = ''.join(f'<div>{msg[:200]}...</div>' if len(msg) > 200 else f'<div>{msg}</div>' 
                            for msg in result.sample_messages[:3])
            samples_html = f'<div class="sample-messages">{samples}</div>'
        
        return f'''
        <div class="issue {severity_class}">
            <div class="issue-header">
                <span class="issue-title">{result.title}</span>
                <span class="issue-count">{result.occurrences} occurrences</span>
            </div>
            <p class="issue-description">{result.description}</p>
            <p class="issue-meta">
                <strong>First seen:</strong> {result.first_seen or 'N/A'} | 
                <strong>Last seen:</strong> {result.last_seen or 'N/A'}
            </p>
            <div class="issue-tags">{tags_html}</div>
            <div class="recommendation"><strong>Recommendation:</strong> {result.recommendation}</div>
            {samples_html}
        </div>
        '''
    
    def _render_top_tags_table(self, stats: Dict) -> str:
        """Render top tags as table rows."""
        top_tags = list(stats.get('top_tags', {}).items())[:15]
        total = stats.get('total_entries', 1)
        
        rows = []
        for tag, count in top_tags:
            pct = (count / total) * 100
            rows.append(f'<tr><td>{tag}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>')
        
        return '\n'.join(rows)
    
    def _render_automotive_summary(self, summary: Dict) -> str:
        """Render automotive-specific summary section."""
        if not summary or not summary.get('subsystem_activity'):
            return ''
        
        subsystems_html = ''
        for name, data in summary['subsystem_activity'].items():
            errors_class = 'subsystem-errors' if data['errors'] > 0 else ''
            subsystems_html += f'''
            <div class="subsystem-box">
                <div class="subsystem-name">{name}</div>
                <div class="subsystem-stats">
                    {data['total']:,} logs<br>
                    <span class="{errors_class}">{data['errors']} errors</span>
                </div>
            </div>
            '''
        
        return f'''
        <div class="card">
            <h2>Automotive Subsystems</h2>
            <div class="automotive-grid">
                {subsystems_html}
            </div>
            <div style="margin-top:16px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px;text-align:center;">
                <div><strong>{summary.get('vehicle_property_errors', 0)}</strong><br><small>Vehicle Property Errors</small></div>
                <div><strong>{summary.get('power_transitions', 0)}</strong><br><small>Power Transitions</small></div>
                <div><strong>{summary.get('can_errors', 0)}</strong><br><small>CAN Bus Errors</small></div>
            </div>
        </div>
        '''
