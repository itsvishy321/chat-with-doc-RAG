from supabase import create_client, Client
import os
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseService:
    def __init__(self):
        """Initialize Supabase client"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    def create_session(self, session_id: str, url: str, chunks_count: int) -> bool:
        """Create a new document session"""
        try:
            data = {
                "session_id": session_id,
                "document_url": url,
                "chunks_count": chunks_count,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("document_sessions").insert(data).execute()
            return True
            
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def save_chat_message(self, session_id: str, question: str, answer: str, 
                         relevant_chunks_count: int) -> bool:
        """Save a chat message to the database"""
        try:
            data = {
                "session_id": session_id,
                "question": question,
                "answer": answer,
                "relevant_chunks_count": relevant_chunks_count,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("chat_messages").insert(data).execute()
            
            # Update session's updated_at timestamp
            self.supabase.table("document_sessions").update({
                "updated_at": datetime.utcnow().isoformat()
            }).eq("session_id", session_id).execute()
            
            return True
            
        except Exception as e:
            print(f"Error saving chat message: {e}")
            return False
    
    def get_session_history(self, session_id: str) -> Dict:
        """Get session info and chat history"""
        try:
            # Get session info
            session_result = self.supabase.table("document_sessions").select("*").eq(
                "session_id", session_id
            ).execute()
            
            if not session_result.data:
                return None
            
            session_info = session_result.data[0]
            
            # Get chat messages
            messages_result = self.supabase.table("chat_messages").select("*").eq(
                "session_id", session_id
            ).order("created_at", desc=False).execute()
            
            return {
                "session_info": session_info,
                "chat_history": messages_result.data
            }
            
        except Exception as e:
            print(f"Error getting session history: {e}")
            return None
    
    def get_all_sessions(self, limit: int = 50) -> List[Dict]:
        """Get all document sessions ordered by most recent"""
        try:
            result = self.supabase.table("document_sessions").select(
                "session_id, document_url, chunks_count, created_at, updated_at"
            ).order("updated_at", desc=True).limit(limit).execute()
            
            return result.data
            
        except Exception as e:
            print(f"Error getting all sessions: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its chat messages"""
        try:
            # Delete chat messages first (foreign key constraint)
            self.supabase.table("chat_messages").delete().eq("session_id", session_id).execute()
            
            # Delete session
            self.supabase.table("document_sessions").delete().eq("session_id", session_id).execute()
            
            return True
            
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def search_sessions(self, search_term: str) -> List[Dict]:
        """Search sessions by document URL"""
        try:
            result = self.supabase.table("document_sessions").select(
                "session_id, document_url, chunks_count, created_at, updated_at"
            ).ilike("document_url", f"%{search_term}%").order("updated_at", desc=True).execute()
            
            return result.data
            
        except Exception as e:
            print(f"Error searching sessions: {e}")
            return []