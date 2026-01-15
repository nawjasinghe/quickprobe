# QuickProbe - Network SLO Monitoring Tool

A lightweight, async Python tool for monitoring network Service Level Objectives (SLOs) through TCP connection tests and HTTP Time-To-First-Byte (TTFB) measurements

## Features

- **Dual Probe Modes**
  - **TCP**: Measure connection establishment time
  - **HTTP**: Measure Time To First Byte / TTFB (application responsiveness)

- **Smart SLO Evaluation**
  - Configure per-target or default targets
  - p95/p99 latency checks
  - Packet loss monitoring

- **High Performance**
  - Support for concurrent probing
  - Configurable concurrency limits (semaphore-based)
  - Efficient HEAD→GET for HTTP probes

- **Flexible Output**
  - Machine-readable JSON reports

- **Production Ready**
  - Configurable timeouts and retries
  - Per-target SLO overrides via YAML config

---

## Tech Stack
- Python
- Pytest (Unit Testing)
- Batch Files (Setup and UI)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

**Automated Setup (Windows)**

Download all the python files and run the setup batch file:
```bash
setup.bat
```

## Quick Start

Simply run `run.bat` it will:
- let you select TCP or HTTP probe mode
- Let you enter websites one at a time
- Change SLO targets
- Ask how many samples you want
- Optionally save results to JSON
- Display results in a table
- Offer to run another test

## Configuration

### Targets File Format

```text
# Formats supported:
hostname                    # Uses default port 443
hostname:port               # Explicit port
https://hostname            # Full URL (port 443)
http://hostname             # Full URL (port 80)

# Examples:
google.com
github.com:443
https://example.com/health
```

### SLO Configuration (`config.yaml`)

```yaml
# Default SLO for all targets
default_slo:
  latency_p95_ms: 100.0    # p95 must be ≤ 100ms
  latency_p99_ms: 200.0    # p99 must be ≤ 200ms (optional)
  max_loss_pct: 5.0        # Loss must be ≤ 5%

# Per-target overrides
target_slos:
  api.example.com:
    latency_p95_ms: 50.0   # Stricter for critical API
    max_loss_pct: 1.0
  
  slow-service.com:
    latency_p95_ms: 500.0  # More lenient for known slow service
```

**SLO Thresholds Explanation:**
- **latency_p95_ms**: 95th percentile latency threshold. 95% of probes must be faster than this.
- **latency_p99_ms**: 99th percentile latency threshold (optional). 99% of probes must be faster than this.
- **max_loss_pct**: Maximum acceptable probe failure rate (0-100%).

**Recommended SLO values:**
- **TCP mode**: p95≤100ms, loss≤5%
- **HTTP mode**: p95≤500ms, p99≤1000ms, loss≤5%

---

## Output

### Console Output

```
RESULTS
================================================================
Target              Avg (ms)  P95 (ms)  P99 (ms)  Loss %  SLO
----------------------------------------------------------------
google.com:443      30.47     65.44     65.44     0.0%    PASS
slow-site.com:443   450.23    890.12    890.12    10.0%   FAIL
  ! p95 latency 890.12ms exceeds threshold 500.00ms
  ! Loss 10.0% exceeds threshold 5.0%
================================================================

SLO Summary: 1 passed, 1 failed (out of 2 targets)
```

### JSON Report

```json
{
  "metadata": {
    "timestamp": "2025-10-14T23:27:51.244796Z",
    "tool": "PingSLO",
    "version": "0.1.0",
    "config": {
      "mode": "tcp",
      "samples": 10,
      "timeout": 5.0
    }
  },
  "summary": {
    "total_targets": 2,
    "slo_passed": 1,
    "slo_failed": 1
  },
  "targets": [
    {
      "host": "google.com",
      "port": 443,
      "statistics": {
        "avg_ms": 30.47,
        "p95_ms": 65.44,
        "p99_ms": 65.44,
        "loss_pct": 0.0
      },
      "slo": {
        "passed": true,
        "thresholds": {...},
        "failures": []
      }
    }
  ]
}
```

### Key Design Decisions

**1. Why asyncio instead of threads?**
- Network I/O is I/O-bound, not CPU-bound
- Asyncio handles 1000s of concurrent connections efficiently
- Lower memory overhead than threads
- Better for timing-sensitive measurements

**2. Why HEAD→GET fallback?**
- HEAD is faster and uses less bandwidth
- Some servers return 405 (Method Not Allowed) for HEAD
- GET always works (HTTP spec requirement)

**3. Why semaphore for concurrency?**
- Prevents overwhelming network/system resources
- Respects server rate limits
- Configurable based on environment
---

## FAQ

**Q: TCP vs HTTP mode - which should I use?**
A: 
- TCP = "Can I reach the server?" (connection only)
- HTTP = "How responsive is the application?" (full request/response)

**Q: Why are my HTTP p95 values 10x higher than TCP?**
A: HTTP includes TCP + TLS + HTTP processing. Set different SLO thresholds.

**Q: How many samples should I use?**
A: 
- Quick check: 5-10 samples
- SLO evaluation: 20-50 samples
- Statistical accuracy: 100+ samples

**Q: What's a good concurrency limit?**
A: Default 5 is safe. Increase to 10-20 if monitoring many fast targets. Lower to 1-3 for slow/rate-limited targets.

