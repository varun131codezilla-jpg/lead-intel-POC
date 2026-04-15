import requests
import json
import time
import socket
import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BRIGHT_DATA_API_TOKEN")
DATASET_ID = os.getenv("BRIGHT_DATA_DATASET_ID")

def dns_override():
    """
    Force api.brightdata.com to resolve to known IPs if DNS fails.
    """
    original_getaddrinfo = socket.getaddrinfo
    def patched_getaddrinfo(*args, **kwargs):
        if args[0] == 'api.brightdata.com':
            # Return the IPs we found via nslookup earlier
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('3.232.71.244', 443))]
        return original_getaddrinfo(*args, **kwargs)
    socket.getaddrinfo = patched_getaddrinfo
    print("Applied DNS override for api.brightdata.com")

def test_bright_data_live(linkedin_url):
    print(f"Testing Bright Data with Dataset ID: {DATASET_ID}")
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
    params = {"dataset_id": DATASET_ID, "include_errors": "true"}
    payload = [{"url": linkedin_url}]
    
    try:
        print("Attempting to trigger...")
        resp = requests.post(trigger_url, params=params, headers=headers, json=payload, timeout=30)
        
        if resp.status_code != 200:
            print(f"FAILED Trigger: {resp.status_code}")
            print(resp.text)
            return
            
        snapshot_id = resp.json().get("snapshot_id")
        print(f"SUCCESS Trigger! Snapshot ID: {snapshot_id}")
        
        # Poll for 60 seconds
        for i in range(12):
            time.sleep(5)
            progress_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
            p_resp = requests.get(progress_url, headers=headers, timeout=20)
            status = p_resp.json().get("status")
            print(f"Status: {status}")
            
            if status == "ready":
                print("Snapshot ready! Fetching data...")
                # Use the corrected URL (no /data)
                data_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
                d_resp = requests.get(data_url, headers=headers, timeout=30)
                if d_resp.status_code == 200:
                    data = d_resp.json()
                    print("DATA RECEIVED SUCCESSFULLY!")
                    print(json.dumps(data, indent=2)[:500] + "...")
                    return True
                else:
                    print(f"Data Fetch Failed: {d_resp.status_code}")
                    print(d_resp.text)
                    return
            elif status == "failed":
                print("Job failed in Bright Data.")
                return
                
    except Exception as e:
        print(f"Error during live test: {e}")
        if "NameResolutionError" in str(e) or "failed to resolve" in str(e).lower():
            print("\nDNS issue detected. Attempting to apply DNS override and retry...")
            dns_override()
            return test_bright_data_live(linkedin_url)
    return False

if __name__ == "__main__":
    test_url = "https://www.linkedin.com/company/elysian-capital-llp"
    test_bright_data_live(test_url)
