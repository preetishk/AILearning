"""
Agent Logic for Context-Aware Print Management Application
Uses LangGraph and Ollama (Llama 3.1) for intelligent print job management.
"""

from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from db import ContextDatabase
import json


# Define the state structure
class AgentState(TypedDict):
    """State for the print management agent."""
    messages: list
    context_summary: str
    detected_intent: str
    user_id: str
    ui_directive: dict
    raw_context: dict
    ai_reasoning: str  # AI's reasoning for decisions
    recommended_defaults: dict  # AI-recommended smart defaults


class PrintManagementAgent:
    """
    Context-aware print management agent using LangGraph.
    Analyzes user context to determine intent and provide intelligent responses.
    """
    
    INTENTS = {
        "SETUP_REQUIRED": "User needs to set up printer",
        "TROUBLESHOOT_ERROR": "User needs help with a printer error",
        "STANDARD_PRINT_COLOR": "User wants to print in color",
        "STANDARD_PRINT_BW": "User wants to print in black and white",
        "GENERAL_CHAT": "General conversation or question",
        "CHANGE_SETTINGS": "User wants to change printer settings"
    }
    
    def __init__(self, db: ContextDatabase, model_name: str = "llama3.1"):
        """
        Initialize the agent.
        
        Args:
            db: ContextDatabase instance
            model_name: Ollama model name (default: llama3.1)
        """
        self.db = db
        self.llm = ChatOllama(model=model_name, temperature=0.7)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("fetch_context", self._fetch_context)
        workflow.add_node("analyze_intent", self._analyze_intent)
        workflow.add_node("handle_setup", self._handle_setup)
        workflow.add_node("handle_troubleshoot", self._handle_troubleshoot)
        workflow.add_node("handle_print", self._handle_print)
        workflow.add_node("handle_chat", self._handle_chat)
        workflow.add_node("respond", self._respond)
        
        # Set entry point
        workflow.set_entry_point("fetch_context")
        
        # Add edges
        workflow.add_edge("fetch_context", "analyze_intent")
        
        # Conditional routing based on intent
        workflow.add_conditional_edges(
            "analyze_intent",
            self._route_by_intent,
            {
                "SETUP_REQUIRED": "handle_setup",
                "TROUBLESHOOT_ERROR": "handle_troubleshoot",
                "STANDARD_PRINT_COLOR": "handle_print",
                "STANDARD_PRINT_BW": "handle_print",
                "CHANGE_SETTINGS": "handle_chat",
                "GENERAL_CHAT": "handle_chat"
            }
        )
        
        # All handlers lead to respond
        workflow.add_edge("handle_setup", "respond")
        workflow.add_edge("handle_troubleshoot", "respond")
        workflow.add_edge("handle_print", "respond")
        workflow.add_edge("handle_chat", "respond")
        
        # End after respond
        workflow.add_edge("respond", END)
        
        return workflow.compile()
    
    def _fetch_context(self, state: AgentState) -> AgentState:
        """Fetch user context from database."""
        user_id = state.get("user_id", "default")
        
        # Get raw context
        raw_context = self.db.get_user_context(user_id)
        
        # Get natural language summary
        context_summary = self.db.summarize_context(user_id)
        
        state["raw_context"] = raw_context
        state["context_summary"] = context_summary
        
        return state
    
    def _analyze_intent(self, state: AgentState) -> AgentState:
        """AI-powered intent analysis using LLM to understand context and user needs."""
        user_id = state.get("user_id", "default")
        raw_context = state["raw_context"]
        messages = state.get("messages", [])
        context_summary = state["context_summary"]
        
        # Check for connection mode scenario in session data
        if raw_context.get("sessions"):
            latest_session = raw_context["sessions"][0]
            session_data_str = latest_session.get("session_data")
            if session_data_str:
                try:
                    session_data = json.loads(session_data_str)
                    # Handle double-encoded JSON from old data
                    if isinstance(session_data, str):
                        session_data = json.loads(session_data)
                    if "connection_mode" in session_data:
                        state["detected_intent"] = "SETUP_REQUIRED"
                        connection_info = session_data.get("connection_mode", "network")
                        detected_printers = session_data.get("detected_printers", [])
                        
                        if connection_info == "wifi":
                            wifi_ssid = session_data.get("wifi_ssid", "Unknown")
                            state["ai_reasoning"] = f"Wi-Fi network '{wifi_ssid}' detected with {len(detected_printers)} printer(s) available. Guiding user through Wi-Fi printer setup."
                        elif connection_info == "usb":
                            state["ai_reasoning"] = f"USB printer detected. Guiding user through USB printer setup."
                        elif connection_info == "bluetooth":
                            state["ai_reasoning"] = f"Bluetooth printer detected. Guiding user through Bluetooth printer setup."
                        elif connection_info == "network":
                            protocol = session_data.get("protocol", "Network")
                            state["ai_reasoning"] = f"{protocol} network printer discovered. Guiding user through network printer setup."
                        elif connection_info == "multiple":
                            state["ai_reasoning"] = f"Multiple connection options available ({len(detected_printers)} printer(s)). User can choose preferred connection method."
                        
                        return state
                except json.JSONDecodeError:
                    pass
        
        # First check critical blocking conditions (still rule-based for safety)
        if not self.db.has_printer_setup(user_id):
            state["detected_intent"] = "SETUP_REQUIRED"
            state["ai_reasoning"] = "No printer configured. Setup is required before printing."
            return state
        
        if self._has_unresolved_error(user_id, raw_context):
            state["detected_intent"] = "TROUBLESHOOT_ERROR"
            state["ai_reasoning"] = "Unresolved printer error must be addressed before continuing."
            return state
        
        # AI-POWERED INTENT DETECTION
        # Let the LLM analyze the full context and determine user intent
        user_message = ""
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, HumanMessage):
                user_message = last_message.content
        
        # Get AI-recommended smart defaults first
        ai_defaults = self._get_ai_smart_defaults(raw_context, context_summary)
        state["recommended_defaults"] = ai_defaults
        
        # Prepare context for AI intent analysis
        intent_prompt = f"""You are an intelligent print management assistant. Analyze the context and determine the user's intent.

CONTEXT:
{context_summary}

RECENT ACTIVITY:
{self._format_recent_activity(raw_context)}

USER INPUT: {user_message if user_message else "(User opened the app without specific request)"}

AVAILABLE INTENTS:
1. SETUP_REQUIRED - User needs to configure printer
2. TROUBLESHOOT_ERROR - User has a printer error to fix
3. STANDARD_PRINT_COLOR - User wants to print in color
4. STANDARD_PRINT_BW - User wants to print in black and white  
5. CHANGE_SETTINGS - User wants to change printer settings
6. GENERAL_CHAT - User has questions or wants to chat

Based on the context and user input, what is the most likely intent?

Respond in JSON format:
{{
  "intent": "<one of the intents above>",
  "reasoning": "<brief explanation of why you chose this intent>",
  "confidence": "<high/medium/low>"
}}"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=intent_prompt)])
            result = json.loads(response.content)
            
            state["detected_intent"] = result.get("intent", "GENERAL_CHAT")
            state["ai_reasoning"] = result.get("reasoning", "AI analysis of user context")
            
        except Exception as e:
            # Fallback to simple logic if AI fails
            if user_message:
                if "error" in user_message.lower() or "problem" in user_message.lower():
                    state["detected_intent"] = "TROUBLESHOOT_ERROR"
                elif "color" in user_message.lower():
                    state["detected_intent"] = "STANDARD_PRINT_COLOR"
                else:
                    state["detected_intent"] = "STANDARD_PRINT_BW"
            else:
                # Use AI-recommended defaults
                if ai_defaults.get("color_mode") == "color":
                    state["detected_intent"] = "STANDARD_PRINT_COLOR"
                else:
                    state["detected_intent"] = "STANDARD_PRINT_BW"
            
            state["ai_reasoning"] = "Using fallback intent detection"
        
        return state
    
    def _get_ai_smart_defaults(self, raw_context: dict, context_summary: str) -> dict:
        """AI-powered smart defaults recommendation based on user behavior patterns."""
        # Get statistical defaults as baseline
        fallback_defaults = {
            "color_mode": "black_white",
            "paper_size": "A4",
            "num_copies": 1,
            "print_quality": "normal"
        }
        
        if not raw_context.get("usage_history"):
            return fallback_defaults
        
        # Format recent usage for AI
        recent_usage = raw_context["usage_history"][:10]
        usage_summary = "\n".join([
            f"Print {i+1}: {u.get('color_mode')} | {u.get('print_quality')} quality | {u.get('num_copies')} copies | {u.get('paper_size')} | {'Success' if u.get('success') else 'Failed'}"
            for i, u in enumerate(recent_usage)
        ])
        
        ai_prompt = f"""You are an intelligent print assistant. Analyze the user's recent printing behavior and recommend optimal default settings.

USER CONTEXT:
{context_summary}

RECENT PRINTS (last 10):
{usage_summary}

TASK:
Based on the patterns you see in the last 5 prints, recommend smart defaults for:
1. color_mode (color or black_white)
2. paper_size (A4, Letter, Legal, A3)
3. num_copies (1-10)
4. print_quality (draft, normal, high)

Consider:
- Most frequent choices in recent prints (prioritize last 5)
- User's typical workflow patterns
- Quality vs speed trade-offs
- Cost efficiency (color is more expensive)

Respond in JSON format:
{{
  "color_mode": "<color or black_white>",
  "paper_size": "<A4/Letter/Legal/A3>",
  "num_copies": <number>,
  "print_quality": "<draft/normal/high>",
  "reasoning": "<brief explanation of your recommendations>"
}}"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=ai_prompt)])
            result = json.loads(response.content)
            
            return {
                "color_mode": result.get("color_mode", fallback_defaults["color_mode"]),
                "paper_size": result.get("paper_size", fallback_defaults["paper_size"]),
                "num_copies": result.get("num_copies", fallback_defaults["num_copies"]),
                "print_quality": result.get("print_quality", fallback_defaults["print_quality"]),
                "reasoning": result.get("reasoning", "AI analysis of usage patterns")
            }
        except Exception as e:
            # Fallback to statistical approach
            recent_5 = recent_usage[:5]
            if recent_5:
                color_modes = [u.get("color_mode") for u in recent_5 if u.get("color_mode")]
                qualities = [u.get("print_quality") for u in recent_5 if u.get("print_quality")]
                copies = [u.get("num_copies") for u in recent_5 if u.get("num_copies")]
                
                if color_modes:
                    fallback_defaults["color_mode"] = max(set(color_modes), key=color_modes.count)
                if qualities:
                    fallback_defaults["print_quality"] = max(set(qualities), key=qualities.count)
                if copies:
                    fallback_defaults["num_copies"] = round(sum(copies) / len(copies))
            
            return fallback_defaults
    
    def _format_recent_activity(self, raw_context: dict) -> str:
        """Format recent activity for AI consumption."""
        if not raw_context.get("usage_history"):
            return "No recent activity"
        
        recent = raw_context["usage_history"][:5]
        lines = []
        for i, u in enumerate(recent, 1):
            lines.append(
                f"{i}. {u.get('color_mode', 'N/A')} | {u.get('print_quality', 'N/A')} quality | "
                f"{u.get('num_copies', 1)} copies | {u.get('paper_size', 'A4')}"
            )
        return "\n".join(lines)
    
    def _has_unresolved_error(self, user_id: str, raw_context: dict) -> bool:
        """Check if there are any unresolved errors that block printing."""
        # Check last session status first
        last_status = self.db.get_last_session_status(user_id)
        if last_status == "error":
            return True
        
        # Check if any recent session (last 5) has an error not followed by success
        if raw_context.get("sessions"):
            sessions = raw_context["sessions"]  # Already sorted by timestamp DESC
            
            # Look through recent sessions
            for i, session in enumerate(sessions[:5]):
                if session.get("status") == "error":
                    # Check if there's ANY newer session with success/resolved status
                    # (newer sessions appear BEFORE in the list since it's DESC order)
                    has_resolution = any(
                        s.get("status") in ["success", "setup_complete", "resolved"]
                        for s in sessions[:i]  # Sessions BEFORE (newer than) this error
                    )
                    if not has_resolution:
                        # Found unresolved error
                        return True
        
        return False
    
    def _route_by_intent(self, state: AgentState) -> str:
        """Route to appropriate handler based on detected intent."""
        return state["detected_intent"]
    
    def _handle_setup(self, state: AgentState) -> AgentState:
        """Handle printer setup flow."""
        state["ui_directive"] = {
            "flow": "setup",
            "message": "Welcome! Let's set up your printer first.",
            "action": "show_setup_form"
        }
        
        # Generate helpful message
        system_msg = SystemMessage(content="You are a helpful printer setup assistant.")
        user_msg = HumanMessage(content="User needs to set up their printer. Provide a brief, friendly welcome message encouraging them to start the setup process.")
        
        response = self.llm.invoke([system_msg, user_msg])
        
        state["messages"].append(AIMessage(content=response.content))
        
        return state
    
    def _handle_troubleshoot(self, state: AgentState) -> AgentState:
        """Handle troubleshooting flow."""
        context = state["raw_context"]
        
        # Get the last error
        error_msg = "Unknown error"
        if context["sessions"]:
            last_error = next((s for s in context["sessions"] if s.get("status") == "error"), None)
            if last_error:
                error_msg = last_error.get("error_message", "Unknown error")
        
        state["ui_directive"] = {
            "flow": "troubleshoot",
            "message": f"I noticed there was an error: {error_msg}",
            "action": "show_troubleshoot_options"
        }
        
        # Get LLM's troubleshooting advice
        system_msg = SystemMessage(content=f"""You are a helpful printer troubleshooting assistant.
User context: {state['context_summary']}""")
        
        user_msg = HumanMessage(content=f"The user encountered this error: {error_msg}. Provide specific troubleshooting steps.")
        
        response = self.llm.invoke([system_msg, user_msg])
        
        state["messages"].append(AIMessage(content=response.content))
        
        return state
    
    def _handle_print(self, state: AgentState) -> AgentState:
        """Handle standard print job with AI-recommended defaults."""
        user_id = state.get("user_id", "default")
        
        # Use AI-recommended defaults from the analyze phase
        ai_defaults = state.get("recommended_defaults", {})
        
        # If no AI defaults, fallback to statistical
        if not ai_defaults:
            ai_defaults = self.db.get_smart_defaults(user_id)
            ai_defaults["reasoning"] = "Based on your recent printing patterns"
        
        intent = state["detected_intent"]
        is_color = "COLOR" in intent
        
        state["ui_directive"] = {
            "flow": "print",
            "message": "Ready to print!",
            "action": "show_print_form",
            "defaults": {
                "color_mode": "color" if is_color else ai_defaults.get("color_mode", "black_white"),
                "paper_size": ai_defaults.get("paper_size", "A4"),
                "num_copies": ai_defaults.get("num_copies", 1),
                "print_quality": ai_defaults.get("print_quality", "normal")
            },
            "ai_reasoning": ai_defaults.get("reasoning", state.get("ai_reasoning", ""))
        }
        
        # Generate contextual message with reasoning
        system_msg = SystemMessage(content=f"""You are a helpful print assistant.
User context: {state['context_summary']}

You've analyzed their printing patterns and recommended these defaults:
- Color: {ai_defaults.get('color_mode')}
- Quality: {ai_defaults.get('print_quality')}
- Copies: {ai_defaults.get('num_copies')}
- Paper: {ai_defaults.get('paper_size')}

Reasoning: {ai_defaults.get('reasoning', 'Based on usage patterns')}

Provide a brief, friendly message acknowledging the print request and mentioning the smart defaults if relevant.""")
        
        messages_to_send = [system_msg]
        if state.get("messages"):
            messages_to_send.extend(state["messages"])
        else:
            messages_to_send.append(HumanMessage(content="I want to print something."))
        
        response = self.llm.invoke(messages_to_send)
        
        state["messages"].append(AIMessage(content=response.content))
        
        return state
    
    def _handle_chat(self, state: AgentState) -> AgentState:
        """Handle general chat and questions."""
        system_msg = SystemMessage(content=f"""You are a helpful printer assistant with knowledge about printer setup, troubleshooting, and print settings.
Current user context: {state['context_summary']}

Answer user questions helpfully and concisely. If they ask about printer issues, provide specific troubleshooting steps.""")
        
        messages_to_send = [system_msg]
        if state.get("messages"):
            messages_to_send.extend(state["messages"])
        
        response = self.llm.invoke(messages_to_send)
        
        state["ui_directive"] = {
            "flow": "chat",
            "message": response.content,
            "action": "show_chat_response"
        }
        
        state["messages"].append(AIMessage(content=response.content))
        
        return state
    
    def _respond(self, state: AgentState) -> AgentState:
        """Final response preparation."""
        # State is already prepared by handlers
        return state
    
    def process(self, user_input: str = None, user_id: str = "default") -> dict:
        """
        Process user input and return AI-powered response with personalized recommendations.
        
        Args:
            user_input: Optional user message
            user_id: User identifier
            
        Returns:
            Dictionary containing response, intent, UI directives, and AI reasoning
        """
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=user_input)] if user_input else [],
            "context_summary": "",
            "detected_intent": "",
            "user_id": user_id,
            "ui_directive": {},
            "raw_context": {},
            "ai_reasoning": "",
            "recommended_defaults": {}
        }
        
        # Run the agentic graph
        final_state = self.graph.invoke(initial_state)
        
        # Extract response
        ai_messages = [msg for msg in final_state["messages"] if isinstance(msg, AIMessage)]
        response_text = ai_messages[-1].content if ai_messages else "I'm here to help with your printing needs!"
        
        # Get AI-recommended defaults
        ai_defaults = final_state.get("recommended_defaults", self.db.get_smart_defaults(user_id))
        
        return {
            "response": response_text,
            "intent": final_state["detected_intent"],
            "ui_directive": final_state["ui_directive"],
            "context_summary": final_state["context_summary"],
            "smart_defaults": ai_defaults,
            "ai_reasoning": final_state.get("ai_reasoning", ""),
            "is_ai_powered": True  # Flag to indicate this is AI-driven personalization
        }
    
    def process_print_job(self, user_id: str, print_settings: dict, success: bool = True):
        """
        Record a print job in the database.
        
        Args:
            user_id: User identifier
            print_settings: Print job settings
            success: Whether the job succeeded
        """
        self.db.update_context(user_id, "usage", {
            "color_mode": print_settings.get("color_mode"),
            "paper_size": print_settings.get("paper_size"),
            "num_copies": print_settings.get("num_copies", 1),
            "print_quality": print_settings.get("print_quality"),
            "operation_type": "print",
            "success": success
        })
        
        # Update session
        status = "success" if success else "error"
        self.db.update_context(user_id, "session", {
            "status": status,
            "error_message": print_settings.get("error_message") if not success else None,
            "session_data": print_settings
        })
    
    def save_printer_setup(self, user_id: str, printer_model: str, preferences: dict = None):
        """
        Save printer setup information.
        
        Args:
            user_id: User identifier
            printer_model: Printer model name
            preferences: Additional preferences
        """
        pref_data = {
            "printer_setup": True,
            "last_printer_model": printer_model,
            "default_color_mode": preferences.get("default_color_mode") if preferences else None,
            "default_paper_size": preferences.get("default_paper_size") if preferences else None,
            "preferences_data": preferences or {}
        }
        
        self.db.update_context(user_id, "preference", pref_data)
        
        # Create a success session
        self.db.update_context(user_id, "session", {
            "status": "setup_complete",
            "session_data": {"printer_model": printer_model}
        })


# Convenience function
def get_agent(db: ContextDatabase = None, model_name: str = "llama3.1") -> PrintManagementAgent:
    """Get or create a PrintManagementAgent instance."""
    if db is None:
        from db import get_db
        db = get_db()
    return PrintManagementAgent(db, model_name)
