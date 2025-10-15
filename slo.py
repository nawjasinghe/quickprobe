"""slo service level objective evaluation"""
import yaml
from pathlib import Path


"""slo configuration with default and per-target thresholds"""
class SLOConfig:
    
    """load slo config from yaml file or use defaults"""
    def __init__(self, config_path=None):
        # sensible defaults for tcp probing
        # http probing needs higher thresholds
        self.default_slo = {
            'latency_p95_ms': 100.0,
            'latency_p99_ms': None,  # optional
            'max_loss_pct': 5.0,
        }
        self.target_slos = {}  # per-target overrides
        
        if config_path and Path(config_path).exists():
            self._load_config(config_path)
    
    """load config from yaml file"""
    def _load_config(self, config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # merge default_slo section if present
        if 'default_slo' in config:
            self.default_slo.update(config['default_slo'])
        
        # load per-target overrides
        if 'target_slos' in config:
            self.target_slos = config['target_slos']
    
    """get slo thresholds for specific host"""
    def get_slo(self, host):
        # check if this host has custom thresholds
        if host in self.target_slos:
            # start with defaults then apply overrides
            slo = self.default_slo.copy()
            slo.update(self.target_slos[host])
            return slo
        
        # use default thresholds
        return self.default_slo.copy()


"""evaluate if target meets its slo requirements"""
def evaluate_slo(result, slo_config):
    host = result['host']
    stats = result['stats']
    loss_pct = result['loss_pct']
    
    # get thresholds for this specific host
    slo = slo_config.get_slo(host)
    failures = []
    
    # cant evaluate if all probes failed
    if stats['p95_ms'] is None:
        failures.append("All probes failed - no data to evaluate")
        return {
            'passed': False,
            'failures': failures,
            'thresholds': slo,
        }
    
    # check p95 latency threshold
    if slo['latency_p95_ms'] is not None:
        if stats['p95_ms'] > slo['latency_p95_ms']:
            failures.append(
                f"p95 latency {stats['p95_ms']:.2f}ms exceeds "
                f"threshold {slo['latency_p95_ms']:.2f}ms"
            )
    
    # check p99 latency if its configured
    if slo['latency_p99_ms'] is not None:
        if stats['p99_ms'] > slo['latency_p99_ms']:
            failures.append(
                f"p99 latency {stats['p99_ms']:.2f}ms exceeds "
                f"threshold {slo['latency_p99_ms']:.2f}ms"
            )
    
    # check packet loss percentage
    if slo['max_loss_pct'] is not None:
        if loss_pct > slo['max_loss_pct']:
            failures.append(
                f"Loss {loss_pct:.1f}% exceeds "
                f"threshold {slo['max_loss_pct']:.1f}%"
            )
    
    # slo passes only if zero failures
    return {
        'passed': len(failures) == 0,
        'failures': failures,
        'thresholds': slo,
    }
