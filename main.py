"""pingslo - network slo monitoring tool"""
import argparse
import asyncio
import sys
from pathlib import Path
from runner import run_probes, print_results_table
from slo import SLOConfig, evaluate_slo
from report import generate_json_report, format_json_summary


"""parse targets file, return list of (host, port) tuples"""
def parse_targets_file(filepath):
    targets = []
    errors = []
    path = Path(filepath)
    
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    with path.open('r') as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            
            # skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            try:
                host, port = parse_target(line)
                targets.append((host, port))
            except ValueError as e:
                error_msg = f"Line {line_num}: {e}"
                errors.append(error_msg)
                print(f"Warning: {error_msg}")
                continue
    
    if not targets:
        print(f"\nError: No valid targets found in {filepath}")
        if errors:
            print(f"\nFound {len(errors)} error(s):")
            for err in errors[:5]:  # show first 5 errors
                print(f"  - {err}")
        sys.exit(1)
    
    if errors:
        print(f"\nWarning: Skipped {len(errors)} invalid target(s)")
    
    return targets


"""parse target string into (host, port)"""
def parse_target(target_str):
    # handle urls with protocol prefix
    if target_str.startswith('https://'):
        host = target_str[8:]  # strip https://
        default_port = 443
    elif target_str.startswith('http://'):
        host = target_str[7:]  # strip http://
        default_port = 80
    else:
        # no protocol, assume https
        host = target_str
        default_port = 443
    
    # remove trailing slashes and any path components
    host = host.rstrip('/')
    if '/' in host:
        # keep only hostname:port part, drop /path
        host = host.split('/')[0]
    
    # check if port is explicitly specified
    if ':' in host:
        parts = host.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid target format: {target_str}")
        host, port_str = parts
        try:
            port = int(port_str)
            # valid tcp port range
            if not (1 <= port <= 65535):
                raise ValueError(f"Port must be 1-65535: {port}")
        except ValueError:
            raise ValueError(f"Invalid port number: {port_str}")
    else:
        # no port specified, use default based on protocol
        port = default_port
    
    if not host:
        raise ValueError(f"Empty hostname in: {target_str}")
    
    return host, port


"""run command - probe multiple targets from file"""
async def cmd_run(args):
    # parse and validate targets file
    targets = parse_targets_file(args.targets)
    
    print(f"Loaded {len(targets)} target(s) from {args.targets}")
    
    # figure out which slo config to use
    slo_config = None
    if args.config:
        # user specified config file explicitly
        if Path(args.config).exists():
            slo_config = SLOConfig(args.config)
            print(f"Loaded SLO config from {args.config}")
        else:
            print(f"Warning: Config file not found: {args.config}, using defaults")
            slo_config = SLOConfig()
    else:
        # no --config flag, try default config.yaml in current dir
        if Path('config.yaml').exists():
            slo_config = SLOConfig('config.yaml')
            print(f"Loaded SLO config from config.yaml")
        else:
            # no config file found, use hardcoded defaults
            slo_config = SLOConfig()
            print(f"Using default SLO thresholds (p95<=100ms, loss<=5%)")
    
    # run all probes concurrently
    results = await run_probes(
        targets,
        num_probes=args.samples,
        timeout=args.timeout,
        interval=args.interval,
        max_concurrent=args.concurrent,
        mode=args.mode
    )
    
    # check each result against slo thresholds
    slo_evaluations = [evaluate_slo(r, slo_config) for r in results]
    
    # display results in nice table format
    print_results_table(results, slo_evaluations)
    
    # count how many passed vs failed
    passed = sum(1 for e in slo_evaluations if e['passed'])
    failed = len(slo_evaluations) - passed
    
    print(f"\nSLO Summary: {passed} passed, {failed} failed (out of {len(results)} targets)")
    
    # optionally save results to json file
    if args.out:
        # include run configuration in report metadata
        config_data = {
            'mode': args.mode,
            'samples': args.samples,
            'timeout': args.timeout,
            'interval': args.interval,
            'max_concurrent': args.concurrent,
        }
        generate_json_report(results, slo_evaluations, config_data, args.out)
        format_json_summary(args.out)
    
    # exit code matters for ci/cd pipelines
    # non-zero exit = build failure
    if failed > 0:
        print(f"\nSLO violations detected!")
        sys.exit(1)  # failure exit code
    else:
        print(f"\nAll SLOs passed!")
        sys.exit(0)  # success exit code


"""sample command - quick test of single url"""
async def cmd_sample(args):
    from runner import probe_target
    
    # validate url format
    try:
        host, port = parse_target(args.url)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print(f"Quick sample: {host}:{port} ({args.samples} probes, mode: {args.mode})\n")
    
    result = await probe_target(
        host, port,
        num_probes=args.samples,
        timeout=args.timeout,
        interval=args.interval,
        mode=args.mode
    )
    
    print_results_table([result])


"""cli entry point"""
def main():
    parser = argparse.ArgumentParser(
        prog='pingslo',
        description='Network SLO monitoring tool - measure latency and availability',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Probe targets from file (TCP mode)
  python main.py run --targets urls.txt --samples 10

  # Quick test of single URL
  python main.py sample --url google.com --samples 5

  # Custom settings
  python main.py run --targets urls.txt --samples 20 --timeout 10 --concurrent 10
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    subparsers.required = True
    
    # run command
    run_parser = subparsers.add_parser('run', help='Probe multiple targets from a file')
    run_parser.add_argument(
        '--targets',
        required=True,
        help='Path to targets file (one target per line)'
    )
    run_parser.add_argument(
        '--config',
        help='Path to config.yaml with SLO thresholds (default: config.yaml if exists)'
    )
    run_parser.add_argument(
        '--mode',
        choices=['tcp', 'http'],
        default='tcp',
        help='Probe mode: tcp (connection time) or http (TTFB). Default: tcp'
    )
    run_parser.add_argument(
        '--samples',
        type=int,
        default=10,
        help='Number of probes per target. Default: 10'
    )
    run_parser.add_argument(
        '--timeout',
        type=float,
        default=5.0,
        help='Timeout per probe in seconds. Default: 5.0'
    )
    run_parser.add_argument(
        '--interval',
        type=float,
        default=0.5,
        help='Delay between probes in seconds. Default: 0.5'
    )
    run_parser.add_argument(
        '--concurrent',
        type=int,
        default=5,
        help='Max concurrent targets to probe. Default: 5'
    )
    run_parser.add_argument(
        '--out',
        help='Output JSON report file path (e.g., report.json)'
    )
    
    # sample command
    sample_parser = subparsers.add_parser('sample', help='Quick test of a single URL')
    sample_parser.add_argument(
        '--url',
        required=True,
        help='URL or hostname to test (e.g., google.com or https://example.com)'
    )
    sample_parser.add_argument(
        '--mode',
        choices=['tcp', 'http'],
        default='tcp',
        help='Probe mode: tcp (connection time) or http (TTFB). Default: tcp'
    )
    sample_parser.add_argument(
        '--samples',
        type=int,
        default=5,
        help='Number of probes. Default: 5'
    )
    sample_parser.add_argument(
        '--timeout',
        type=float,
        default=5.0,
        help='Timeout per probe in seconds. Default: 5.0'
    )
    sample_parser.add_argument(
        '--interval',
        type=float,
        default=0.5,
        help='Delay between probes in seconds. Default: 0.5'
    )
    
    args = parser.parse_args()
    
    # route to command handler
    if args.command == 'run':
        asyncio.run(cmd_run(args))
    elif args.command == 'sample':
        asyncio.run(cmd_sample(args))


if __name__ == '__main__':
    main()
