import os
import json
import threading
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Load env from parent directory if not found
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Singleton Client
_supabase_client = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        url = os.environ.get("Supabase_URL")
        key = os.environ.get("supabase_key")
        
        # Debug print
        if not url:
             print(f"[Supabase Debug] URL not found. Current ENV keys: {list(os.environ.keys())[:5]}...")
             
        if not url or not key:
            raise ValueError("Supabase credentials missing in .env")
        _supabase_client = create_client(url, key)
    return _supabase_client

class IndustrialAuth:
    """Handles User Authentication & Profile Management"""
    
    def __init__(self):
        self.client = get_supabase_client()
        
    def sign_in(self, email, password):
        """Sign in with email/password"""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response.user
        except Exception as e:
            print(f"[Auth Error] Sign in failed: {e}")
            return None

    def update_password(self, new_password):
        """Update current user's password"""
        try:
            self.client.auth.update_user({"password": new_password})
            return True, "Password updated successfully"
        except Exception as e:
            return False, str(e)

    def get_profile_stats(self, user_id):
        """Fetch user profile stats for Sidebar"""
        try:
            # RLS ensures user only sees their own profile unless admin
            response = self.client.table("profiles").select("display_name, role, stats").eq("id", user_id).single().execute()
            if response.data:
                return response.data
            return {}
        except Exception as e:
            print(f"[Profile Error] Fetch failed: {e}")
            return {}

class TelemetryLogger:
    """Handles Async Logging of Chat Interactions"""
    
    def __init__(self):
        self.client = get_supabase_client()
        
    def _background_log(self, data):
        """Internal worker for async insert"""
        try:
            self.client.table("chat_messages").insert(data).execute()
        except Exception as e:
            print(f"[Telemetry Error] Failed to log message: {e}")

    def log_interaction(self, session_id, user_id, role, content, metadata=None):
        """
        Log entry and return the Message ID (Synchronous to ensure ID availability).
        """
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        
        try:
            response = self.client.table("chat_messages").insert(payload).execute()
            if response.data:
                return response.data[0]['id']
        except Exception as e:
            print(f"[Telemetry Error] Failed to log message: {e}")
            return None

    def create_session(self, user_id, title="New Chat"):
        """Create a new chat session"""
        try:
            data = {
                "user_id": user_id,
                "title": title
            }
            response = self.client.table("chat_sessions").insert(data).execute()
            if response.data:
                return response.data[0]['id']
        except Exception as e:
            print(f"[Session Error] Create failed: {e}")
        return None

    def log_feedback(self, message_id, user_id, score, comment=None):
        """Log user feedback (Like/Dislike)"""
        try:
            self.client.table("feedback").insert({
                "message_id": message_id,
                "user_id": user_id,
                "score": score,
                "comment": comment
            }).execute()
            
            # Update user stats: increment feedback count
            # Note: We can also do this via DB trigger, but client side is fine for now
            # Actually, let's use a trigger for consistency? No, simple update here is okay.
            # But wait, RLS allows user to update OWN profile stats? 
            # In schema.sql I added: create policy "Users can update own profile"
            
            # Let's fetch current stats first or let DB handle it. 
            # To correspond with schema trigger logic, we might want a trigger for feedback too. 
            # For now, let's just log the feedback.
            return True
        except Exception as e:
            print(f"[Feedback Error] {e}")
            return False
