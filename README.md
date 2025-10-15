# PingSLO - Network SLO Monitoring Tool

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

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

**Automated Setup (Windows)**

Simply run the setup batch file:
```bash
setup.bat
```

## Quick Start

### Windows Users (Easy Mode)

Use the provided batch file for convenience:

**Quick test of a single target:**
```bash
run.bat sample --url google.com --samples 5
```

**Test multiple targets:**
```bash
run.bat run --targets urls.txt --samples 10
```

**Or use Interactive Mode (Recommended):**

Simply run `run.bat` without arguments for an interactive menu that will:
- Guide you through selecting TCP or HTTP probe mode
- Let you enter websites one at a time (no file needed!)
- Ask how many samples you want
- Optionally save results to JSON
- Display results in a table
- Offer to run another test

### Manual Usage

### 1. Create a targets file (`urls.txt`)

```text
# My targets
google.com
github.com:443
https://example.com
```

### 2. Run TCP probes

```bash
python main.py run --targets urls.txt --mode tcp --samples 10
```

### 3. Run HTTP TTFB probes

```bash
python main.py run --targets urls.txt --mode http --samples 10 --out report.json
```

### 4. Quick test a single URL

```bash
python main.py sample --url google.com --mode tcp --samples 5
```

---

## Usage

### Commands

#### `run` - Probe multiple targets

```bash
python main.py run --targets <file> [options]
```

**Options:**
- `--targets <file>` - Path to targets file (required)
- `--mode <tcp|http>` - Probe mode (default: tcp)
- `--samples <N>` - Number of probes per target (default: 10)
- `--timeout <seconds>` - Timeout per probe (default: 5.0)
- `--interval <seconds>` - Delay between probes (default: 0.5)
- `--concurrent <N>` - Max concurrent targets (default: 5)
- `--config <file>` - SLO config YAML (default: config.yaml if exists)
- `--out <file>` - Output JSON report path

**Example:**
```bash
python main.py run --targets urls.txt --mode http --samples 20 --out results.json
```

#### `sample` - Quick test single URL

```bash
python main.py sample --url <url> [options]
```

**Options:**
- `--url <url>` - URL or hostname to test (required)
- `--mode <tcp|http>` - Probe mode (default: tcp)
- `--samples <N>` - Number of probes (default: 5)
- `--timeout <seconds>` - Timeout per probe (default: 5.0)
- `--interval <seconds>` - Delay between probes (default: 0.5)

**Example:**
```bash
python main.py sample --url https://api.example.com --mode http --samples 10
```

---

## Configuration

### Targets File Format

```text
# Lines starting with # are comments
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

---

## Architecture

### Project Structure

```
PingSLO Project/
├── main.py           # CLI entry point (argparse)
├── runner.py         # Multi-target coordination
├── tcp_probe.py      # TCP connection probing
├── http_probe.py     # HTTP TTFB probing
├── stats.py          # Percentile calculations
├── slo.py            # SLO evaluation logic
├── report.py         # JSON report generation
├── test_stats.py     # Unit tests
├── config.yaml       # SLO configuration
├── urls.txt          # Targets file
└── README.md         # This file
```

### Key Design Decisions

**1. Why asyncio instead of threads?**
- Network I/O is I/O-bound, not CPU-bound
- Asyncio handles 1000s of concurrent connections efficiently
- Lower memory overhead than threads
- Better for timing-sensitive measurements

**2. Why numpy for percentiles?**
- `method='higher'` ensures actual observed values (no interpolation)
- Critical for SLO accuracy - we want real measurements
- Alternative stdlib `statistics.quantiles()` interpolates

**3. Why HEAD→GET fallback?**
- HEAD is faster and uses less bandwidth
- Some servers return 405 (Method Not Allowed) for HEAD
- GET always works (HTTP spec requirement)

**4. Why semaphore for concurrency?**
- Prevents overwhelming network/system resources
- Respects server rate limits
- Configurable based on environment

---

## Testing

### Run Unit Tests

```bash
pytest test_stats.py -v
```

### Test TCP Probe

```bash
python tcp_probe.py
```

### Test HTTP Probe

```bash
python http_probe.py
```

---

## Use Cases

### 1. CI/CD Integration

```bash
# In your CI pipeline
python main.py run --targets production_urls.txt --out report.json

# Exit code 0 = all SLOs passed
# Exit code 1 = SLO violations detected
```

### 2. Pre-Deployment Validation

```bash
# Smoke test new deployment
python main.py run --targets api_endpoints.txt --mode http --samples 20
```

### 3. Performance Monitoring

```bash
# Cron job every 5 minutes
*/5 * * * * cd /path/to/pingslo && python main.py run --targets urls.txt --out /var/log/slo_$(date +\%Y\%m\%d_\%H\%M).json
```

### 4. Debugging Network Issues

```bash
# Quick check if service is reachable
python main.py sample --url problematic-host.com --mode tcp --samples 20
```

---

## Troubleshooting

### All probes timeout
- Check network connectivity
- Verify firewall rules
- Try increasing `--timeout`
- Test with `ping` or `curl` first

### HTTP probes fail with SSL errors
- Server may have invalid/expired certificate
- Tool currently skips cert verification for monitoring
- Check server certificate separately if needed

### SLOs always failing
- Check if thresholds are realistic for probe mode
  - TCP: typically 10-100ms
  - HTTP: typically 100-1000ms
- Use `sample` command to establish baseline
- Adjust `config.yaml` thresholds

---

## Batch Files Reference (Windows)

PingSLO includes convenience batch files for Windows users:

### `setup.bat`
Automated environment setup - creates virtual environment and installs all dependencies.
```bash
setup.bat
```

### `run.bat`
Interactive menu-driven interface or command-line runner.

**Interactive Mode (No arguments):**
```bash
run.bat
```
Provides a user-friendly menu to:
- Select probe mode (TCP or HTTP)
- Enter target websites one at a time
- Configure number of samples
- Optionally save to JSON file
- Run multiple tests in sequence

**Command-Line Mode (With arguments):**
```bash
run.bat run --targets urls.txt --samples 10
run.bat sample --url google.com --samples 5
run.bat run --targets urls.txt --mode http --out report.json
```

**Benefits:**
- Interactive mode perfect for demos and quick testing
- No need to manually activate virtual environment
- No need to create target files for quick tests
- Automatic JSON file naming with timestamps
- Easy to use for non-technical users

---

## Changelog

### v0.1.0 (2025-10-14)
- Initial release
- TCP connection time probing
- HTTP TTFB probing with HEAD→GET fallback
- SLO evaluation with YAML config
- JSON report generation
- Concurrent probing with semaphore
- CLI with run/sample commands
- Unit tests for percentile calculations

---

## Contributing

This is a learning/interview project. Feel free to:
- Open issues for bugs or enhancements
- Submit pull requests
- Use as reference for your own projects

---

## License

MIT License - Free to use, modify, and distribute.

---

## FAQ

**Q: TCP vs HTTP mode - which should I use?**
A: 
- TCP = "Can I reach the server?" (connection only)
- HTTP = "How responsive is the application?" (full request/response)
- Use TCP for infrastructure monitoring, HTTP for application monitoring

**Q: Why are my HTTP p95 values 10x higher than TCP?**
A: Normal! HTTP includes TCP + TLS + HTTP processing. Set different SLO thresholds.

**Q: Can I monitor HTTPS endpoints with invalid certificates?**
A: Yes, the tool skips cert verification for monitoring purposes. In production, you should monitor cert validity separately.

**Q: How many samples should I use?**
A: 
- Quick check: 5-10 samples
- SLO evaluation: 20-50 samples
- Statistical accuracy: 100+ samples

**Q: What's a good concurrency limit?**
A: Default 5 is safe. Increase to 10-20 if monitoring many fast targets. Lower to 1-3 for slow/rate-limited targets.

---

## Future Enhancements

- [ ] HTML report generation
- [ ] Configurable SSL certificate verification
- [ ] HTTP authentication support (Bearer tokens, Basic auth)
- [ ] Custom HTTP headers
- [ ] UDP probing
- [ ] Metrics export (Prometheus format)
- [ ] Historical trending
- [ ] Alerting integrations (Slack, PagerDuty)
- [ ] Web dashboard

---

**Built as a learning project**
