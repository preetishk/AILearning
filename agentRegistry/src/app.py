import streamlit as st
import pandas as pd
import time
from models import AgentMetadata, AgentType, AgentStatus, CapabilityDefinition
from registry import get_registry

st.set_page_config(page_title="Agent Registry", page_icon="🤖", layout="wide")

st.title("🤖 AI Agent Registry")

# Auto-refresh every 5 seconds to show live status
st_autorefresh = st.empty()
with st_autorefresh:
    st.caption("🔄 Auto-refreshing every 5 seconds for live status updates")
time.sleep(0.1)  # Small delay to ensure caption renders

# Force reload registry data (bypass singleton cache for fresh data)
registry = get_registry()

# Tabs
tab1, tab2, tab3 = st.tabs(["Browse Agents", "Register Agent", "Search"])

with tab1:
    st.header("Registered Agents")
    
    agents = registry.get_all_agents()
    
    if not agents:
        st.info("No agents registered yet.")
    else:
        # Convert to DataFrame for easier display
        data = []
        for agent in agents:
            data.append({
                "ID": agent.id,
                "Name": agent.name,
                "Type": agent.agent_type.value,
                "Status": agent.status.value,
                "Description": agent.description,
                "Tags": ", ".join(agent.tags)
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Detailed View
        st.subheader("Agent Details")
        selected_agent_id = st.selectbox("Select Agent to View Details", [a.id for a in agents], format_func=lambda x: next((a.name for a in agents if a.id == x), x))
        
        if selected_agent_id:
            agent = registry.get_agent(selected_agent_id)
            if agent:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Name:** {agent.name}")
                    st.markdown(f"**ID:** `{agent.id}`")
                    st.markdown(f"**Version:** {agent.version}")
                    st.markdown(f"**Owner:** {agent.owner}")
                with col2:
                    st.markdown(f"**Type:** {agent.agent_type.value}")
                    st.markdown(f"**Status:** {agent.status.value}")
                    st.markdown(f"**Created:** {agent.created_at}")
                
                st.markdown(f"**Description:** {agent.description}")
                
                if agent.endpoint:
                    st.markdown(f"**Endpoint:** `{agent.endpoint}`")
                
                st.markdown("**Capabilities:**")
                for cap in agent.capabilities:
                    with st.expander(cap.name):
                        st.write(cap.description)
                        st.write(f"Category: {cap.category}")

with tab2:
    st.header("Register New Agent")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Agent Name")
            version = st.text_input("Version", value="1.0.0")
            owner = st.text_input("Owner", value="User")
        with col2:
            agent_type = st.selectbox("Agent Type", [t.value for t in AgentType])
            status = st.selectbox("Status", [s.value for s in AgentStatus])
            endpoint = st.text_input("Endpoint URL (Optional)")
            
        description = st.text_area("Description")
        tags_input = st.text_input("Tags (comma separated)")
        
        st.subheader("Capabilities")
        cap_name = st.text_input("Capability Name")
        cap_desc = st.text_input("Capability Description")
        
        submitted = st.form_submit_button("Register Agent")
        
        if submitted:
            if not name or not description:
                st.error("Name and Description are required.")
            else:
                tags = [t.strip() for t in tags_input.split(",") if t.strip()]
                
                capabilities = []
                if cap_name:
                    capabilities.append(CapabilityDefinition(name=cap_name, description=cap_desc))
                
                new_agent = AgentMetadata(
                    name=name,
                    version=version,
                    description=description,
                    owner=owner,
                    status=AgentStatus(status),
                    agent_type=AgentType(agent_type),
                    endpoint=endpoint if endpoint else None,
                    tags=tags,
                    capabilities=capabilities
                )
                
                try:
                    agent_id = registry.register_agent(new_agent)
                    st.success(f"Agent registered successfully! ID: {agent_id}")
                except Exception as e:
                    st.error(f"Error registering agent: {e}")

with tab3:
    st.header("Search Agents")
    query = st.text_input("Search query (name, description, tags)")
    
    if query:
        results = registry.search_agents(query)
        st.write(f"Found {len(results)} agents.")
        for agent in results:
            st.markdown(f"### {agent.name}")
            st.write(agent.description)
            st.caption(f"ID: {agent.id} | Type: {agent.agent_type.value}")
            st.divider()

# Auto-refresh the page every 5 seconds
st.markdown(
    """
    <script>
        setTimeout(function() {
            window.location.reload();
        }, 5000);
    </script>
    """,
    unsafe_allow_html=True
)
