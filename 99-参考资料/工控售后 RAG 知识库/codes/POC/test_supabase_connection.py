
import os
import time
import pytest
from supabase_client import IndustrialAuth, TelemetryLogger

# --- Config ---
# Ensure these match your real credentials for testing
TEST_EMAIL = "weiwill666@gmail.com" 
TEST_PASSWORD = "453721Wd"

@pytest.fixture
def auth_client():
    return IndustrialAuth()

@pytest.fixture
def logger_client():
    return TelemetryLogger()

def test_login_flow(auth_client):
    """Test Case 1: Validate Login and Profile Retrieval"""
    print(f"\n[Test] Attempting login with {TEST_EMAIL}...")
    
    # 1. Sign In
    user = auth_client.sign_in(TEST_EMAIL, TEST_PASSWORD)
    assert user is not None, "Login failed! Check credentials."
    print(f"[Success] Logged in as User ID: {user.id}")
    
    # 2. Fetch Stats
    stats = auth_client.get_profile_stats(user.id)
    print(f"[Success] Retrieved Profile Stats: {stats}")
    assert 'stats' in stats, "Profile missing 'stats' field"

def test_telemetry_flow(logger_client, auth_client):
    """Test Case 2: Validate Async Logging"""
    # Need a valid user ID first
    user = auth_client.sign_in(TEST_EMAIL, TEST_PASSWORD)
    user_id = user.id
    
    print("\n[Test] simulating a chat session...")
    
    # 1. Create Session
    session_id = logger_client.create_session(user_id, title="Pytest Session")
    assert session_id is not None, "Failed to create session"
    print(f"[Success] Created Session: {session_id}")
    
    # 2. Log Interaction
    meta = {"test_key": "test_value", "latency": 100}
    try:
        logger_client.log_interaction(session_id, user_id, "user", "Hello World", metadata=None)
        logger_client.log_interaction(session_id, user_id, "assistant", "Hi there!", metadata=meta)
        print("[Success] Interaction logged (Async check needed in DB)")
    except Exception as e:
        pytest.fail(f"Logging failed: {e}")
        
    # Wait a bit for thread to finish
    time.sleep(2)

if __name__ == "__main__":
    # Manual run wrapper
    print("=== Starting Supabase Integration Test ===")
    try:
        auth = IndustrialAuth()
        logger = TelemetryLogger()
        
        test_login_flow(auth)
        test_telemetry_flow(logger, auth)
        
        print("\n✅ All Tests Passed! Backend is ready.")
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
