"""
Verify proxies are working and check what IPs they resolve to.
Then test Chanel through NST proxy (different provider).
"""
import requests

# Check our real IP
def check_ip(label, proxy=None):
    print(f"\n--- {label} ---")
    try:
        kwargs = {"url": "https://httpbin.org/ip", "timeout": 15}
        if proxy:
            kwargs["proxies"] = {"https": proxy, "http": proxy}
        resp = requests.get(**kwargs)
        print(f"  IP: {resp.json()}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Get NST proxy credentials
def get_nst_proxy(channel_id):
    token = "NSTPROXY-DA9C7A614946EA8FCEFDA9FD3B3F4A9D"
    api_url = f"https://api.nstproxy.com/api/v1/generate/apiproxies?count=1&country=US&protocol=http&sessionDuration=0&channelId={channel_id}&token={token}"
    print(f"\nFetching NST proxy ({channel_id[:8]}...):")
    print(f"  URL: {api_url}")
    try:
        resp = requests.get(api_url, timeout=15)
        print(f"  HTTP {resp.status_code}")
        print(f"  Body: {resp.text[:500]}")
        data = resp.json()
        if data.get("code") == 200 and data.get("data"):
            proxy_str = data["data"][0]
            parts = proxy_str.split(":")
            if len(parts) == 4:
                ip, port, user, pwd = parts
                proxy_url = f"http://{user}:{pwd}@{ip}:{port}"
                print(f"  Proxy URL: http://{user[:10]}...@{ip}:{port}")
                return proxy_url
    except Exception as e:
        print(f"  ERROR: {e}")
    return None

# Test Chanel
def test_chanel(label, proxy=None, use_cffi=False):
    url = "https://www.chanel.com/us/fashion/handbags/c/1x1x1/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    try:
        if use_cffi:
            from curl_cffi import requests as cffi_requests
            kwargs = {"url": url, "headers": headers, "impersonate": "chrome", "timeout": 30, "allow_redirects": True}
            if proxy:
                kwargs["proxies"] = {"https": proxy, "http": proxy}
            resp = cffi_requests.get(**kwargs)
        else:
            kwargs = {"url": url, "headers": headers, "timeout": 30, "allow_redirects": True}
            if proxy:
                kwargs["proxies"] = {"https": proxy, "http": proxy}
            resp = requests.get(**kwargs)

        blocked = "Access Denied" in resp.text
        print(f"  Status: {resp.status_code}")
        print(f"  Size: {len(resp.text):,} bytes")
        print(f"  Result: {'BLOCKED' if blocked else 'SUCCESS' if resp.status_code == 200 and len(resp.text) > 10000 else 'UNCLEAR'}")
        if not blocked and resp.status_code == 200:
            print(f"  First 300 chars: {resp.text[:300]}")
    except Exception as e:
        print(f"  ERROR: {e}")


if __name__ == "__main__":
    MASSIVE_RES = "https://mpuQHs4sWZ-country-US:D0yWxVQo8wQ05RWqz1Bn@network.joinmassive.com:65535"
    MASSIVE_DC = "http://mpuQHs4sWZ-country-US:D0yWxVQo8wQ05RWqz1Bn@isp.joinmassive.com:8000"

    # Step 1: Verify IPs
    print("="*60)
    print("STEP 1: Verify proxy IPs")
    check_ip("Direct (Hetzner)")
    check_ip("Massive Residential", MASSIVE_RES)
    check_ip("Massive Datacenter/ISP", MASSIVE_DC)

    # Step 2: Get NST proxies
    print("\n" + "="*60)
    print("STEP 2: Get NST proxy credentials")
    nst_res = get_nst_proxy("7864DDA266D5899C")  # residential
    nst_dc = get_nst_proxy("AE0C3B5547F8A021")   # datacenter

    if nst_res:
        check_ip("NST Residential", nst_res)
    if nst_dc:
        check_ip("NST Datacenter", nst_dc)

    # Step 3: Test Chanel with all available proxies
    print("\n" + "="*60)
    print("STEP 3: Test Chanel.com")

    if nst_res:
        test_chanel("curl_cffi + NST residential", proxy=nst_res, use_cffi=True)
        test_chanel("plain requests + NST residential", proxy=nst_res, use_cffi=False)

    if nst_dc:
        test_chanel("curl_cffi + NST datacenter", proxy=nst_dc, use_cffi=True)

    # Also try Massive ISP/datacenter (different from residential)
    test_chanel("curl_cffi + Massive ISP", proxy=MASSIVE_DC, use_cffi=True)
