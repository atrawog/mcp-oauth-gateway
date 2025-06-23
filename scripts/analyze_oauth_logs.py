#!/usr/bin/env python3
"""Sacred OAuth Log Analysis Script
Analyzes OAuth flow patterns and errors from logs.
"""
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def analyze_logs(log_dir: Path) -> dict:
    """Analyze OAuth logs for patterns and issues."""
    stats = {
        "total_requests": 0,
        "endpoints": defaultdict(int),
        "errors": defaultdict(int),
        "client_registrations": 0,
        "token_exchanges": 0,
        "auth_failures": 0,
        "successful_flows": 0
    }

    if not log_dir.exists():
        return stats

    # Process all log files
    for log_file in log_dir.glob("**/*.log"):
        try:
            with open(log_file) as f:
                for line in f:
                    analyze_line(line, stats)
        except Exception as e:
            print(f"Error reading {log_file}: {e}")

    return stats


def analyze_line(line: str, stats: dict):
    """Analyze a single log line."""
    stats["total_requests"] += 1

    # Check for specific endpoints
    if "/register" in line:
        stats["endpoints"]["register"] += 1
        if "201" in line:
            stats["client_registrations"] += 1

    if "/authorize" in line:
        stats["endpoints"]["authorize"] += 1

    if "/token" in line:
        stats["endpoints"]["token"] += 1
        if "200" in line:
            stats["token_exchanges"] += 1

    if "/verify" in line:
        stats["endpoints"]["verify"] += 1

    # Check for errors
    if "401" in line or "WWW-Authenticate" in line:
        stats["auth_failures"] += 1

    if "error" in line.lower():
        # Try to extract error type
        error_match = re.search(r'"error"\s*:\s*"([^"]+)"', line)
        if error_match:
            stats["errors"][error_match.group(1)] += 1


def generate_report(stats: dict) -> str:
    """Generate markdown report from stats."""
    report = f"""# OAuth Flow Analysis Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary Statistics

- Total Requests: {stats['total_requests']}
- Client Registrations: {stats['client_registrations']}
- Token Exchanges: {stats['token_exchanges']}
- Auth Failures: {stats['auth_failures']}

## Endpoint Usage

| Endpoint | Requests |
|----------|----------|
"""

    for endpoint, count in sorted(stats['endpoints'].items()):
        report += f"| /{endpoint} | {count} |\n"

    if stats['errors']:
        report += "\n## Error Distribution\n\n"
        report += "| Error Type | Count |\n"
        report += "|------------|-------|\n"

        for error, count in sorted(stats['errors'].items(), key=lambda x: x[1], reverse=True):
            report += f"| {error} | {count} |\n"

    # Add recommendations
    report += "\n## Recommendations\n\n"

    if stats['auth_failures'] > stats['token_exchanges']:
        report += "- ⚠️ High auth failure rate detected. Check client credentials.\n"

    if stats['errors'].get('invalid_client', 0) > 0:
        report += "- ⚠️ Invalid client errors detected. Verify client registration.\n"

    if stats['client_registrations'] == 0 and stats['total_requests'] > 0:
        report += "- ℹ️ No client registrations found. Ensure clients are registering properly.\n"

    return report


def main():
    """Main analysis function."""
    log_dir = Path(__file__).parent.parent / "logs"
    stats = analyze_logs(log_dir)
    report = generate_report(stats)
    print(report)


if __name__ == "__main__":
    main()
