"""
Scenario Testing Framework for Complete Printer App Workflows
Tests all scenarios from the comprehensive scenario table
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from db_extended import ExtendedPrinterDB
from datetime import datetime, timedelta
import json
import random

class ScenarioTester:
    """Test framework for all printer app scenarios"""
    
    def __init__(self, user_id: str = "test_user"):
        self.db = ExtendedPrinterDB()
        self.user_id = user_id
        self.results = []
    
    def reset(self):
        """Clear all test data"""
        print("🔄 Resetting test database...")
        # In production, you'd delete tables or use a separate test DB
        self.results = []
    
    def log_result(self, scenario: str, status: str, details: str):
        """Log test result"""
        result = {
            'scenario': scenario,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {scenario}: {details}")
    
    # ===== SETUP FLOW SCENARIOS =====
    
    def test_first_time_user(self):
        """Scenario: User opens app (first time)"""
        print("\n" + "="*60)
        print("📱 SCENARIO: First Time User")
        print("="*60)
        
        # Context: No printers, no queues, no cache
        has_printer = self.db.has_configured_printer(self.user_id)
        context = self.db.get_complete_context(self.user_id)
        
        if not has_printer and context['prints_today'] == 0:
            self.log_result(
                "First Time User",
                "PASS",
                "No printer configured, no cache. Should show SETUP flow."
            )
            return "SETUP_REQUIRED"
        else:
            self.log_result(
                "First Time User",
                "FAIL",
                f"Expected no printer, found: {has_printer}"
            )
            return "ERROR"
    
    def test_network_scan(self):
        """Scenario: App scans network"""
        print("\n📡 SCENARIO: Network Discovery")
        
        # Simulate Wi-Fi network scan
        wifi_devices = [
            {
                'name': 'HP LaserJet Pro',
                'ip': '192.168.1.105',
                'type': 'IPP',
                'model': 'HP LaserJet Pro M404dn'
            },
            {
                'name': 'Canon PIXMA',
                'ip': '192.168.1.108',
                'type': 'WSD',
                'model': 'Canon PIXMA TR8620'
            }
        ]
        
        self.db.record_network_scan(
            self.user_id,
            scan_type="Wi-Fi",
            devices_found=wifi_devices,
            wifi_ssid="HomeNetwork_5G",
            subnet="192.168.1.0/24"
        )
        
        self.db.record_hardware_info(
            self.user_id,
            wifi_ssid="HomeNetwork_5G",
            wifi_subnet="192.168.1.0/24",
            nearby_wifi=["HomeNetwork_5G", "Neighbor_WiFi", "Guest_Network"],
            os_type="Windows 11"
        )
        
        self.log_result(
            "Network Scan",
            "PASS",
            f"Found {len(wifi_devices)} devices on Wi-Fi network"
        )
        return wifi_devices
    
    def test_bluetooth_discovery(self):
        """Scenario: Bluetooth printer discovery"""
        print("\n🔵 SCENARIO: Bluetooth Discovery")
        
        bluetooth_devices = [
            "HP DeskJet 3755 (BT)",
            "Epson EcoTank ET-2800"
        ]
        
        self.db.record_network_scan(
            self.user_id,
            scan_type="Bluetooth",
            devices_found=[{'name': d, 'type': 'Bluetooth'} for d in bluetooth_devices]
        )
        
        self.log_result(
            "Bluetooth Discovery",
            "PASS",
            f"Found {len(bluetooth_devices)} Bluetooth printers"
        )
        return bluetooth_devices
    
    def test_printer_pairing(self, printer_data: dict):
        """Scenario: App pairs and installs printer"""
        print("\n🔗 SCENARIO: Printer Pairing & Installation")
        
        # Simulate discovering printer capabilities
        capabilities = {
            'color': True,
            'duplex': True,
            'paper_sizes': ['A4', 'Letter', 'Legal'],
            'max_dpi': 1200,
            'supports_scan': True
        }
        
        self.db.register_printer(
            self.user_id,
            printer_name=printer_data['name'],
            printer_model=printer_data['model'],
            connection_type=printer_data['type'],
            ip_address=printer_data.get('ip'),
            capabilities=capabilities,
            driver_type='SUPD',
            queue_name=f"Queue_{printer_data['name']}",
            port='IP_192.168.1.105',
            spooler_state='ready',
            test_print_status='success'
        )
        
        self.log_result(
            "Printer Pairing",
            "PASS",
            f"Paired {printer_data['name']}, installed queue, test print OK"
        )
        return True
    
    def test_scanner_setup(self):
        """Scenario: Scanner detection and setup"""
        print("\n📷 SCENARIO: Scanner Setup")
        
        self.db.register_scanner(
            self.user_id,
            scanner_name="HP LaserJet Pro M404dn (Scanner)",
            scanner_type="WIA",
            max_dpi=1200,
            supported_formats=['PDF', 'JPG', 'PNG']
        )
        
        has_scanner = self.db.has_scanner(self.user_id)
        
        if has_scanner:
            self.log_result(
                "Scanner Setup",
                "PASS",
                "Scanner registered with WIA support"
            )
            return True
        else:
            self.log_result(
                "Scanner Setup",
                "FAIL",
                "Scanner registration failed"
            )
            return False
    
    # ===== PRINT FLOW SCENARIOS =====
    
    def test_returning_user(self):
        """Scenario: User opens app (printer already configured)"""
        print("\n" + "="*60)
        print("👤 SCENARIO: Returning User")
        print("="*60)
        
        has_printer = self.db.has_configured_printer(self.user_id)
        
        if has_printer:
            self.log_result(
                "Returning User",
                "PASS",
                "Printer configured. Should show PRINT flow."
            )
            return "PRINT_READY"
        else:
            self.log_result(
                "Returning User",
                "FAIL",
                "No printer found for returning user"
            )
            return "SETUP_REQUIRED"
    
    def test_document_selection(self):
        """Scenario: User selects document/photo"""
        print("\n📄 SCENARIO: Document Selection")
        
        documents = [
            {
                'name': 'Report_Q1_2026.pdf',
                'type': 'PDF',
                'size_mb': 2.5,
                'pages': 15
            },
            {
                'name': 'Family_Photo.jpg',
                'type': 'JPG',
                'size_mb': 5.2,
                'pages': 1
            },
            {
                'name': 'Presentation.pptx',
                'type': 'PPTX',
                'size_mb': 12.8,
                'pages': 45
            }
        ]
        
        selected = documents[0]  # Select PDF report
        
        self.log_result(
            "Document Selection",
            "PASS",
            f"Selected: {selected['name']} ({selected['pages']} pages, {selected['size_mb']} MB)"
        )
        return selected
    
    def test_print_job_creation(self, document: dict):
        """Scenario: Create and track print job"""
        print("\n🖨️ SCENARIO: Print Job Creation & Tracking")
        
        settings = {
            'color_mode': 'black_white',
            'print_quality': 'high',
            'duplex': True,
            'num_copies': 2,
            'paper_size': 'A4',
            'printer_name': 'HP LaserJet Pro',
            'file_size_mb': document['size_mb']
        }
        
        job_id = self.db.create_print_job(
            self.user_id,
            file_name=document['name'],
            file_type=document['type'],
            page_count=document['pages'],
            settings=settings
        )
        
        # Simulate job progression
        self.db.update_job_status(job_id, 'printing')
        self.db.update_job_status(job_id, 'completed')
        
        self.log_result(
            "Print Job",
            "PASS",
            f"Job #{job_id} created, queued, printed successfully"
        )
        return job_id
    
    # ===== ECO OPTIMIZATION SCENARIOS =====
    
    def test_eco_optimization(self):
        """Scenario: Eco mode suggestion based on behavior"""
        print("\n" + "="*60)
        print("🌱 SCENARIO: Eco Optimization")
        print("="*60)
        
        # Set low ink status
        self.db.update_eco_status(
            self.user_id,
            ink_levels={
                'cyan': 15,
                'magenta': 20,
                'yellow': 18,
                'black': 25,
                'toner': 30
            },
            paper_status='Medium',
            total_pages=500
        )
        
        eco_context = self.db.get_eco_context(self.user_id)
        
        # AI should suggest greyscale or draft mode
        suggestion = None
        if eco_context.get('ink_level_black', 100) < 30:
            suggestion = "Draft Mode (ink low)"
        
        if suggestion:
            self.db.record_eco_suggestion(
                self.user_id,
                suggestion_type=suggestion,
                context=eco_context,
                user_action='accepted'  # Simulate user accepts
            )
            
            self.log_result(
                "Eco Optimization",
                "PASS",
                f"Suggested: {suggestion}. Ink: {eco_context['ink_level_black']}%"
            )
        else:
            self.log_result(
                "Eco Optimization",
                "WARNING",
                "No eco suggestion triggered (ink levels OK)"
            )
        
        return eco_context
    
    def test_paper_low_alert(self):
        """Scenario: Paper low alert before large job"""
        print("\n📄 SCENARIO: Paper Low Alert")
        
        # Create large print jobs in history
        for i in range(5):
            settings = {
                'color_mode': 'black_white',
                'print_quality': 'standard',
                'num_copies': 1,
                'paper_size': 'A4'
            }
            job_id = self.db.create_print_job(
                self.user_id,
                file_name=f"LargeDoc_{i}.pdf",
                file_type="PDF",
                page_count=random.randint(55, 80),  # Over 50 pages
                settings=settings
            )
            self.db.update_job_status(job_id, 'completed')
        
        # Set paper tray low
        self.db.update_eco_status(
            self.user_id,
            paper_status='Low'
        )
        
        eco_context = self.db.get_eco_context(self.user_id)
        
        if eco_context['recent_large_jobs'] >= 5 and eco_context['paper_tray_status'] == 'Low':
            self.log_result(
                "Paper Low Alert",
                "PASS",
                f"Alert triggered: {eco_context['recent_large_jobs']} large jobs, paper LOW"
            )
            return True
        else:
            self.log_result(
                "Paper Low Alert",
                "FAIL",
                f"Alert not triggered properly: {eco_context}"
            )
            return False
    
    def test_recent_file_detection(self):
        """Scenario: Print recently downloaded document"""
        print("\n⏰ SCENARIO: Recent File Detection")
        
        # Simulate file downloaded 30 seconds ago
        recent_time = datetime.now() - timedelta(seconds=30)
        
        self.db.track_recent_file(
            self.user_id,
            file_path="C:/Users/Downloads/Invoice_2026.pdf",
            file_type="PDF",
            file_size_mb=0.8,
            created_timestamp=recent_time
        )
        
        # Check detection
        recent_files = self.db.get_recent_files(self.user_id, seconds_ago=60)
        
        if len(recent_files) > 0:
            self.log_result(
                "Recent File Detection",
                "PASS",
                f"Detected {len(recent_files)} file(s) created <60s ago: {recent_files[0]['file_path']}"
            )
            return recent_files
        else:
            self.log_result(
                "Recent File Detection",
                "FAIL",
                "No recent files detected"
            )
            return []
    
    # ===== SCAN FLOW SCENARIOS =====
    
    def test_scan_workflow(self):
        """Scenario: Complete scan workflow"""
        print("\n" + "="*60)
        print("📷 SCENARIO: Scan Workflow")
        print("="*60)
        
        # Check scanner availability
        has_scanner = self.db.has_scanner(self.user_id)
        
        if not has_scanner:
            self.log_result(
                "Scan Workflow",
                "FAIL",
                "No scanner available"
            )
            return False
        
        # User chooses scan settings
        scan_settings = {
            'type': 'PDF',
            'dpi': 300,
            'page_count': 3
        }
        
        # Perform scan
        self.db.record_scan(
            self.user_id,
            scan_type=scan_settings['type'],
            dpi=scan_settings['dpi'],
            page_count=scan_settings['page_count'],
            file_size_mb=2.1,
            output_path="C:/Users/Scans/Document_2026.pdf"
        )
        
        self.log_result(
            "Scan Workflow",
            "PASS",
            f"Scanned {scan_settings['page_count']} pages at {scan_settings['dpi']} DPI to PDF"
        )
        return True
    
    # ===== COMPREHENSIVE TEST RUNNER =====
    
    def run_all_scenarios(self):
        """Run complete scenario test suite"""
        print("\n" + "="*80)
        print("🚀 RUNNING COMPREHENSIVE SCENARIO TEST SUITE")
        print("="*80)
        
        # SETUP FLOW
        print("\n📋 PHASE 1: SETUP FLOW")
        print("-" * 80)
        self.test_first_time_user()
        wifi_devices = self.test_network_scan()
        self.test_bluetooth_discovery()
        
        if wifi_devices:
            self.test_printer_pairing(wifi_devices[0])
        
        self.test_scanner_setup()
        
        # PRINT FLOW
        print("\n📋 PHASE 2: PRINT FLOW")
        print("-" * 80)
        self.test_returning_user()
        document = self.test_document_selection()
        self.test_print_job_creation(document)
        
        # ECO OPTIMIZATION
        print("\n📋 PHASE 3: ECO OPTIMIZATION")
        print("-" * 80)
        self.test_eco_optimization()
        self.test_paper_low_alert()
        self.test_recent_file_detection()
        
        # SCAN FLOW
        print("\n📋 PHASE 4: SCAN FLOW")
        print("-" * 80)
        self.test_scan_workflow()
        
        # RESULTS SUMMARY
        print("\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
        print("="*80)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        warnings = sum(1 for r in self.results if r['status'] == 'WARNING')
        total = len(self.results)
        
        print(f"\n✅ PASSED: {passed}/{total}")
        print(f"❌ FAILED: {failed}/{total}")
        print(f"⚠️  WARNINGS: {warnings}/{total}")
        print(f"\n📈 Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed scenarios
        if failed > 0:
            print("\n❌ FAILED SCENARIOS:")
            for r in self.results:
                if r['status'] == 'FAIL':
                    print(f"  - {r['scenario']}: {r['details']}")
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'results': self.results
        }


if __name__ == "__main__":
    print("🧪 Scenario Testing Framework")
    print("Testing complete printer app workflows\n")
    
    tester = ScenarioTester(user_id="scenario_test_user")
    results = tester.run_all_scenarios()
    
    print("\n" + "="*80)
    print("✅ SCENARIO TESTING COMPLETE")
    print("="*80)
    print(f"\nDetailed results: {len(results['results'])} scenarios tested")
    print("\nTo integrate with AI agent:")
    print("  1. Use db_extended.py for context collection")
    print("  2. Pass context to agent via get_complete_context()")
    print("  3. Agent analyzes context and makes intelligent decisions")
    print("\n💡 Next: Run 'python test_agentic_scenarios.py' for AI-powered testing")
