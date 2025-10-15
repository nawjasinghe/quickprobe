"""json report generation"""
import json
from datetime import datetime
from pathlib import Path


"""generate json report from probe results"""
def generate_json_report(results, slo_evaluations, config, output_path):
    # structured report with metadata, summary, and detailed results
    report = {
        'metadata': {
            'timestamp': datetime.utcnow().isoformat() + 'Z',  # iso 8601 format
            'tool': 'PingSLO',
            'version': '0.1.0',
            'config': config,  # probe settings used
        },
        'summary': {
            'total_targets': len(results),
            'slo_passed': sum(1 for e in slo_evaluations if e['passed']),
            'slo_failed': sum(1 for e in slo_evaluations if not e['passed']),
        },
        'targets': [],
    }
    
    # iterate through results and evaluations together
    for result, slo_eval in zip(results, slo_evaluations):
        target_data = {
            'host': result['host'],
            'port': result['port'],
            'target': f"{result['host']}:{result['port']}",
            'statistics': result['stats'],  # avg, p95, p99, etc
            'loss_pct': result['loss_pct'],
            'slo': {
                'passed': slo_eval['passed'],
                'thresholds': slo_eval['thresholds'],
                'failures': slo_eval['failures'],  # reasons for failure if any
            }
        }
        report['targets'].append(target_data)
    
    # write json with nice indentation for readability
    output_path = Path(output_path)
    with output_path.open('w') as f:
        json.dump(report, f, indent=2)
    
    return report


"""print summary of json report file"""
def format_json_summary(report_path):
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    print(f"\nReport saved: {report_path}")
    print(f"   Timestamp: {report['metadata']['timestamp']}")
    print(f"   Total targets: {report['summary']['total_targets']}")
    print(f"   SLO passed: {report['summary']['slo_passed']}")
    print(f"   SLO failed: {report['summary']['slo_failed']}")
