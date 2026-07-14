"""
Database Layer for Context-Aware Print Management Application
Manages SQLite database for storing user sessions, preferences, and usage history.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
import json


class ContextDatabase:
    """Manages user context data in SQLite database."""
    
    def __init__(self, db_path: str = "user_context.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                error_message TEXT,
                session_data TEXT
            )
        """)
        
        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT PRIMARY KEY,
                printer_setup BOOLEAN DEFAULT 0,
                last_printer_model TEXT,
                default_color_mode TEXT,
                default_paper_size TEXT,
                preferences_data TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Usage history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                color_mode TEXT,
                paper_size TEXT,
                num_copies INTEGER,
                print_quality TEXT,
                operation_type TEXT,
                success BOOLEAN DEFAULT 1
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_user_context(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Retrieve comprehensive user context including sessions, preferences, and usage history.
        
        Args:
            user_id: User identifier (default: "default")
            
        Returns:
            Dictionary containing all user context data
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        context = {
            "user_id": user_id,
            "sessions": [],
            "preferences": None,
            "usage_history": []
        }
        
        # Get last 10 sessions
        cursor.execute("""
            SELECT * FROM user_sessions 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        """, (user_id,))
        context["sessions"] = [dict(row) for row in cursor.fetchall()]
        
        # Get user preferences
        cursor.execute("""
            SELECT * FROM user_preferences 
            WHERE user_id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if row:
            context["preferences"] = dict(row)
        
        # Get last 20 usage records
        cursor.execute("""
            SELECT * FROM usage_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 20
        """, (user_id,))
        context["usage_history"] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return context
    
    def update_context(self, user_id: str, event_type: str, data: Dict[str, Any]):
        """
        Update context based on user actions.
        
        Args:
            user_id: User identifier
            event_type: Type of event (session, preference, usage)
            data: Event data to store
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if event_type == "session":
            cursor.execute("""
                INSERT INTO user_sessions (user_id, status, error_message, session_data)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                data.get("status", "active"),
                data.get("error_message"),
                json.dumps(data.get("session_data", {}))
            ))
        
        elif event_type == "preference":
            cursor.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (user_id, printer_setup, last_printer_model, default_color_mode, 
                 default_paper_size, preferences_data, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                user_id,
                data.get("printer_setup", False),
                data.get("last_printer_model"),
                data.get("default_color_mode"),
                data.get("default_paper_size"),
                json.dumps(data.get("preferences_data", {}))
            ))
        
        elif event_type == "usage":
            cursor.execute("""
                INSERT INTO usage_history 
                (user_id, color_mode, paper_size, num_copies, print_quality, 
                 operation_type, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                data.get("color_mode"),
                data.get("paper_size"),
                data.get("num_copies", 1),
                data.get("print_quality"),
                data.get("operation_type", "print"),
                data.get("success", True)
            ))
        
        conn.commit()
        conn.close()
    
    def summarize_context(self, user_id: str = "default") -> str:
        """
        Generate a natural language summary of user context for the LLM.
        
        Args:
            user_id: User identifier
            
        Returns:
            Natural language summary string
        """
        context = self.get_user_context(user_id)
        
        summary_parts = []
        
        # Printer setup status
        if context["preferences"] and context["preferences"].get("printer_setup"):
            printer_model = context["preferences"].get("last_printer_model", "Unknown")
            summary_parts.append(f"User has set up a {printer_model} printer.")
        else:
            summary_parts.append("User has not completed printer setup yet.")
        
        # Recent UNRESOLVED errors only (don't mention resolved errors)
        if context["sessions"]:
            sessions = context["sessions"]
            for i, session in enumerate(sessions[:5]):
                if session.get("status") == "error":
                    # Check if this error has been resolved
                    has_resolution = any(
                        s.get("status") in ["success", "setup_complete", "resolved"]
                        for s in sessions[:i]  # Sessions BEFORE (newer than) this error
                    )
                    if not has_resolution:
                        # Unresolved error - mention it
                        error_msg = session.get("error_message", "Unknown error")
                        summary_parts.append(f"IMPORTANT: There is an unresolved error: {error_msg}")
                        break
        
        # Recent print jobs with details
        if context["sessions"]:
            recent_prints = [s for s in context["sessions"][:5] if s.get("status") == "success"]
            if recent_prints:
                summary_parts.append(f"Recently completed {len(recent_prints)} print job(s).")
                # Add details about most recent print
                latest = recent_prints[0]
                session_data_str = latest.get("session_data")
                if session_data_str:
                    try:
                        import json
                        session_data = json.loads(session_data_str)
                        if isinstance(session_data, str):
                            session_data = json.loads(session_data)
                        if isinstance(session_data, dict):
                            summary_parts.append(
                                f"Last print: {session_data.get('num_copies', 1)} copies, "
                                f"{session_data.get('color_mode', 'unknown')}, "
                                f"{session_data.get('paper_size', 'unknown')}, "
                                f"{session_data.get('print_quality', 'normal')} quality."
                            )
                    except:
                        pass
        
        # Resolved errors history
        if context["sessions"]:
            resolved_errors = [s for s in context["sessions"][:10] if s.get("status") == "resolved"]
            if resolved_errors:
                summary_parts.append(f"User has successfully resolved {len(resolved_errors)} error(s) recently.")
                # Add detail about most recent resolution
                latest_resolution = resolved_errors[0]
                session_data_str = latest_resolution.get("session_data")
                if session_data_str:
                    try:
                        import json
                        session_data = json.loads(session_data_str)
                        if isinstance(session_data, str):
                            session_data = json.loads(session_data)
                        if isinstance(session_data, dict) and session_data.get("original_error"):
                            summary_parts.append(f"Last resolved error: {session_data.get('original_error')}")
                    except:
                        pass
        
        # Usage patterns
        if context["usage_history"]:
            recent_usage = context["usage_history"][:10]
            color_prints = sum(1 for u in recent_usage if u.get("color_mode") == "color")
            
            total_copies = sum(u.get("num_copies", 1) for u in recent_usage if u.get("operation_type") == "print")
            summary_parts.append(f"Total pages printed in recent history: {total_copies}")
            
            if color_prints > len(recent_usage) / 2:
                summary_parts.append("User typically prints in color.")
            else:
                summary_parts.append("User typically prints in black and white.")
            
            # Common paper size
            paper_sizes = [u.get("paper_size") for u in recent_usage if u.get("paper_size")]
            if paper_sizes:
                most_common_paper = max(set(paper_sizes), key=paper_sizes.count)
                summary_parts.append(f"Most commonly used paper size: {most_common_paper}")
        
        # Preferences
        if context["preferences"]:
            default_color = context["preferences"].get("default_color_mode")
            default_paper = context["preferences"].get("default_paper_size")
            
            if default_color:
                summary_parts.append(f"User's preferred color mode: {default_color}")
            if default_paper:
                summary_parts.append(f"User's preferred paper size: {default_paper}")
        
        return " ".join(summary_parts) if summary_parts else "No context available for this user."
    
    def get_last_session_status(self, user_id: str = "default") -> Optional[str]:
        """Get the status of the last session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT status FROM user_sessions 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def has_printer_setup(self, user_id: str = "default") -> bool:
        """Check if user has completed printer setup."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT printer_setup FROM user_preferences 
            WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return bool(result[0]) if result else False
    
    def get_smart_defaults(self, user_id: str = "default") -> Dict[str, Any]:
        """
        Get smart defaults based on RECENT usage history (prioritizes behavior over preferences).
        Uses a weighted approach that favors more recent prints.
        
        Returns:
            Dictionary with recommended default values
        """
        context = self.get_user_context(user_id)
        defaults = {
            "color_mode": "black_white",
            "paper_size": "A4",
            "num_copies": 1,
            "print_quality": "normal"
        }
        
        # Start with preferences as baseline (but will be overridden by usage)
        if context["preferences"]:
            prefs = context["preferences"]
            if prefs.get("default_color_mode"):
                defaults["color_mode"] = prefs["default_color_mode"]
            if prefs.get("default_paper_size"):
                defaults["paper_size"] = prefs["default_paper_size"]
        
        # PRIORITIZE recent usage patterns
        # Focus on last 5 prints for more responsive behavior
        if context["usage_history"]:
            recent = context["usage_history"][:5]  # Most recent 5 prints
            
            if len(recent) > 0:
                # Most common color mode (from recent prints)
                color_modes = [u.get("color_mode") for u in recent if u.get("color_mode")]
                if color_modes:
                    defaults["color_mode"] = max(set(color_modes), key=color_modes.count)
                
                # Most common paper size (from recent prints)
                paper_sizes = [u.get("paper_size") for u in recent if u.get("paper_size")]
                if paper_sizes:
                    defaults["paper_size"] = max(set(paper_sizes), key=paper_sizes.count)
                
                # Most common print quality (from recent prints)
                print_qualities = [u.get("print_quality") for u in recent if u.get("print_quality")]
                if print_qualities:
                    defaults["print_quality"] = max(set(print_qualities), key=print_qualities.count)
                
                # Average number of copies (from recent prints, rounded)
                num_copies_list = [u.get("num_copies") for u in recent if u.get("num_copies")]
                if num_copies_list:
                    defaults["num_copies"] = round(sum(num_copies_list) / len(num_copies_list))
        
        return defaults
    
    def clear_usage_history(self, user_id: str = "default"):
        """Clear only usage history for a user (useful for scenario testing)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM usage_history WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()
    
    def add_to_usage_history(self, user_id: str, color_mode: str, paper_size: str, 
                            num_copies: int = 1, print_quality: str = "normal"):
        """
        Convenience method to add a usage record.
        
        Args:
            user_id: User identifier
            color_mode: Color mode (color/black_white)
            paper_size: Paper size (A4/Letter/Legal/A3)
            num_copies: Number of copies
            print_quality: Print quality (draft/normal/high)
        """
        self.update_context(user_id, "usage", {
            "color_mode": color_mode,
            "paper_size": paper_size,
            "num_copies": num_copies,
            "print_quality": print_quality,
            "operation_type": "print",
            "success": True
        })
    
    def clear_context(self, user_id: str = "default"):
        """Clear all context data for a user (useful for testing)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM usage_history WHERE user_id = ?", (user_id,))
        
        conn.commit()
        conn.close()


# Convenience function for quick initialization
def get_db(db_path: str = "user_context.db") -> ContextDatabase:
    """Get or create a ContextDatabase instance."""
    return ContextDatabase(db_path)
