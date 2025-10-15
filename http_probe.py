"""http ttfb time to first byte probing"""
import asyncio
import time
import aiohttp
import ssl


"""measure http ttfb in milliseconds"""
async def http_probe(url, timeout=5.0, method='HEAD'):
    # start timer before http request
    start = time.perf_counter()
    
    # disable ssl verification because we only care about timing not security
    # in production monitoring you might want real certs
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.request(method, url, ssl=ssl_context) as response:
                # read just 1 byte to measure time to first byte
                # dont download whole response body
                await response.content.read(1)
                
                # stop timer once first byte arrives
                elapsed = time.perf_counter() - start
                elapsed_ms = elapsed * 1000
                
                return elapsed_ms
    
    except asyncio.TimeoutError:
        # server too slow or network issue
        return None
    except aiohttp.ClientError as e:
        # http errors like 404, connection refused, dns failure
        print(f"  Error probing {url} - {type(e).__name__}: {e}")
        return None
    except Exception as e:
        # catch anything else unexpected
        print(f"  Unexpected error probing {url} - {type(e).__name__}: {e}")
        return None


"""try head request first then fallback to get if needed"""
async def http_probe_with_fallback(url, timeout=5.0):
    # head is faster and uses less bandwith (no body)
    # but some servers dont support it
    result = await http_probe(url, timeout, method='HEAD')
    
    if result is not None:
        return result, 'HEAD'
    
    # some servers reject head requests so try get as fallback
    result = await http_probe(url, timeout, method='GET')
    
    if result is not None:
        return result, 'GET'
    
    # both failed
    return None, 'FAILED'
