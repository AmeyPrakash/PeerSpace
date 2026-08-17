"""
PeerSpace Security Audit: Security Headers, Input Validation & Rate Limiting
"""

import urllib.request
import urllib.error
import json
import time
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"

def run_security_tests():
    print("=" * 65)
    print(" RUNNING PEERSPACE COMPREHENSIVE SECURITY TEST SUITE")
    print("=" * 65)

    passed_count = 0
    total_tests = 0

    # -------------------------------------------------------------
    # Test 1: Security Headers on Static Endpoints
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 1] Checking HTTP Security Headers...")
    try:
        res = urllib.request.urlopen(f"{BASE_URL}/")
        headers = dict(res.headers)
        
        has_nosniff = headers.get("x-content-type-options") == "nosniff"
        has_frame_deny = headers.get("x-frame-options") == "DENY"
        has_csp = "content-security-policy" in headers
        has_referrer = "referrer-policy" in headers

        if has_nosniff and has_frame_deny and has_csp and has_referrer:
            print("  [PASSED] All security headers (CSP, nosniff, DENY, referrer) present.")
            passed_count += 1
        else:
            print(f"  [FAILED] Missing headers. Headers found: {headers}")
    except Exception as e:
        print(f"  [FAILED] {e}")

    # -------------------------------------------------------------
    # Test 2: Input Validation - Reject Empty Message
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 2] Input Validation: Empty / Whitespace payload rejection...")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/chat",
            data=json.dumps({"message": "   "}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req)
        print("  [FAILED] Server accepted empty whitespace message.")
    except urllib.error.HTTPError as e:
        if e.code == 422 or e.code == 400:
            print(f"  [PASSED] Server rejected empty payload with status {e.code}.")
            passed_count += 1
        else:
            print(f"  [WARNING] Unexpected status code: {e.code}")

    # -------------------------------------------------------------
    # Test 3: Input Validation - Malicious / Invalid Session ID Format
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 3] Input Validation: Malicious session_id rejection (XSS/Path Traversal)...")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/chat",
            data=json.dumps({
                "message": "Hello coach",
                "session_id": "../../etc/passwd<script>alert(1)</script>"
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req)
        print("  [FAILED] Server accepted invalid session_id.")
    except urllib.error.HTTPError as e:
        if e.code == 422 or e.code == 400:
            print(f"  [PASSED] Server rejected invalid session_id with status {e.code}.")
            passed_count += 1
        else:
            print(f"  [WARNING] Unexpected status code: {e.code}")

    # -------------------------------------------------------------
    # Test 4: Prompt Sanitization & Safe Response
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 4] Sanitization: Null bytes & control characters in prompt...")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/chat",
            data=json.dumps({
                "message": "Hey coach \x00\x08 I am feeling anxious about finals \x1f",
                "session_id": "clean-session-sec-1"
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        if "reply" in data and len(data["reply"]) > 0:
            print("  [PASSED] Message processed cleanly and securely.")
            passed_count += 1
        else:
            print("  [FAILED] Empty reply.")
    except Exception as e:
        print(f"  [FAILED] {e}")

    # -------------------------------------------------------------
    # Test 5: Rate Limiting
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 5] Rate Limiter: Testing flood request rejection (HTTP 429)...")
    rate_limited = False
    rate_session = "flood-test-session"
    for i in range(35):
        try:
            req = urllib.request.Request(
                f"{BASE_URL}/api/reset",
                data=json.dumps({"session_id": rate_session}).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                rate_limited = True
                break
        time.sleep(0.01)
    
    if rate_limited:
        print("  [PASSED] Flood requests triggered HTTP 429 (Rate Limit Exceeded).")
        passed_count += 1
    else:
        print("  [FAILED] Rate limit threshold was not triggered.")

    print("\n" + "=" * 65)
    print(f" SECURITY AUDIT COMPLETED: {passed_count}/{total_tests} tests passed.")
    print("=" * 65)

if __name__ == "__main__":
    run_security_tests()
