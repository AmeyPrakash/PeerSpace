"""
PeerSpace WebRTC Signaling & Voice Matchmaking Tests
"""

import asyncio
import json
import websockets
import urllib.request
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

WS_URL = "ws://127.0.0.1:8000/ws/voice-room"
HTTP_URL = "http://127.0.0.1:8000"

async def run_voice_test():
    print("=" * 70)
    print(" TESTING STUDENT-TO-STUDENT ANONYMOUS WEBRTC VOICE MATCHMAKING")
    print("=" * 70)

    passed_count = 0
    total_tests = 0

    # -------------------------------------------------------------
    # Test 1: First student connects and enters waiting queue
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 1] Student A connects to voice room...")
    async with websockets.connect(f"{WS_URL}?session_id=student-a-123&alias=MindfulFalcon11") as ws_a:
        msg_a1 = json.loads(await ws_a.recv())
        print("  Received:", msg_a1)
        if msg_a1.get("type") == "waiting":
            print("  [PASSED] Student A entered matchmaking queue successfully.")
            passed_count += 1
        else:
            print("  [FAILED] Unexpected first message:", msg_a1)

        # ---------------------------------------------------------
        # Test 2: Second student connects and instant match occurs
        # ---------------------------------------------------------
        total_tests += 1
        print("\n[Test 2] Student B connects and matches with Student A...")
        async with websockets.connect(f"{WS_URL}?session_id=student-b-456&alias=QuietComet99") as ws_b:
            match_a = json.loads(await ws_a.recv())
            match_b = json.loads(await ws_b.recv())

            print("  Student A match notification:", match_a)
            print("  Student B match notification:", match_b)

            if (match_a.get("type") == "matched" and 
                match_b.get("type") == "matched" and 
                match_a.get("peer_alias") == "QuietComet99" and 
                match_b.get("peer_alias") == "MindfulFalcon11"):
                print("  [PASSED] Both students matched into private anonymous voice room!")
                passed_count += 1
            else:
                print("  [FAILED] Matching payload mismatch.")

            # -----------------------------------------------------
            # Test 3: WebRTC SDP & ICE Signal Relaying
            # -----------------------------------------------------
            total_tests += 1
            print("\n[Test 3] Testing WebRTC Offer/Answer relay...")
            dummy_offer = {"type": "offer", "offer": {"sdp": "v=0\r\no=dummy", "type": "offer"}}
            await ws_a.send(json.dumps(dummy_offer))

            relayed_offer = json.loads(await ws_b.recv())
            if relayed_offer.get("type") == "offer" and "sdp" in relayed_offer.get("offer", {}):
                print("  [PASSED] Offer relayed to Student B successfully.")
                passed_count += 1
            else:
                print("  [FAILED] Offer not relayed correctly:", relayed_offer)

    # -------------------------------------------------------------
    # Test 4: Voice Call Counselor Emergency Escalation API
    # -------------------------------------------------------------
    total_tests += 1
    print("\n[Test 4] Voice Call Counselor Emergency Escalation API...")
    try:
        req = urllib.request.Request(
            f"{HTTP_URL}/api/voice/escalate",
            data=json.dumps({
                "session_id": "student-a-123",
                "alias": "MindfulFalcon11",
                "peer_alias": "QuietComet99",
                "reason": "Peer student sounds in severe distress and asked for crisis help."
            }).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))

        if data.get("status") == "success" and "alert_id" in data:
            print(f"  [PASSED] Counselor Alert generated from live voice call (Alert ID: {data['alert_id']})")
            passed_count += 1
        else:
            print("  [FAILED] Unexpected response:", data)
    except Exception as e:
        print(f"  [FAILED] {e}")

    print("\n" + "=" * 70)
    print(f" VOICE TEST COMPLETED: {passed_count}/{total_tests} tests passed.")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_voice_test())
