#!/usr/bin/env python3
"""
VIP Scheduling - Test THREE NEW features:
1. Recurring availability
2. Reschedule
3. Auto-complete
"""
import requests
import pymongo
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')
frontend_env = Path(__file__).parent / "frontend" / ".env"
load_dotenv(frontend_env)

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") + "/api"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

print(f"BASE_URL: {BASE_URL}")
print(f"MONGO_URL: {MONGO_URL}")
print(f"DB_NAME: {DB_NAME}")

# MongoDB client
mongo_client = pymongo.MongoClient(MONGO_URL)
db = mongo_client[DB_NAME]

def register_user(email, password, name):
    """Register a new user"""
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": password,
        "name": name,
        "gender": "female",
        "age": 25,
        "interested_in": "male",
        "city": "New York",
        "country": "USA"
    })
    print(f"Register {email}: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        return data["token"], data["user"]["id"]
    else:
        print(f"Register failed: {resp.text}")
        return None, None

def setup_users():
    """Setup two users A and B"""
    # Generate unique emails
    import uuid
    suffix = str(uuid.uuid4())[:8]
    email_a = f"vip_user_a_{suffix}@example.com"
    email_b = f"regular_user_b_{suffix}@example.com"
    
    # Register users
    token_a, user_id_a = register_user(email_a, "password123", "VIP User A")
    token_b, user_id_b = register_user(email_b, "password123", "Regular User B")
    
    if not token_a or not token_b:
        raise Exception("Failed to register users")
    
    # Set A as VIP with far-future vip_until
    db.users.update_one(
        {"id": user_id_a},
        {"$set": {"vip_until": "2030-01-01T00:00:00+00:00"}}
    )
    
    # Give both users 5000 coins
    db.users.update_one({"id": user_id_a}, {"$set": {"coins": 5000}})
    db.users.update_one({"id": user_id_b}, {"$set": {"coins": 5000}})
    
    print(f"✅ Setup complete:")
    print(f"  User A (VIP): {user_id_a}")
    print(f"  User B: {user_id_b}")
    
    return {
        "a": {"token": token_a, "id": user_id_a, "email": email_a},
        "b": {"token": token_b, "id": user_id_b, "email": email_b}
    }

def test_recurring_availability(users):
    """FEATURE 1: Test recurring availability"""
    print("\n" + "="*80)
    print("FEATURE 1: RECURRING AVAILABILITY")
    print("="*80)
    
    token_a = users["a"]["token"]
    token_b = users["b"]["token"]
    user_id_a = users["a"]["id"]
    
    # Test 1: VIP user creates recurring availability for Saturdays and Sundays (weekdays 5,6)
    print("\n[TEST 1.1] VIP creates recurring availability for Sat/Sun, 18:00-22:00, 60-min slots, 4 weeks")
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/availability/recurring",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "weekdays": [5, 6],  # Saturday=5, Sunday=6
            "start": "18:00",
            "end": "22:00",
            "slot_len": 60,
            "weeks": 4
        }
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    
    if resp.status_code != 200:
        print("❌ FAILED: Expected 200")
        return False
    
    data = resp.json()
    if data["created"] <= 0:
        print("❌ FAILED: Expected created > 0")
        return False
    
    # Verify all blocks are on Saturday or Sunday
    blocks = data["blocks"]
    print(f"Created {len(blocks)} blocks")
    
    for block in blocks:
        date_obj = datetime.strptime(block["date"], "%Y-%m-%d")
        weekday = date_obj.weekday()
        if weekday not in [5, 6]:
            print(f"❌ FAILED: Block on wrong weekday: {block['date']} (weekday={weekday})")
            return False
        if block["start"] != "18:00" or block["end"] != "22:00" or block["slot_len"] != 60:
            print(f"❌ FAILED: Block has wrong time/slot_len: {block}")
            return False
    
    print("✅ PASSED: All blocks on Sat/Sun with correct times")
    
    # Test 2: Non-VIP user tries to create recurring availability
    print("\n[TEST 1.2] Non-VIP user tries to create recurring availability")
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/availability/recurring",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "weekdays": [5, 6],
            "start": "18:00",
            "end": "22:00",
            "slot_len": 60,
            "weeks": 4
        }
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    
    if resp.status_code != 403:
        print("❌ FAILED: Expected 403 VIP_REQUIRED")
        return False
    
    if "VIP_REQUIRED" not in resp.json().get("detail", ""):
        print("❌ FAILED: Expected detail=VIP_REQUIRED")
        return False
    
    print("✅ PASSED: Non-VIP correctly rejected with 403 VIP_REQUIRED")
    
    # Test 3: Empty weekdays
    print("\n[TEST 1.3] VIP with empty weekdays")
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/availability/recurring",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "weekdays": [],
            "start": "18:00",
            "end": "22:00",
            "slot_len": 60,
            "weeks": 4
        }
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    
    if resp.status_code != 400:
        print("❌ FAILED: Expected 400 NO_WEEKDAYS")
        return False
    
    if "NO_WEEKDAYS" not in resp.json().get("detail", ""):
        print("❌ FAILED: Expected detail=NO_WEEKDAYS")
        return False
    
    print("✅ PASSED: Empty weekdays correctly rejected with 400 NO_WEEKDAYS")
    
    # Test 4: Verify GET /api/vip/schedule/me includes the generated blocks
    print("\n[TEST 1.4] Verify GET /api/vip/schedule/me includes generated blocks")
    resp = requests.get(
        f"{BASE_URL}/vip/schedule/me",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print("❌ FAILED: Expected 200")
        return False
    
    data = resp.json()
    if len(data["blocks"]) < len(blocks):
        print(f"❌ FAILED: Expected at least {len(blocks)} blocks, got {len(data['blocks'])}")
        return False
    
    print(f"✅ PASSED: GET /me returned {len(data['blocks'])} blocks")
    
    print("\n✅ FEATURE 1: ALL TESTS PASSED")
    return True

def test_reschedule(users):
    """FEATURE 2: Test reschedule"""
    print("\n" + "="*80)
    print("FEATURE 2: RESCHEDULE")
    print("="*80)
    
    token_a = users["a"]["token"]
    token_b = users["b"]["token"]
    user_id_a = users["a"]["id"]
    user_id_b = users["b"]["id"]
    
    # Setup: A adds a normal availability block for a future date
    future_date = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")
    print(f"\n[SETUP] VIP A adds availability for {future_date} 18:00-22:00")
    
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/availability",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "date": future_date,
            "start": "18:00",
            "end": "22:00",
            "slot_len": 60,
            "tz": "UTC"
        }
    )
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Could not add availability: {resp.text}")
        return False
    
    # B books 19:00-20:00
    print(f"\n[SETUP] User B books 19:00-20:00 slot")
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/{user_id_a}/book",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "date": future_date,
            "start": "19:00",
            "end": "20:00",
            "coins": 300,
            "tz": "UTC"
        }
    )
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Could not book slot: {resp.text}")
        return False
    
    booking_data = resp.json()
    booking_id = booking_data["booking_id"]
    print(f"Booking ID: {booking_id}")
    
    # Test 1: B reschedules to 21:00-22:00 (valid slot)
    print("\n[TEST 2.1] B reschedules to 21:00-22:00 (valid available slot)")
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/bookings/{booking_id}/reschedule",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "date": future_date,
            "start": "21:00",
            "end": "22:00"
        }
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    
    if resp.status_code != 200:
        print("❌ FAILED: Expected 200")
        return False
    
    data = resp.json()
    if data["status"] != "pending":
        print(f"❌ FAILED: Expected status=pending, got {data['status']}")
        return False
    
    if data["start"] != "21:00" or data["end"] != "22:00":
        print(f"❌ FAILED: Expected start=21:00 end=22:00, got {data['start']}-{data['end']}")
        return False
    
    print("✅ PASSED: Reschedule successful, status=pending, time updated")
    
    # Verify via GET /api/vip/schedule/me
    print("\n[TEST 2.2] Verify booking shows new time in GET /api/vip/schedule/me")
    resp = requests.get(
        f"{BASE_URL}/vip/schedule/me",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    if resp.status_code != 200:
        print("❌ FAILED: Could not get schedule")
        return False
    
    data = resp.json()
    booking = next((b for b in data["pending"] if b["id"] == booking_id), None)
    
    if not booking:
        print("❌ FAILED: Booking not found in pending list")
        return False
    
    if booking["start"] != "21:00" or booking["end"] != "22:00":
        print(f"❌ FAILED: Booking time not updated: {booking['start']}-{booking['end']}")
        return False
    
    print("✅ PASSED: Booking shows new time 21:00-22:00")
    
    # Test 3: Reschedule to time outside availability (10:00-11:00)
    print("\n[TEST 2.3] Reschedule to time outside availability (10:00-11:00)")
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/bookings/{booking_id}/reschedule",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "date": future_date,
            "start": "10:00",
            "end": "11:00"
        }
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    
    if resp.status_code != 400:
        print("❌ FAILED: Expected 400 TIME_UNAVAILABLE")
        return False
    
    if "TIME_UNAVAILABLE" not in resp.json().get("detail", ""):
        print("❌ FAILED: Expected detail=TIME_UNAVAILABLE")
        return False
    
    print("✅ PASSED: Reschedule to unavailable time correctly rejected with 400 TIME_UNAVAILABLE")
    
    # Test 4: Create another booking at 18:00-19:00, then B reschedules to conflict with it
    print("\n[TEST 2.4] Create second booking, then reschedule to conflicting slot")
    
    # Register a third user C for the second booking
    import uuid
    suffix = str(uuid.uuid4())[:8]
    email_c = f"user_c_{suffix}@example.com"
    token_c, user_id_c = register_user(email_c, "password123", "User C")
    db.users.update_one({"id": user_id_c}, {"$set": {"coins": 5000}})
    
    # C books 18:00-19:00
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/{user_id_a}/book",
        headers={"Authorization": f"Bearer {token_c}"},
        json={
            "date": future_date,
            "start": "18:00",
            "end": "19:00",
            "coins": 300,
            "tz": "UTC"
        }
    )
    print(f"C books 18:00-19:00: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Could not create second booking: {resp.text}")
        return False
    
    # B tries to reschedule to 18:30-19:30 (conflicts with C's 18:00-19:00 + 15-min buffer)
    print("\n[TEST 2.5] B reschedules to 18:30-19:30 (conflicts with C's booking)")
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/bookings/{booking_id}/reschedule",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "date": future_date,
            "start": "18:30",
            "end": "19:30"
        }
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    
    if resp.status_code != 409:
        print("❌ FAILED: Expected 409 SLOT_TAKEN")
        return False
    
    if "SLOT_TAKEN" not in resp.json().get("detail", ""):
        print("❌ FAILED: Expected detail=SLOT_TAKEN")
        return False
    
    print("✅ PASSED: Reschedule to conflicting slot correctly rejected with 409 SLOT_TAKEN")
    
    # Test 5: VIP (A) tries to reschedule (should fail - only requester can reschedule)
    print("\n[TEST 2.6] VIP (A) tries to reschedule (should fail)")
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/bookings/{booking_id}/reschedule",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "date": future_date,
            "start": "20:00",
            "end": "21:00"
        }
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    
    if resp.status_code != 403:
        print("❌ FAILED: Expected 403")
        return False
    
    print("✅ PASSED: VIP cannot reschedule (only requester can)")
    
    # Test 6: Confirm the booking, then try to reschedule (should fail - NOT_PENDING)
    print("\n[TEST 2.7] Confirm booking, then try to reschedule")
    
    # A confirms the booking
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/bookings/{booking_id}/confirm",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    print(f"Confirm: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Could not confirm booking: {resp.text}")
        return False
    
    # B tries to reschedule confirmed booking
    resp = requests.post(
        f"{BASE_URL}/vip/schedule/bookings/{booking_id}/reschedule",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "date": future_date,
            "start": "20:00",
            "end": "21:00"
        }
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    
    if resp.status_code != 400:
        print("❌ FAILED: Expected 400 NOT_PENDING")
        return False
    
    if "NOT_PENDING" not in resp.json().get("detail", ""):
        print("❌ FAILED: Expected detail=NOT_PENDING")
        return False
    
    print("✅ PASSED: Cannot reschedule confirmed booking (400 NOT_PENDING)")
    
    print("\n✅ FEATURE 2: ALL TESTS PASSED")
    return True

def test_auto_complete(users):
    """FEATURE 3: Test auto-complete"""
    print("\n" + "="*80)
    print("FEATURE 3: AUTO-COMPLETE")
    print("="*80)
    
    token_a = users["a"]["token"]
    token_b = users["b"]["token"]
    user_id_a = users["a"]["id"]
    user_id_b = users["b"]["id"]
    
    # Get A's current coins/escrow/withdrawable
    resp = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    if resp.status_code != 200:
        print("❌ FAILED: Could not get user A info")
        return False
    
    user_a_before = resp.json()
    escrow_before = user_a_before.get("escrow", 0)
    withdrawable_before = user_a_before.get("withdrawable", 0)
    
    print(f"\n[SETUP] User A before: escrow={escrow_before}, withdrawable={withdrawable_before}")
    
    # Seed a confirmed booking with date in the past
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    booking_id = str(__import__("uuid").uuid4())
    
    print(f"\n[SETUP] Seeding confirmed booking with past date {past_date}")
    
    booking_doc = {
        "id": booking_id,
        "vip_id": user_id_a,
        "requester_id": user_id_b,
        "date": past_date,
        "start": "18:00",
        "end": "19:00",
        "lock_start": "17:45",
        "lock_end": "19:15",
        "tz": "UTC",
        "coins": 400,
        "status": "confirmed",
        "scheduled_at": f"{past_date}T18:00:00",
        "confirmed_at": datetime.now(timezone.utc).isoformat(),
        "reminder_30_sent": True
    }
    
    db.vip_sched.insert_one(booking_doc)
    
    # Add 400 to A's escrow
    db.users.update_one({"id": user_id_a}, {"$inc": {"escrow": 400}})
    
    print(f"✅ Seeded booking {booking_id} with 400 coins in escrow")
    
    # Call GET /api/vip/schedule/me as A (triggers lazy auto-complete)
    print("\n[TEST 3.1] Call GET /api/vip/schedule/me to trigger auto-complete")
    resp = requests.get(
        f"{BASE_URL}/vip/schedule/me",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print("❌ FAILED: Could not get schedule")
        return False
    
    # Verify booking status is now "completed"
    data = resp.json()
    completed_booking = next((b for b in data["past"] if b["id"] == booking_id), None)
    
    if not completed_booking:
        print("❌ FAILED: Booking not found in past list")
        return False
    
    if completed_booking["status"] != "completed":
        print(f"❌ FAILED: Expected status=completed, got {completed_booking['status']}")
        return False
    
    print("✅ PASSED: Booking status changed to 'completed'")
    
    # Verify A's withdrawable increased by 400 and escrow decreased by 400
    print("\n[TEST 3.2] Verify A's withdrawable increased and escrow decreased")
    resp = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    
    if resp.status_code != 200:
        print("❌ FAILED: Could not get user A info")
        return False
    
    user_a_after = resp.json()
    escrow_after = user_a_after.get("escrow", 0)
    withdrawable_after = user_a_after.get("withdrawable", 0)
    
    print(f"User A after: escrow={escrow_after}, withdrawable={withdrawable_after}")
    
    # Check DB directly as well
    user_a_db = db.users.find_one({"id": user_id_a})
    escrow_db = user_a_db.get("escrow", 0)
    withdrawable_db = user_a_db.get("withdrawable", 0)
    
    print(f"User A DB: escrow={escrow_db}, withdrawable={withdrawable_db}")
    
    # Expected: escrow decreased by 400, withdrawable increased by 400
    expected_escrow = escrow_before  # We added 400 in setup, then it should be removed
    expected_withdrawable = withdrawable_before + 400
    
    if escrow_db != expected_escrow:
        print(f"❌ FAILED: Expected escrow={expected_escrow}, got {escrow_db}")
        return False
    
    if withdrawable_db != expected_withdrawable:
        print(f"❌ FAILED: Expected withdrawable={expected_withdrawable}, got {withdrawable_db}")
        return False
    
    print("✅ PASSED: Escrow decreased by 400, withdrawable increased by 400")
    
    print("\n✅ FEATURE 3: ALL TESTS PASSED")
    return True

def main():
    print("="*80)
    print("VIP SCHEDULING - THREE NEW FEATURES TEST")
    print("="*80)
    
    # Setup users
    users = setup_users()
    
    # Test all three features
    results = {
        "recurring": test_recurring_availability(users),
        "reschedule": test_reschedule(users),
        "auto_complete": test_auto_complete(users)
    }
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for feature, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{feature.upper()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
