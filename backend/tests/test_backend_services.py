import sys
import time
import urllib.request
import urllib.error
import urllib.parse
import json

BASE_URL = "http://localhost:8000"

def green(text):
    return f"\033[92m{text}\033[0m"

def red(text):
    return f"\033[91m{text}\033[0m"

def check_endpoint(name, url):
    print(f"Checking {name} ({url})...", end=" ")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            status = response.status
            data = json.loads(response.read().decode())
            
            if status == 200:
                print(green("OK"))
                return True, data
            else:
                print(red(f"FAILED (Status: {status})"))
                return False, data
    except urllib.error.URLError as e:
        print(red(f"FAILED (Error: {e})"))
        return False, None
    except Exception as e:
        print(red(f"FAILED (Exception: {e})"))
        return False, None

def main():
    print(f"Starting Backend Service Verification against {BASE_URL}\n")
    
    # 1. Check Root
    ok, data = check_endpoint("Root", f"{BASE_URL}/")
    if ok:
        print(f"  App Name: {data.get('name')}")
        print(f"  Status: {data.get('status')}")
    else:
        print("  Could not connect to backend. Is it running?")
        sys.exit(1)

    print("-" * 30)

    # 2. Check Health (DB & Redis)
    ok, data = check_endpoint("Health", f"{BASE_URL}/health")
    if ok:
        db_status = data.get("database")
        redis_status = data.get("redis")
        
        if db_status == "healthy":
            print(f"  Database: {green(db_status)}")
        else:
            print(f"  Database: {red(db_status)}")
            
        if redis_status == "healthy":
            print(f"  Redis: {green(redis_status)}")
        else:
            print(f"  Redis: {red(redis_status)}")
            
        if db_status != "healthy" or redis_status != "healthy":
            print(red("\nOne or more services are unhealthy!"))
            # Don't exit yet, check other endpoints
            
    print("-" * 30)

    # 3. Check API Routes
    endpoints = [
        ("/api/v1/stocks", "Stocks API"), # This might need a trailing slash or specific endpoint
        ("/docs", "API Documentation"),
    ]
    
    for path, name in endpoints:
        check_endpoint(name, f"{BASE_URL}{path}")

    # 4. Check specific logical endpoints (using a safe method if possible, or just checking 404 vs 401/200)
    # We'll check /api/v1/stocks/ (list) usually
    print("-" * 30)
    print("Checking Stocks Listing...")
    ok, _ = check_endpoint("Stocks List", f"{BASE_URL}/api/v1/stocks/") 
    if not ok:
         # Try without trailing slash if redirects aren't handled auto by urllib
         check_endpoint("Stocks List (no slash)", f"{BASE_URL}/api/v1/stocks")

if __name__ == "__main__":
    main()
