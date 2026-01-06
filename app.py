import nest_asyncio
nest_asyncio.apply()

import streamlit as st
import pandas as pd
import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# --- CONFIG ---
st.set_page_config(page_title="MCP Analyst", layout="wide")
api_key = st.secrets["GEMINI_API_KEY"]

# Specific version to avoid 404
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-001", google_api_key=api_key)

async def initialize_agent():
    # Use absolute path! Streamlit Cloud needs this.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "server.py")
    
    if not os.path.exists(server_path):
        raise FileNotFoundError(f"Could not find server.py at {server_path}")

    client = MultiServerMCPClient({
        "finance_server": {
            "command": "python",
            "args": [server_path],
            "transport": "stdio"
        }
    })
    
    tools = await client.get_tools()
    return create_react_agent(llm, tools)

# --- UI ---
st.title("💰 Finance Tracker")
uploaded_file = st.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"])

if uploaded_file:
    # Save file for MCP Server
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.to_csv("transaction_data.csv", index=False)
    
    if "agent" not in st.session_state:
        with st.spinner("Connecting to MCP..."):
            try:
                # REPLACEMENT FOR asyncio.run()
                loop = asyncio.get_event_loop()
                st.session_state.agent = loop.run_until_complete(initialize_agent())
                st.success("Agent Ready!")
            except Exception as e:
                st.error(f"Failed to start MCP: {e}")

    # Chat logic
    if prompt := st.chat_input("Ask about your data"):
        st.chat_message("user").write(prompt)
        # Agent execution logic...
        res = st.session_state.agent.invoke({"messages": [("user", prompt)]})
        st.chat_message("assistant").write(res["messages"][-1].content)
