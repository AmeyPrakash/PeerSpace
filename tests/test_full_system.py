"""
PeerSpace End-to-End System & Counselor Intervention Tests
"""

import urllib.request
import urllib.error
import json
import time
import sys
import os

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 70)
    print(" RUNNING PEERSPACE FULL SYSTEM & INTERVENTION TEST SUITE")
    print("=" * 70)

    passed_count = 0
    total_tests = 0

    # -------------------------------------------------------------
    # 0. Health Check Endpoint
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 0] System Health Check...")
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/health")
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        if data.get("status") == "healthy":
            print(f"  [PASSED] Service is healthy: {data}")
            passed_count += 1
        else:
            print(f"  [FAILED] Unhealthy status: {data}")
    except Exception as e:
        print(f"  [FAILED] Health check error: {e}")

    # -------------------------------------------------------------
    # 1. Anonymous Student Authentication & Alias Setup
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 1] Student Anonymous Authentication & Alias Setup...")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/student",
            data=json.dumps({"alias": "MindfulFalcon88"}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        
        if data.get("alias") == "MindfulFalcon88" and "session_id" in data:
            print(f"  [PASSED] Anonymous alias created: {data['alias']} (Session: {data['session_id'][:8]}...)")
            passed_count += 1
            student_session_id = data["session_id"]
        else:
            print(f"  [FAILED] Unexpected response: {data}")
            student_session_id = "test-session-fallback"
    except Exception as e:
        print(f"  [FAILED] {e}")
        student_session_id = "test-session-fallback"

    # -------------------------------------------------------------
    # 1b. Anonymous Student Alias Randomization (Click randomize)
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 1b] Student Anonymous Alias Randomization...")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/student",
            data=json.dumps({"session_id": student_session_id, "randomize": True}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        new_alias = data.get("alias")
        if new_alias and new_alias != "MindfulFalcon88" and data.get("session_id") == student_session_id:
            print(f"  [PASSED] Alias successfully randomized: {new_alias} (Previous: MindfulFalcon88)")
            passed_count += 1
        else:
            print(f"  [FAILED] Alias randomization failed: {data}")
    except Exception as e:
        print(f"  [FAILED] {e}")

    # -------------------------------------------------------------
    # 2. Student Chat (Normal Stress / Slang Mirroring)
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 2] Student Space: Normal Chat interaction...")
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/chat",
            data=json.dumps({
                "message": "Hey coach, ngl I am feeling burnt out from organic chemistry",
                "session_id": student_session_id,
                "alias": "MindfulFalcon88"
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        
        if "reply" in data and len(data["reply"]) > 0:
            print(f"  [PASSED] Peer coach replied: \"{data['reply']}\"")
            passed_count += 1
        else:
            print("  [FAILED] Empty reply.")
    except Exception as e:
        print(f"  [FAILED] {e}")

    # -------------------------------------------------------------
    # 3. AI-Driven Professional Intervention Trigger (Acute Crisis)
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 3] AI Intervention Call: Acute crisis trigger test...")
    try:
        crisis_session_id = "crisis-trigger-session-99"
        req = urllib.request.Request(
            f"{BASE_URL}/api/chat",
            data=json.dumps({
                "message": "I feel hopeless and I want to end my life, please help",
                "session_id": crisis_session_id,
                "alias": "DesperateStudent"
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        
        print(f"  Peer Coach Support Reply: \"{data['reply']}\"")
        
        alerts_req = urllib.request.Request(f"{BASE_URL}/api/admin/alerts")
        alerts_res = urllib.request.urlopen(alerts_req)
        alerts_data = json.loads(alerts_res.read().decode('utf-8'))
        
        found_alert = any("end my life" in str(a.get("reason", "")).lower() or a.get("severity") == "CRITICAL" for a in alerts_data.get("alerts", []))
        
        if found_alert:
            print(f"  [PASSED] AI automatically generated a CRITICAL Counselor Alert! (Total Alerts: {alerts_data['total_alerts']})")
            passed_count += 1
            latest_alert_id = alerts_data["alerts"][0]["id"]
        else:
            print(f"  [FAILED] Counselor alert not found in queue: {alerts_data}")
            latest_alert_id = None
    except Exception as e:
        print(f"  [FAILED] {e}")
        latest_alert_id = None

    # -------------------------------------------------------------
    # 4. Counselor / Admin Portal Authentication
    # Note: This test uses the COUNSELOR_PASSKEY from environment/config
    # For testing, ensure you set COUNSELOR_PASSKEY in your .env file
    # Example: COUNSELOR_PASSKEY=test_counselor_passkey_12345
    total_tests += 1
    print("\n[Test 4] Counselor Portal: Admin Passkey Authentication...")
    
    # For testing, use a test passkey (in production, this would be from secure config)
    # This is intentionally NOT the production passkey for security
    test_counselor_passkey = os.getenv("COUNSELOR_PASSKEY", "test_passkey_for_unit_tests")
    
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/admin",
            data=json.dumps({"passkey": test_counselor_passkey}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        
        if data.get("status") == "authenticated" and "token" in data:
            print(f"  [PASSED] Counselor authenticated successfully (Token: {data['token']})")
            passed_count += 1
        else:
            print(f"  [FAILED] Auth failed: {data}")
    except Exception as e:
        print(f"  [FAILED] {e}")

    # -------------------------------------------------------------
    # 5. Counselor Action: Dispatch Professional Intervention
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 5] Counselor Portal: 1-Click Dispatch Action...")
    if latest_alert_id:
        try:
            req = urllib.request.Request(
                f"{BASE_URL}/api/admin/alerts/{latest_alert_id}/action",
                data=json.dumps({"action": "DISPATCHED"}).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            res = urllib.request.urlopen(req)
            data = json.loads(res.read().decode('utf-8'))
            
            if data.get("new_status") == "DISPATCHED":
                print(f"  [PASSED] Intervention status updated to DISPATCHED for alert #{latest_alert_id}")
                passed_count += 1
            else:
                print(f"  [FAILED] {data}")
        except Exception as e:
            print(f"  [FAILED] {e}")
    else:
        print("  [WARNING] Skipped Test 5 due to missing alert ID.")

    # -------------------------------------------------------------
    # 6. Active Anonymous Sessions Monitor
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 6] Counselor Portal: Active Anonymous Sessions List...")
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/admin/sessions")
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        
        if data.get("total_active", 0) > 0 and len(data.get("active_sessions", [])) > 0:
            print(f"  [PASSED] Active sessions retrieved ({data['total_active']} active students monitored)")
            passed_count += 1
        else:
            print(f"  [FAILED] No active sessions returned: {data}")
    except Exception as e:
        print(f"  [FAILED] {e}")

    print("\n" + "=" * 70)
    print(f" SYSTEM TEST COMPLETED: {passed_count}/{total_tests} tests passed.")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
