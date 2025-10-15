"""tests for statistics calculations"""
import pytest


"""test basic stats calculation"""
def test_compute_stats_basic():
    from stats import compute_stats
    
    latencies = [10, 20, 30, 40, 50]
    result = compute_stats(latencies)
    
    assert result['avg_ms'] == 30.0
    assert result['p95_ms'] == 50.0
    assert result['p99_ms'] == 50.0
    assert result['min_ms'] == 10.0
    assert result['max_ms'] == 50.0
    assert result['count'] == 5


"""test with realistic latencies including outliers"""
def test_compute_stats_realistic():
    from stats import compute_stats
    
    # 95 fast probes, 5 slow probes
    latencies = [15.0] * 95 + [200.0] * 5
    result = compute_stats(latencies)
    
    assert result['avg_ms'] == pytest.approx(24.25, rel=0.01)
    assert result['p95_ms'] == 200.0  # lands on slow group
    assert result['count'] == 100


"""test edge case - all probes failed"""
def test_compute_stats_empty():
    from stats import compute_stats
    
    result = compute_stats([])
    
    assert result['count'] == 0
    assert result['avg_ms'] is None
    assert result['p95_ms'] is None


"""test edge case - only one successfull probe"""
def test_compute_stats_single_value():
    from stats import compute_stats
    
    result = compute_stats([42.5])
    
    assert result['avg_ms'] == 42.5
    assert result['p95_ms'] == 42.5
    assert result['p99_ms'] == 42.5
    assert result['count'] == 1
