"""
Streamlit UI for Context-Aware Print Management Application
Dynamic interface that adapts based on user context and agent intelligence.
"""

import streamlit as st
from db import get_db
from agent import get_agent
import sys
import json
import datetime
import time
from pathlib import Path

# Add src to path if needed
sys.path.append(str(Path(__file__).parent))


# Page configuration
st.set_page_config(
    page_title="Smart Print Manager",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "db" not in st.session_state:
        st.session_state.db = get_db("user_context.db")
    
    if "agent" not in st.session_state:
        try:
            st.session_state.agent = get_agent(st.session_state.db, "llama3.1")
            st.session_state.agent_ready = True
        except Exception as e:
            st.session_state.agent_ready = False
            st.session_state.agent_error = str(e)
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = "default"
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "current_flow" not in st.session_state:
        st.session_state.current_flow = None


def sidebar_controls():
    """Render sidebar with context information and controls."""
    with st.sidebar:
        st.title("🖨️ Smart Print Manager")
        st.markdown("---")
        
        # User ID selector (for demo/testing)
        st.session_state.user_id = st.text_input(
            "User ID", 
            value=st.session_state.user_id,
            help="Change user ID to test different contexts"
        )
        
        st.markdown("---")
        
        # Context summary
        st.subheader("📊 Your Context")
        
        if st.session_state.db.has_printer_setup(st.session_state.user_id):
            st.success("✅ Printer configured")
            context = st.session_state.db.get_user_context(st.session_state.user_id)
            if context["preferences"]:
                st.info(f"Printer: {context['preferences'].get('last_printer_model', 'N/A')}")
        else:
            st.warning("⚠️ Printer not set up")
        
        # Display context summary
        summary = st.session_state.db.summarize_context(st.session_state.user_id)
        st.text_area("Context Summary", summary, height=150, disabled=True)
        
        st.markdown("---")
        
        # Smart defaults with AI indicator
        st.subheader("🎯 Smart Defaults")
        
        # Try to get AI-powered defaults if available
        if hasattr(st.session_state, 'last_response') and st.session_state.last_response:
            defaults = st.session_state.last_response.get("smart_defaults", {})
            is_ai_powered = st.session_state.last_response.get("is_ai_powered", False)
            
            if is_ai_powered and defaults.get("reasoning"):
                st.success("🤖 AI-Powered Recommendations")
                st.caption(f"_{defaults.get('reasoning', '')}_")
            else:
                st.info("📊 Statistical Analysis")
        else:
            defaults = st.session_state.db.get_smart_defaults(st.session_state.user_id)
            st.info("📊 Statistical Analysis")
        
        # Show the defaults
        display_defaults = {k: v for k, v in defaults.items() if k != "reasoning"}
        st.json(display_defaults)
        
        st.markdown("---")
        
        # Testing controls
        with st.expander("🧪 Testing Controls", expanded=False):
            st.session_state.show_debug = st.checkbox("Show Debug Info", value=st.session_state.get("show_debug", False))
            
            st.markdown("##### Context Controls")
            
            if st.button("Clear Context", help="Clear all user data"):
                st.session_state.db.clear_context(st.session_state.user_id)
                st.session_state.chat_history = []
                st.rerun()
            
            if st.button("Reset to Setup", help="Clear printer setup"):
                st.session_state.db.update_context(
                    st.session_state.user_id,
                    "preference",
                    {"printer_setup": False}
                )
                st.rerun()
            
            st.markdown("---")
            st.markdown("##### Error Simulation")
            
            error_type = st.selectbox(
                "Select Error Type",
                [
                    "Paper jam detected in tray 2",
                    "Wi-Fi connection lost - printer offline",
                    "Low ink - black cartridge empty",
                    "Driver not responding",
                    "Print spooler service stopped",
                    "Paper tray 1 is empty",
                    "Printer door open - close to continue",
                    "Network timeout - cannot reach printer",
                    "USB connection error",
                    "Incompatible paper size loaded"
                ],
                help="Choose which error to simulate",
                key="error_type_selector"
            )
            
            # Store selected error type in session state
            st.session_state.selected_error_type = error_type
            
            if st.button("Simulate Error", help="Create an error session with selected type"):
                st.session_state.db.update_context(
                    st.session_state.user_id, 
                    "session",
                    {
                        "status": "error",
                        "error_message": error_type,
                        "session_data": {
                            "error_type": error_type,
                            "error_timestamp": datetime.datetime.now().isoformat(),
                            "error_source": "manual_simulation"
                        }
                    }
                )
                st.rerun()
            
            st.markdown("---")
            st.markdown("##### Scenario Simulation")
            
            scenario_category = st.radio(
                "Scenario Category",
                ["Connection Mode", "Setup Flow", "Print Flow", "Quick Context"],
                help="Choose scenario type to simulate"
            )
            
            if scenario_category == "Connection Mode":
                scenario = st.selectbox(
                    "Connection Setup Scenario",
                    [
                        "Wi-Fi network available → Setup printer",
                        "USB printer detected → Setup",
                        "Bluetooth device found → Setup",
                        "Network printer (IPP) discovered",
                        "Network printer (WSD) discovered",
                        "Multiple connection options available"
                    ]
                )
                
                if st.button("Apply Connection Scenario"):
                    # Clear context first for fresh setup
                    st.session_state.db.clear_context(st.session_state.user_id)
                    
                    # Create session data indicating connection mode intent
                    if "Wi-Fi" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "session",
                            {
                                "status": "success",
                                "session_data": {
                                    "network_available": True,
                                    "wifi_ssid": "HomeNetwork_5G",
                                    "connection_mode": "wifi",
                                    "detected_printers": [
                                        {"name": "HP LaserJet Pro", "ip": "192.168.1.105", "type": "IPP"},
                                        {"name": "Canon PIXMA", "ip": "192.168.1.108", "type": "WSD"}
                                    ]
                                }
                            }
                        )
                        st.info("📡 **Wi-Fi Network Detected**\n\nSSID: HomeNetwork_5G\n\nScanning for printers on network...")
                    
                    elif "USB" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "session",
                            {
                                "status": "success",
                                "session_data": {
                                    "connection_mode": "usb",
                                    "detected_printers": [
                                        {"name": "HP DeskJet 3755", "port": "USB001", "type": "USB"}
                                    ]
                                }
                            }
                        )
                        st.info("🔌 **USB Printer Detected**\n\nPort: USB001\n\nModel: HP DeskJet 3755")
                    
                    elif "Bluetooth" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "session",
                            {
                                "status": "success",
                                "session_data": {
                                    "connection_mode": "bluetooth",
                                    "detected_printers": [
                                        {"name": "Epson EcoTank", "mac": "AA:BB:CC:DD:EE:FF", "type": "Bluetooth"}
                                    ]
                                }
                            }
                        )
                        st.info("🔵 **Bluetooth Device Found**\n\nDevice: Epson EcoTank\n\nReady to pair")
                    
                    elif "IPP" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "session",
                            {
                                "status": "success",
                                "session_data": {
                                    "network_available": True,
                                    "connection_mode": "network",
                                    "protocol": "IPP",
                                    "detected_printers": [
                                        {"name": "HP LaserJet Pro M404dn", "ip": "192.168.1.105", "type": "IPP", "uri": "ipp://192.168.1.105/ipp/print"}
                                    ]
                                }
                            }
                        )
                        st.info("🌐 **Network Printer Found (IPP)**\n\nIP: 192.168.1.105\n\nModel: HP LaserJet Pro M404dn")
                    
                    elif "WSD" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "session",
                            {
                                "status": "success",
                                "session_data": {
                                    "network_available": True,
                                    "connection_mode": "network",
                                    "protocol": "WSD",
                                    "detected_printers": [
                                        {"name": "Canon PIXMA TR8620", "ip": "192.168.1.108", "type": "WSD"}
                                    ]
                                }
                            }
                        )
                        st.info("🌐 **Network Printer Found (WSD)**\n\nIP: 192.168.1.108\n\nModel: Canon PIXMA TR8620")
                    
                    elif "Multiple" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "session",
                            {
                                "status": "success",
                                "session_data": {
                                    "network_available": True,
                                    "connection_mode": "multiple",
                                    "detected_printers": [
                                        {"name": "HP LaserJet Pro", "ip": "192.168.1.105", "type": "IPP"},
                                        {"name": "HP DeskJet 3755", "port": "USB001", "type": "USB"},
                                        {"name": "Epson EcoTank", "mac": "AA:BB:CC:DD:EE:FF", "type": "Bluetooth"}
                                    ]
                                }
                            }
                        )
                        st.info("📡 **Multiple Connection Options**\n\n✓ Wi-Fi (2 printers)\n✓ USB (1 printer)\n✓ Bluetooth (1 printer)")
                    
                    st.success(f"✅ Applied: {scenario}")
                    st.warning("⚙️ **Setup Required** - Navigate to main screen to begin printer setup")
                    st.rerun()
            
            elif scenario_category == "Setup Flow":
                scenario = st.selectbox(
                    "Setup Scenario",
                    [
                        "First-time user (no printer)",
                        "Printer configured (HP DeskJet)",
                        "Printer configured (Canon PIXMA)",
                        "Multiple printers configured"
                    ]
                )
                
                if st.button("Apply Setup Scenario"):
                    if "First-time" in scenario:
                        st.session_state.db.clear_context(st.session_state.user_id)
                    elif "HP DeskJet" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "preference",
                            {
                                "printer_setup": True,
                                "last_printer_model": "HP DeskJet 3755",
                                "default_color_mode": "black_white",
                                "default_paper_size": "A4"
                            }
                        )
                    elif "Canon PIXMA" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "preference",
                            {
                                "printer_setup": True,
                                "last_printer_model": "Canon PIXMA TR8620",
                                "default_color_mode": "color",
                                "default_paper_size": "Letter"
                            }
                        )
                    st.success(f"✅ Applied: {scenario}")
                    st.rerun()
            
            elif scenario_category == "Print Flow":
                scenario = st.selectbox(
                    "Print Scenario",
                    [
                        "Recent B&W prints (x5)",
                        "Recent color prints (x5)",
                        "Mixed print history",
                        "High-quality pattern (x8)",
                        "Draft mode pattern (x8)",
                        "Large job history (50+ pages)"
                    ]
                )
                
                if st.button("Apply Print Scenario"):
                    # Clear existing usage history
                    st.session_state.db.clear_usage_history(st.session_state.user_id)
                    
                    if "Recent B&W" in scenario:
                        for i in range(5):
                            st.session_state.db.add_to_usage_history(
                                st.session_state.user_id,
                                "black_white", "A4", 2, "high"
                            )
                    elif "Recent color" in scenario:
                        for i in range(5):
                            st.session_state.db.add_to_usage_history(
                                st.session_state.user_id,
                                "color", "A4", 1, "high"
                            )
                    elif "Mixed" in scenario:
                        for i in range(3):
                            st.session_state.db.add_to_usage_history(
                                st.session_state.user_id,
                                "black_white", "A4", 2, "standard"
                            )
                        for i in range(2):
                            st.session_state.db.add_to_usage_history(
                                st.session_state.user_id,
                                "color", "Letter", 1, "high"
                            )
                    elif "High-quality" in scenario:
                        for i in range(8):
                            st.session_state.db.add_to_usage_history(
                                st.session_state.user_id,
                                "black_white", "A4", 2, "high"
                            )
                    elif "Draft mode" in scenario:
                        for i in range(8):
                            st.session_state.db.add_to_usage_history(
                                st.session_state.user_id,
                                "black_white", "A4", 1, "draft"
                            )
                    
                    st.success(f"✅ Applied: {scenario}")
                    st.rerun()
            
            elif scenario_category == "Quick Context":
                scenario = st.selectbox(
                    "Quick Scenario",
                    [
                        "B&W high-quality user",
                        "Color photo enthusiast",
                        "Budget-conscious (draft mode)",
                        "Default settings user"
                    ]
                )
                
                if st.button("Apply Quick Scenario"):
                    # Clear and setup
                    st.session_state.db.clear_usage_history(st.session_state.user_id)
                    
                    if "B&W high-quality" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "preference",
                            {
                                "printer_setup": True,
                                "last_printer_model": "HP LaserJet Pro",
                                "default_color_mode": "black_white",
                                "default_paper_size": "A4"
                            }
                        )
                        for i in range(8):
                            st.session_state.db.add_to_usage_history(
                                st.session_state.user_id,
                                "black_white", "A4", 2, "high"
                            )
                    elif "Color photo" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "preference",
                            {
                                "printer_setup": True,
                                "last_printer_model": "Canon PIXMA TR8620",
                                "default_color_mode": "color",
                                "default_paper_size": "Letter"
                            }
                        )
                        for i in range(6):
                            st.session_state.db.add_to_usage_history(
                                st.session_state.user_id,
                                "color", "Letter", 1, "high"
                            )
                    elif "Budget-conscious" in scenario:
                        st.session_state.db.update_context(
                            st.session_state.user_id,
                            "preference",
                            {
                                "printer_setup": True,
                                "last_printer_model": "HP DeskJet 3755",
                                "default_color_mode": "black_white",
                                "default_paper_size": "A4"
                            }
                        )
                        for i in range(10):
                            st.session_state.db.add_to_usage_history(
                                st.session_state.user_id,
                                "black_white", "A4", 1, "draft"
                            )
                    
                    st.success(f"✅ Applied: {scenario}")
                    st.rerun()


def render_setup_flow():
    """Render printer setup flow."""
    st.header("🔧 Printer Setup")
    
    # Check if we have connection mode information from scenario
    db = st.session_state.db
    context = db.get_user_context(st.session_state.user_id)
    
    connection_info = None
    detected_printers = []
    
    if context.get("sessions"):
        latest_session = context["sessions"][0]
        session_data_str = latest_session.get("session_data")
        if session_data_str:
            try:
                session_data = json.loads(session_data_str)
                # Handle double-encoded JSON from old data
                if isinstance(session_data, str):
                    session_data = json.loads(session_data)
                if "connection_mode" in session_data:
                    connection_info = session_data
                    detected_printers = session_data.get("detected_printers", [])
            except json.JSONDecodeError:
                pass
    
    # Show connection mode information if available
    if connection_info:
        connection_mode = connection_info.get("connection_mode", "network")
        
        if connection_mode == "wifi":
            wifi_ssid = connection_info.get("wifi_ssid", "Unknown")
            st.info(f"📡 **Wi-Fi Network Detected**: {wifi_ssid}")
            st.write(f"Found {len(detected_printers)} printer(s) on the network. Click to configure:")
            for i, printer in enumerate(detected_printers):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{printer.get('name')}** ({printer.get('type')}) - IP: {printer.get('ip')}")
                with col2:
                    if st.button("Configure", key=f"wifi_printer_{i}"):
                        st.session_state.agent.save_printer_setup(
                            st.session_state.user_id,
                            printer.get('name'),
                            {"default_color_mode": "black_white", "default_paper_size": "A4"}
                        )
                        st.success(f"✅ {printer.get('name')} configured!")
                        st.balloons()
                        st.session_state.current_flow = None
                        st.rerun()
        
        elif connection_mode == "usb":
            st.info("🔌 **USB Printer Detected**")
            if detected_printers:
                printer = detected_printers[0]
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{printer.get('name')}** on {printer.get('port')}")
                with col2:
                    if st.button("Configure", key="usb_printer"):
                        st.session_state.agent.save_printer_setup(
                            st.session_state.user_id,
                            printer.get('name'),
                            {"default_color_mode": "black_white", "default_paper_size": "A4"}
                        )
                        st.success(f"✅ {printer.get('name')} configured!")
                        st.balloons()
                        st.session_state.current_flow = None
                        st.rerun()
        
        elif connection_mode == "bluetooth":
            st.info("🔵 **Bluetooth Printer Detected**")
            if detected_printers:
                printer = detected_printers[0]
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{printer.get('name')}** (MAC: {printer.get('mac')})")
                with col2:
                    if st.button("Configure", key="bt_printer"):
                        st.session_state.agent.save_printer_setup(
                            st.session_state.user_id,
                            printer.get('name'),
                            {"default_color_mode": "black_white", "default_paper_size": "A4"}
                        )
                        st.success(f"✅ {printer.get('name')} configured!")
                        st.balloons()
                        st.session_state.current_flow = None
                        st.rerun()
        
        elif connection_mode == "network":
            protocol = connection_info.get("protocol", "Network")
            st.info(f"🌐 **{protocol} Network Printer Discovered**")
            if detected_printers:
                printer = detected_printers[0]
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{printer.get('name')}** - IP: {printer.get('ip')}")
                    if "uri" in printer:
                        st.caption(f"URI: {printer.get('uri')}")
                with col2:
                    if st.button("Configure", key="network_printer"):
                        st.session_state.agent.save_printer_setup(
                            st.session_state.user_id,
                            printer.get('name'),
                            {"default_color_mode": "black_white", "default_paper_size": "A4"}
                        )
                        st.success(f"✅ {printer.get('name')} configured!")
                        st.balloons()
                        st.session_state.current_flow = None
                        st.rerun()
        
        elif connection_mode == "multiple":
            st.info("📡 **Multiple Connection Options Available**")
            st.write("Click on any printer to configure:")
            
            wifi_printers = [p for p in detected_printers if p.get('type') in ['IPP', 'WSD']]
            usb_printers = [p for p in detected_printers if p.get('type') == 'USB']
            bt_printers = [p for p in detected_printers if p.get('type') == 'Bluetooth']
            
            if wifi_printers:
                st.write(f"**Wi-Fi** ({len(wifi_printers)} printer(s)):")
                for i, p in enumerate(wifi_printers):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"  • {p.get('name')} - {p.get('ip')}")
                    with col2:
                        if st.button("Configure", key=f"multi_wifi_{i}"):
                            st.session_state.agent.save_printer_setup(
                                st.session_state.user_id,
                                p.get('name'),
                                {"default_color_mode": "black_white", "default_paper_size": "A4"}
                            )
                            st.success(f"✅ {p.get('name')} configured!")
                            st.balloons()
                            st.session_state.current_flow = None
                            st.rerun()
            if usb_printers:
                st.write(f"**USB** ({len(usb_printers)} printer(s)):")
                for i, p in enumerate(usb_printers):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"  • {p.get('name')} - {p.get('port')}")
                    with col2:
                        if st.button("Configure", key=f"multi_usb_{i}"):
                            st.session_state.agent.save_printer_setup(
                                st.session_state.user_id,
                                p.get('name'),
                                {"default_color_mode": "black_white", "default_paper_size": "A4"}
                            )
                            st.success(f"✅ {p.get('name')} configured!")
                            st.balloons()
                            st.session_state.current_flow = None
                            st.rerun()
            if bt_printers:
                st.write(f"**Bluetooth** ({len(bt_printers)} printer(s)):")
                for i, p in enumerate(bt_printers):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"  • {p.get('name')}")
                    with col2:
                        if st.button("Configure", key=f"multi_bt_{i}"):
                            st.session_state.agent.save_printer_setup(
                                st.session_state.user_id,
                                p.get('name'),
                                {"default_color_mode": "black_white", "default_paper_size": "A4"}
                            )
                            st.success(f"✅ {p.get('name')} configured!")
                            st.balloons()
                            st.session_state.current_flow = None
                            st.rerun()
        
        st.markdown("---")
        st.write("💡 **Tip**: Click 'Configure' for quick setup with defaults, or use the form below for custom preferences.")
    else:
        st.write("Let's get your printer configured!")
    
    with st.form("setup_form"):
        # Pre-populate printer model if detected
        default_model = ""
        if detected_printers and len(detected_printers) == 1:
            default_model = detected_printers[0].get("name", "")
        
        printer_model = st.text_input(
            "Printer Model",
            value=default_model,
            placeholder="e.g., HP DeskJet 3755, Canon PIXMA TR8620",
            help="Enter your printer model name or select from detected printers"
        )
        
        # Show dropdown if multiple printers detected
        if len(detected_printers) > 1:
            printer_options = [p.get("name", f"Printer {i+1}") for i, p in enumerate(detected_printers)]
            selected_printer = st.selectbox(
                "Or select from detected printers:",
                [""] + printer_options
            )
            if selected_printer:
                printer_model = selected_printer
        
        st.subheader("Default Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_color = st.selectbox(
                "Default Color Mode",
                ["black_white", "color"],
                help="Your preferred color mode for most prints"
            )
        
        with col2:
            default_paper = st.selectbox(
                "Default Paper Size",
                ["A4", "Letter", "Legal", "A3"],
                help="Your most commonly used paper size"
            )
        
        submitted = st.form_submit_button("Complete Setup", type="primary")
        
        if submitted:
            if printer_model:
                # Save setup
                st.session_state.agent.save_printer_setup(
                    st.session_state.user_id,
                    printer_model,
                    {
                        "default_color_mode": default_color,
                        "default_paper_size": default_paper
                    }
                )
                st.success(f"✅ {printer_model} configured successfully!")
                st.balloons()
                st.session_state.current_flow = None
                st.rerun()
            else:
                st.error("Please enter a printer model")


def render_troubleshoot_flow(agent_response):
    """Render troubleshooting flow."""
    st.header("🔍 Troubleshooting Required")
    
    # Display warning banner
    st.warning("⚠️ **An error was detected in your last print session. Please resolve it before continuing.**")
    
    # Display the error details
    error_msg = agent_response.get("ui_directive", {}).get("message", "An error was detected")
    st.error(error_msg)
    
    st.markdown("---")
    
    # Display AI recommendation
    st.subheader("💡 AI Recommendation")
    with st.container():
        st.info(agent_response.get("response", "Let me help you resolve this issue."))
    
    st.markdown("---")
    
    # Action buttons
    st.subheader("What would you like to do?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ I've Resolved the Issue", type="primary", use_container_width=True):
            # Get the original error from context to preserve it in resolution
            context = st.session_state.db.get_user_context(st.session_state.user_id)
            original_error = "Unknown error"
            if context.get("sessions"):
                for session in context["sessions"]:
                    if session.get("status") == "error" and session.get("error_message"):
                        original_error = session.get("error_message")
                        break
            
            # Clear the error by creating a RESOLVED session with details
            st.session_state.db.update_context(
                st.session_state.user_id,
                "session",
                {
                    "status": "resolved",
                    "session_data": {
                        "troubleshooting": "user_confirmed_resolved",
                        "original_error": original_error,
                        "resolved_at": datetime.datetime.now().isoformat(),
                        "resolution_method": "manual"
                    }
                }
            )
            st.success("✅ Great! You can now proceed with printing.")
            st.session_state.current_flow = None
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button("💬 I Need More Help", use_container_width=True):
            st.session_state.current_flow = "chat"
            st.rerun()
    
    st.markdown("")
    st.caption("Note: You must resolve the error before you can print. Use 'I Need More Help' to chat with the AI assistant.")


def render_print_flow(agent_response):
    """Render print job configuration flow."""
    st.header("🖨️ Print Job")
    
    # Get smart defaults
    defaults = agent_response.get("smart_defaults", {})
    ui_defaults = agent_response.get("ui_directive", {}).get("defaults", defaults)
    ai_reasoning = agent_response.get("ai_reasoning", "") or ui_defaults.get("reasoning", "")
    
    # Display AI message
    if agent_response.get("response"):
        st.info(f"💡 {agent_response['response']}")
    
    # Show AI reasoning if available
    if ai_reasoning and agent_response.get("is_ai_powered"):
        with st.expander("🤖 Why these defaults? (AI Reasoning)", expanded=False):
            st.write(f"**AI Analysis:** {ai_reasoning}")
            st.caption("The AI analyzed your recent printing behavior to suggest these settings.")
    
    with st.form("print_form"):
        st.subheader("Print Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            color_mode = st.radio(
                "Color Mode",
                ["color", "black_white"],
                index=0 if ui_defaults.get("color_mode") == "color" else 1,
                help="Choose color or black & white printing"
            )
            
            paper_size = st.selectbox(
                "Paper Size",
                ["A4", "Letter", "Legal", "A3"],
                index=["A4", "Letter", "Legal", "A3"].index(ui_defaults.get("paper_size", "A4")),
                help="Select paper size"
            )
        
        with col2:
            num_copies = st.number_input(
                "Number of Copies",
                min_value=1,
                max_value=100,
                value=ui_defaults.get("num_copies", 1),
                help="How many copies to print"
            )
            
            print_quality = st.selectbox(
                "Print Quality",
                ["draft", "normal", "high"],
                index=["draft", "normal", "high"].index(ui_defaults.get("print_quality", "normal")),
                help="Select print quality"
            )
        
        col_submit1, col_submit2 = st.columns([1, 3])
        
        with col_submit1:
            print_submitted = st.form_submit_button("🖨️ Print", type="primary")
        
        with col_submit2:
            simulate_error = st.form_submit_button("⚠️ Simulate Error", type="secondary")
        
        if print_submitted:
            # Record successful print job with detailed metadata
            print_settings = {
                "color_mode": color_mode,
                "paper_size": paper_size,
                "num_copies": num_copies,
                "print_quality": print_quality,
                "print_job_id": f"JOB_{int(time.time())}",
                "timestamp": datetime.datetime.now().isoformat(),
                "status": "completed"
            }
            
            st.session_state.agent.process_print_job(
                st.session_state.user_id,
                print_settings,
                success=True
            )
            
            st.success(f"✅ Print job sent! ({num_copies} {'copy' if num_copies == 1 else 'copies'}, {color_mode}, {paper_size})")
            st.session_state.current_flow = None
            
            # Small delay for user to see success message
            time.sleep(1)
            st.rerun()
        
        if simulate_error:
            # Get error type from session state sidebar selection
            error_message = st.session_state.get("selected_error_type", "Paper jam detected in tray 2")
            
            # Record failed print job with detailed error
            print_settings = {
                "color_mode": color_mode,
                "paper_size": paper_size,
                "num_copies": num_copies,
                "print_quality": print_quality,
                "error_message": error_message,
                "print_job_id": f"JOB_{int(time.time())}",
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            st.session_state.agent.process_print_job(
                st.session_state.user_id,
                print_settings,
                success=False
            )
            
            st.error(f"⚠️ Print job failed: {error_message}")
            st.session_state.current_flow = None
            
            time.sleep(1)
            st.rerun()


def render_chat_interface():
    """Render chat interface for general questions."""
    st.header("💬 Chat with Print Assistant")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask me anything about printing...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Get agent response
        if st.session_state.agent_ready:
            response = st.session_state.agent.process(
                user_input,
                st.session_state.user_id
            )
            
            # Add assistant response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["response"]
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "I'm sorry, the AI agent is not available. Please ensure Ollama is running with llama3.1 model."
            })
        
        st.rerun()


def main():
    """Main application entry point."""
    initialize_session_state()
    
    # Render sidebar
    sidebar_controls()
    
    # Check if Ollama is available
    if not st.session_state.agent_ready:
        st.error("⚠️ AI Agent Not Available")
        st.warning(f"Error: {st.session_state.get('agent_error', 'Unknown error')}")
        st.info("💡 **Make sure Ollama is running:** Run `ollama run llama3.1` in your terminal before starting this app.")
        st.code("ollama run llama3.1", language="bash")
        
        if st.button("Retry Connection"):
            try:
                st.session_state.agent = get_agent(st.session_state.db, "llama3.1")
                st.session_state.agent_ready = True
                st.rerun()
            except Exception as e:
                st.error(f"Still unable to connect: {str(e)}")
        
        return
    
    # Main content area
    st.title("🖨️ Context-Aware Print Manager")
    
    # ALWAYS re-evaluate flow based on current context (don't cache)
    # This ensures errors are caught immediately
    if st.session_state.current_flow is None:
        response = st.session_state.agent.process(
            user_input=None,
            user_id=st.session_state.user_id
        )
        # Always respect the agent's flow decision based on context
        st.session_state.current_flow = response["ui_directive"].get("flow")
        st.session_state.last_response = response
        
        # Fallback only if agent didn't set a flow
        if not st.session_state.current_flow:
            st.session_state.current_flow = "print"
    
    # Debug info (can be removed in production)
    if st.session_state.get("show_debug", False):
        with st.expander("🐛 Debug Info"):
            st.write("**Current Flow:**", st.session_state.current_flow)
            st.write("**Last Intent:**", st.session_state.last_response.get("intent"))
            st.write("**🤖 AI Reasoning:**", st.session_state.last_response.get("ai_reasoning", "N/A"))
            st.write("**AI-Powered:**", st.session_state.last_response.get("is_ai_powered", False))
            st.write("**UI Directive:**", st.session_state.last_response.get("ui_directive"))
    
    # Render appropriate flow
    if st.session_state.current_flow == "setup":
        render_setup_flow()
    elif st.session_state.current_flow == "troubleshoot":
        render_troubleshoot_flow(st.session_state.get("last_response", {}))
    elif st.session_state.current_flow == "print":
        render_print_flow(st.session_state.get("last_response", {}))
    elif st.session_state.current_flow == "chat":
        render_chat_interface()
    
    # Quick actions
    st.markdown("---")
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🖨️ New Print Job", use_container_width=True):
            # Let agent decide the flow based on context (may show error first)
            response = st.session_state.agent.process(
                user_input=None,
                user_id=st.session_state.user_id
            )
            st.session_state.current_flow = response["ui_directive"].get("flow", "print")
            st.session_state.last_response = response
            st.rerun()
    
    with col2:
        if st.button("💬 Ask a Question", use_container_width=True):
            st.session_state.current_flow = "chat"
            st.rerun()
    
    with col3:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_flow = "setup"
            st.rerun()


if __name__ == "__main__":
    main()
