"""
Extended Database Schema for Complete Printer App Scenarios
Supports: Setup, Print, Scan, Eco Optimization, and Device Discovery
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class ExtendedPrinterDB:
    """Extended database with comprehensive context tracking"""
    
    def __init__(self, db_path: str = "../user_context.db"):
        self.db_path = db_path
        self._init_extended_tables()
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def _init_extended_tables(self):
        """Create extended tables for all scenarios"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Hardware & Network Discovery
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_hardware (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                wifi_ssid TEXT,
                wifi_subnet TEXT,
                bluetooth_devices TEXT,  -- JSON array
                nearby_wifi_signals TEXT,  -- JSON array
                os_type TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Printer Configuration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS printer_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                printer_name TEXT,
                printer_model TEXT,
                connection_type TEXT,  -- IPP/WSD/Bluetooth/USB
                ip_address TEXT,
                capabilities TEXT,  -- JSON: duplex, color, paper_sizes
                driver_type TEXT,  -- Driver/SUPD/PSA
                queue_name TEXT,
                port TEXT,
                spooler_state TEXT,
                test_print_status TEXT,
                is_default BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                setup_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME
            )
        """)
        
        # 3. Scanner Configuration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scanner_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                scanner_name TEXT,
                scanner_type TEXT,  -- TWAIN/WIA/IPP
                max_dpi INTEGER,
                supported_formats TEXT,  -- JSON: PDF, JPG, PNG
                is_active BOOLEAN DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. Scan History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                scan_type TEXT,  -- PDF/JPG
                dpi INTEGER,
                page_count INTEGER,
                file_size_mb REAL,
                output_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. Eco Optimization Tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS eco_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                ink_level_cyan REAL,
                ink_level_magenta REAL,
                ink_level_yellow REAL,
                ink_level_black REAL,
                toner_level REAL,
                paper_tray_status TEXT,  -- Low/Medium/Full
                total_pages_printed INTEGER,
                eco_suggestions_accepted INTEGER DEFAULT 0,
                eco_suggestions_rejected INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 6. Recent Files Detection
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recent_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                file_path TEXT,
                file_type TEXT,  -- PDF/DOCX/JPG/PNG
                file_size_mb REAL,
                created_timestamp DATETIME,
                detected_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                was_printed BOOLEAN DEFAULT 0
            )
        """)
        
        # 7. Print Job Details (extended from usage_history)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS print_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                job_id TEXT,
                file_name TEXT,
                file_type TEXT,
                file_size_mb REAL,
                page_count INTEGER,
                color_mode TEXT,
                print_quality TEXT,
                duplex BOOLEAN,
                num_copies INTEGER,
                paper_size TEXT,
                printer_name TEXT,
                queue_status TEXT,  -- queued/printing/completed/failed
                spooler_status TEXT,
                eco_mode_used BOOLEAN DEFAULT 0,
                cost_estimate REAL,
                actual_cost REAL,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                completion_time DATETIME,
                error_message TEXT
            )
        """)
        
        # 8. Network Scan History
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                scan_type TEXT,  -- Wi-Fi/Bluetooth
                devices_found TEXT,  -- JSON array
                wifi_ssid TEXT,
                subnet TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 9. Alerts & Notifications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                alert_type TEXT,  -- paper_low/ink_low/large_job/eco_suggestion
                alert_message TEXT,
                context_data TEXT,  -- JSON: relevant data
                was_shown BOOLEAN DEFAULT 0,
                user_action TEXT,  -- dismissed/accepted/postponed
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ===== SETUP FLOW METHODS =====
    
    def record_network_scan(self, user_id: str, scan_type: str, devices_found: List[Dict], 
                           wifi_ssid: str = None, subnet: str = None):
        """Record network scan results"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO network_scans (user_id, scan_type, devices_found, wifi_ssid, subnet)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, scan_type, json.dumps(devices_found), wifi_ssid, subnet))
        conn.commit()
        conn.close()
    
    def record_hardware_info(self, user_id: str, wifi_ssid: str = None, wifi_subnet: str = None,
                            bluetooth_devices: List[str] = None, nearby_wifi: List[str] = None,
                            os_type: str = None):
        """Record device hardware and network info"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO device_hardware 
            (user_id, wifi_ssid, wifi_subnet, bluetooth_devices, nearby_wifi_signals, os_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id, wifi_ssid, wifi_subnet,
            json.dumps(bluetooth_devices or []),
            json.dumps(nearby_wifi or []),
            os_type
        ))
        conn.commit()
        conn.close()
    
    def register_printer(self, user_id: str, printer_name: str, printer_model: str,
                        connection_type: str, capabilities: Dict, **kwargs):
        """Register discovered printer"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO printer_config
            (user_id, printer_name, printer_model, connection_type, ip_address, 
             capabilities, driver_type, queue_name, port, spooler_state, 
             test_print_status, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, printer_name, printer_model, connection_type,
            kwargs.get('ip_address'),
            json.dumps(capabilities),
            kwargs.get('driver_type'),
            kwargs.get('queue_name'),
            kwargs.get('port'),
            kwargs.get('spooler_state', 'ready'),
            kwargs.get('test_print_status'),
            kwargs.get('is_default', 1)
        ))
        conn.commit()
        conn.close()
    
    def has_configured_printer(self, user_id: str) -> bool:
        """Check if user has any configured printers"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM printer_config
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    # ===== PRINT FLOW METHODS =====
    
    def create_print_job(self, user_id: str, file_name: str, file_type: str,
                        page_count: int, settings: Dict) -> int:
        """Create new print job with full tracking"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO print_jobs
            (user_id, file_name, file_type, file_size_mb, page_count,
             color_mode, print_quality, duplex, num_copies, paper_size,
             printer_name, queue_status, eco_mode_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, file_name, file_type,
            settings.get('file_size_mb', 0),
            page_count,
            settings.get('color_mode', 'black_white'),
            settings.get('print_quality', 'standard'),
            settings.get('duplex', False),
            settings.get('num_copies', 1),
            settings.get('paper_size', 'A4'),
            settings.get('printer_name', 'default'),
            'queued',
            settings.get('eco_mode', False)
        ))
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return job_id
    
    def update_job_status(self, job_id: int, status: str, error: str = None):
        """Update print job status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if status == 'completed':
            cursor.execute("""
                UPDATE print_jobs
                SET queue_status = ?, completion_time = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, job_id))
        else:
            cursor.execute("""
                UPDATE print_jobs
                SET queue_status = ?, error_message = ?
                WHERE id = ?
            """, (status, error, job_id))
        
        conn.commit()
        conn.close()
    
    # ===== ECO OPTIMIZATION METHODS =====
    
    def update_eco_status(self, user_id: str, ink_levels: Dict = None, 
                         paper_status: str = None, total_pages: int = None):
        """Update eco tracking data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO eco_tracking
            (user_id, ink_level_cyan, ink_level_magenta, ink_level_yellow, 
             ink_level_black, toner_level, paper_tray_status, total_pages_printed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            ink_levels.get('cyan', 100) if ink_levels else 100,
            ink_levels.get('magenta', 100) if ink_levels else 100,
            ink_levels.get('yellow', 100) if ink_levels else 100,
            ink_levels.get('black', 100) if ink_levels else 100,
            ink_levels.get('toner', 100) if ink_levels else 100,
            paper_status or 'Full',
            total_pages or 0
        ))
        conn.commit()
        conn.close()
    
    def get_eco_context(self, user_id: str) -> Dict:
        """Get eco optimization context"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get latest eco status
        cursor.execute("""
            SELECT ink_level_black, toner_level, paper_tray_status,
                   total_pages_printed, eco_suggestions_accepted,
                   eco_suggestions_rejected
            FROM eco_tracking
            WHERE user_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {}
        
        # Get recent large jobs
        cursor.execute("""
            SELECT COUNT(*) FROM print_jobs
            WHERE user_id = ? AND page_count > 50
            AND start_time > datetime('now', '-7 days')
        """, (user_id,))
        large_jobs_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'ink_level_black': row[0],
            'toner_level': row[1],
            'paper_tray_status': row[2],
            'total_pages_printed': row[3],
            'eco_acceptance_rate': row[4] / max(1, row[4] + row[5]),
            'recent_large_jobs': large_jobs_count
        }
    
    def record_eco_suggestion(self, user_id: str, suggestion_type: str, 
                             context: Dict, user_action: str = None):
        """Record eco suggestion and user response"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO alerts
            (user_id, alert_type, alert_message, context_data, user_action)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id, 'eco_suggestion', suggestion_type,
            json.dumps(context), user_action
        ))
        
        # Update eco_tracking acceptance/rejection
        if user_action == 'accepted':
            cursor.execute("""
                UPDATE eco_tracking
                SET eco_suggestions_accepted = eco_suggestions_accepted + 1
                WHERE user_id = ? AND id = (
                    SELECT id FROM eco_tracking WHERE user_id = ?
                    ORDER BY timestamp DESC LIMIT 1
                )
            """, (user_id, user_id))
        elif user_action == 'rejected':
            cursor.execute("""
                UPDATE eco_tracking
                SET eco_suggestions_rejected = eco_suggestions_rejected + 1
                WHERE user_id = ? AND id = (
                    SELECT id FROM eco_tracking WHERE user_id = ?
                    ORDER BY timestamp DESC LIMIT 1
                )
            """, (user_id, user_id))
        
        conn.commit()
        conn.close()
    
    # ===== RECENT FILES DETECTION =====
    
    def track_recent_file(self, user_id: str, file_path: str, file_type: str,
                         file_size_mb: float, created_timestamp: datetime):
        """Track recently downloaded/created files"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recent_files
            (user_id, file_path, file_type, file_size_mb, created_timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, file_path, file_type, file_size_mb, created_timestamp))
        conn.commit()
        conn.close()
    
    def get_recent_files(self, user_id: str, seconds_ago: int = 60) -> List[Dict]:
        """Get files created within last N seconds"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT file_path, file_type, file_size_mb, created_timestamp
            FROM recent_files
            WHERE user_id = ?
            AND created_timestamp > datetime('now', '-{seconds_ago} seconds')
            AND was_printed = 0
            ORDER BY created_timestamp DESC
        """, (user_id,))
        
        files = []
        for row in cursor.fetchall():
            files.append({
                'file_path': row[0],
                'file_type': row[1],
                'file_size_mb': row[2],
                'created_timestamp': row[3]
            })
        conn.close()
        return files
    
    # ===== SCAN FLOW METHODS =====
    
    def register_scanner(self, user_id: str, scanner_name: str, scanner_type: str,
                        max_dpi: int, supported_formats: List[str]):
        """Register scanner capabilities"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scanner_config
            (user_id, scanner_name, scanner_type, max_dpi, supported_formats)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, scanner_name, scanner_type, max_dpi, json.dumps(supported_formats)))
        conn.commit()
        conn.close()
    
    def has_scanner(self, user_id: str) -> bool:
        """Check if user has scanner configured"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM scanner_config
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def record_scan(self, user_id: str, scan_type: str, dpi: int,
                   page_count: int, file_size_mb: float, output_path: str):
        """Record completed scan"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scan_history
            (user_id, scan_type, dpi, page_count, file_size_mb, output_path)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, scan_type, dpi, page_count, file_size_mb, output_path))
        conn.commit()
        conn.close()
    
    # ===== COMPREHENSIVE CONTEXT =====
    
    def get_complete_context(self, user_id: str) -> Dict:
        """Get complete context for AI agent"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        context = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Printer status
        cursor.execute("""
            SELECT COUNT(*) FROM printer_config
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        context['has_printer'] = cursor.fetchone()[0] > 0
        
        # Scanner status
        context['has_scanner'] = self.has_scanner(user_id)
        
        # Recent activity (last 24 hours)
        cursor.execute("""
            SELECT COUNT(*) FROM print_jobs
            WHERE user_id = ? AND start_time > datetime('now', '-1 day')
        """, (user_id,))
        context['prints_today'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM scan_history
            WHERE user_id = ? AND timestamp > datetime('now', '-1 day')
        """, (user_id,))
        context['scans_today'] = cursor.fetchone()[0]
        
        # Eco context
        context['eco'] = self.get_eco_context(user_id)
        
        # Recent files
        context['recent_files'] = self.get_recent_files(user_id, seconds_ago=60)
        
        # Active alerts
        cursor.execute("""
            SELECT alert_type, alert_message, context_data
            FROM alerts
            WHERE user_id = ? AND was_shown = 0
            ORDER BY timestamp DESC LIMIT 5
        """, (user_id,))
        
        context['pending_alerts'] = []
        for row in cursor.fetchall():
            context['pending_alerts'].append({
                'type': row[0],
                'message': row[1],
                'data': json.loads(row[2]) if row[2] else {}
            })
        
        conn.close()
        return context
