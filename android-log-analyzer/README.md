# Android Automotive Log Analyzer

A Python tool for parsing and analyzing Android 15 Automotive system logs. Detects issues related to Vehicle HAL, Car Services, CAN bus, and other automotive-specific components.

## Features

- **Multi-format parsing**: Supports Android logcat (threadtime, brief, time) and dmesg/kernel logs
- **Automotive-specific analysis**: Pre-configured patterns for Vehicle HAL, CarService, CAN bus, etc.
- **Comprehensive reports**: HTML and JSON output with visualizations
- **CI/CD integration**: Minimal JSON summary for automated pipelines
- **Extensible**: Add custom patterns via YAML configuration

## Installation

```bash
# Clone or copy the project
cd android-log-analyzer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```bash
# Analyze a single log file
python -m src.main logcat.log

# Analyze a directory of logs
python -m src.main /path/to/logs/ -o report.html

# Generate JSON report
python -m src.main logs/ --format json -o analysis.json

# Generate both HTML and CI summary
python -m src.main device.log -o report.html --json-summary ci_result.json
```

## Collecting Logs from Device

```bash
# Pull logcat (standard)
adb logcat -d > device_logcat.log

# Pull logcat with timestamps
adb logcat -v threadtime -d > device_logcat.log

# Pull kernel logs
adb shell dmesg > kernel.log

# Pull CarService specific logs
adb logcat -d -s CarService:* VehicleHal:* > car_logs.log

# Pull full bug report (includes everything)
adb bugreport > bugreport.zip
```

## Usage

```
usage: main.py [-h] [-o OUTPUT] [--format {html,json,both}]
               [--json-summary FILE] [--parser {logcat,dmesg,auto}]
               [--year YEAR] [--pattern PATTERN] [--no-automotive]
               [--min-severity {info,warning,error,critical}] [-v] [--version]
               log_path

Arguments:
  log_path              Path to log file or directory

Options:
  -o, --output          Output report file (default: analysis_report.html)
  --format              Output format: html, json, or both
  --json-summary        Generate minimal JSON for CI/CD
  --parser              Log parser: logcat, dmesg, or auto
  --year                Year for timestamps (default: current year)
  --pattern             Glob pattern for directory (default: *.log)
  --no-automotive       Disable automotive analysis
  --min-severity        Minimum severity to report
  -v, --verbose         Verbose output
```

## Project Structure

```
android-log-analyzer/
├── config/
│   └── default_config.yaml     # Default configuration
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Settings management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── log_entry.py        # LogEntry data model
│   │   └── analysis_result.py  # AnalysisResult model
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── base_parser.py      # Abstract parser
│   │   ├── logcat_parser.py    # Android logcat parser
│   │   └── dmesg_parser.py     # Kernel dmesg parser
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── statistics.py       # Log statistics
│   │   ├── pattern_analyzer.py # Pattern-based analysis
│   │   └── automotive_analyzer.py  # Automotive-specific
│   └── report/
│       ├── __init__.py
│       ├── html_report.py      # HTML report generator
│       └── json_report.py      # JSON report generator
├── tests/
│   └── sample_logs/            # Sample log files for testing
├── requirements.txt
└── README.md
```

## Detected Issues

### General Android
- ANR (Application Not Responding)
- Native crashes (SIGSEGV, SIGABRT)
- Java/Kotlin exceptions
- Out of memory
- Watchdog timeouts
- Service deaths
- Permission denials

### Android Automotive Specific
- Vehicle HAL errors
- VHAL timeouts
- Power state transitions issues
- Deep sleep failures
- Garage mode problems
- Audio focus conflicts
- Audio zone errors
- Instrument cluster disconnections
- CAN bus errors
- LIN bus errors
- GNSS/GPS failures
- EVS camera errors
- Car watchdog timeouts

## Customization

### Adding Custom Patterns

Edit `config/default_config.yaml`:

```yaml
custom_patterns:
  - name: my_custom_issue
    regex: "MyApp.*(error|fail)"
    tags: [MyApp, MyService]
    severity: error
    description: "Custom app error detected"
    recommendation: "Check MyApp logs for details"
```

### Programmatic Usage

```python
from src.parser import LogcatParser
from src.analysis import AutomotiveAnalyzer, LogStatistics
from src.report import HTMLReportGenerator

# Parse logs
parser = LogcatParser(year=2026)
entries = parser.parse_file('logcat.log')

# Analyze
analyzer = AutomotiveAnalyzer()
results = analyzer.analyze(entries)

# Statistics
stats = LogStatistics(entries).generate_summary()

# Generate report
HTMLReportGenerator().generate(stats, results, 'report.html')
```

## CI/CD Integration

Use `--json-summary` for pipeline integration:

```bash
python -m src.main logs/ --json-summary result.json
```

Output format:
```json
{
  "status": "pass",
  "total_logs": 50000,
  "total_issues": 3,
  "severity_counts": {
    "critical": 0,
    "error": 2,
    "warning": 1,
    "info": 0
  },
  "top_issues": [...]
}
```

Exit codes:
- `0`: Success, no critical issues
- `1`: Error (file not found, parse error)
- `2`: Critical issues detected

## License

MIT License
