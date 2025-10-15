"""tcp connection time probing"""
import asyncio
import time


"""measure tcp connection time in milliseconds"""
async def tcp_probe(host, port=443, timeout=5.0):
    # start timer before connection attempt
    start = time.perf_counter()
    
    try:
        # asyncio.open_connection does tcp handshake (SYN, SYN-ACK, ACK)
        # wait_for wraps it with timeout to avoid hanging forever
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        
        # stop timer as soon as connection succeeds
        elapsed = time.perf_counter() - start
        elapsed_ms = elapsed * 1000
        
        # cleanup - close socket immediately since we dont need it
        writer.close()
        await writer.wait_closed()
        
        return elapsed_ms
        
    except asyncio.TimeoutError:
        # took too long, count as failure
        return None
    except OSError as e:
        # connection refused, network unreachable, dns failure, etc
        print(f"  Error connecting to {host}:{port} - {e}")
        return None
