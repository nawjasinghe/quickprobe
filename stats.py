"""statistics calculations for pingslo"""
import statistics
import numpy as np


"""compute avg, p95, p99, min, max from latency measurements"""
def compute_stats(latencies):
    count = len(latencies)
    
    # handle empty list - all probes failed
    if count == 0:
        return {
            'count': 0,
            'avg_ms': None,
            'p95_ms': None,
            'p99_ms': None,
            'min_ms': None,
            'max_ms': None,
        }
    
    # calcualte basic stats from successful measurements
    avg_ms = statistics.mean(latencies)
    min_ms = min(latencies)
    max_ms = max(latencies)
    
    # percentiles - method='higher' returns actual observed value not interpolated
    # this matters for slo evaluation accuracy
    if count == 1:
        # edge case - only one sample so all percentiles are same
        p95_ms = latencies[0]
        p99_ms = latencies[0]
    else:
        # numpy gives us better control than statistics.quantiles
        p95_ms = np.percentile(latencies, 95, method='higher')
        p99_ms = np.percentile(latencies, 99, method='higher')
    
    return {
        'count': count,
        'avg_ms': avg_ms,
        'p95_ms': p95_ms,
        'p99_ms': p99_ms,
        'min_ms': min_ms,
        'max_ms': max_ms,
    }
