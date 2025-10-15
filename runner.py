"""multi-target probe runner"""
import asyncio
from tcp_probe import tcp_probe
from http_probe import http_probe_with_fallback
from stats import compute_stats


"""probe a single target multiple times"""
async def probe_target(host, port=443, num_probes=10, timeout=5.0, interval=0.5, semaphore=None, mode='tcp'):
    # semaphore limits how many targets probe simultaneously
    # prevents overwhelming network or target servers
    if semaphore:
        async with semaphore:
            return await _probe_target_impl(host, port, num_probes, timeout, interval, mode)
    else:
        # no concurrency control
        return await _probe_target_impl(host, port, num_probes, timeout, interval, mode)


"""internal probe implementation"""
async def _probe_target_impl(host, port, num_probes, timeout, interval, mode):
    print(f"  Probing {host}:{port} ({num_probes} samples, mode: {mode})...")
    
    latencies = []  # successful probe times
    failures = 0    # count of timeouts and errors
    
    # run num_probes measurements
    for i in range(num_probes):
        # pick tcp or http based on mode
        if mode == 'http':
            # construct url from host and port
            scheme = 'https' if port == 443 else 'http'
            url = f"{scheme}://{host}:{port}"
            result, method = await http_probe_with_fallback(url, timeout)
        else:
            # default tcp mode
            result = await tcp_probe(host, port, timeout)
        
        # collect successful measurement or count failure
        if result is not None:
            latencies.append(result)
        else:
            failures += 1
        
        # pause between probes to avoid hammering target
        if i < num_probes - 1:
            await asyncio.sleep(interval)
    
    # compute stats from successful measurements
    stats = compute_stats(latencies)
    loss_pct = (failures / num_probes) * 100
    
    return {
        'host': host,
        'port': port,
        'stats': stats,
        'loss_pct': loss_pct,
    }


"""probe multiple targets concurrently with semaphore"""
async def run_probes(targets, num_probes=10, timeout=5.0, interval=0.5, max_concurrent=5, mode='tcp'):
    print(f"Starting {mode.upper()} probes for {len(targets)} target(s) "
          f"(max {max_concurrent} concurrent)...\n")
    
    # semaphore acts like a ticket system - only max_concurrent tasks get tickets
    # prevents spawning 100+ simultaneous connections
    semaphore = asyncio.Semaphore(max_concurrent)
    
    # create task for each target
    tasks = [
        probe_target(host, port, num_probes, timeout, interval, semaphore, mode)
        for host, port in targets
    ]
    
    # asyncio.gather runs all tasks concurrently and waits for all to finish
    # returns results in same order as targets list
    results = await asyncio.gather(*tasks)
    
    return results


"""print ascii table of results"""
def print_results_table(results, slo_evaluations=None):
    print("\n" + "="*90)
    print("RESULTS")
    print("="*90)
    
    # header changes based on whether we have slo data
    if slo_evaluations:
        print(f"{'Target':<30} {'Avg (ms)':<12} {'P95 (ms)':<12} {'P99 (ms)':<12} {'Loss %':<10} {'SLO':<8}")
        print("-"*90)
    else:
        print(f"{'Target':<30} {'Avg (ms)':<12} {'P95 (ms)':<12} {'P99 (ms)':<12} {'Loss %':<10}")
        print("-"*90)
    
    # print each target as a row
    for i, r in enumerate(results):
        target = f"{r['host']}:{r['port']}"
        stats = r['stats']
        loss = r['loss_pct']
        
        # show "FAILED" if we got zero successful probes
        if stats['avg_ms'] is None:
            avg_str = "FAILED"
            p95_str = "FAILED"
            p99_str = "FAILED"
        else:
            # format numbers with 2 decimal places
            avg_str = f"{stats['avg_ms']:.2f}"
            p95_str = f"{stats['p95_ms']:.2f}"
            p99_str = f"{stats['p99_ms']:.2f}"
        
        # if we have slo evaluations, add pass/fail column
        if slo_evaluations:
            slo_eval = slo_evaluations[i]
            slo_str = "PASS" if slo_eval['passed'] else "FAIL"
            
            print(f"{target:<30} {avg_str:<12} {p95_str:<12} {p99_str:<12} {loss:.1f}%{'':<6} {slo_str}")
            
            # indent failure reasons under the row
            if not slo_eval['passed']:
                for failure in slo_eval['failures']:
                    print(f"  ! {failure}")
        else:
            # no slo data, just print stats
            print(f"{target:<30} {avg_str:<12} {p95_str:<12} {p99_str:<12} {loss:.1f}%")
    
    print("="*90)


"""test runner with known hosts"""
async def test_multi_target():
    targets = [
        ("google.com", 443),
        ("github.com", 443),
        ("cloudflare.com", 443),
    ]
    
    results = await run_probes(targets, num_probes=10, interval=0.3)
    print_results_table(results)


if __name__ == "__main__":
    asyncio.run(test_multi_target())
