import nest_asyncio
nest_asyncio.apply()

import streamlit as st
import pandas as pd
import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# --- CONFIGURATION ---
st.set_page_config(page_title="AI Finance Analyst", layout="wide")
api_key = st.secrets["GEMINI_API_KEY"]

# Using a specific version string to avoid 404 Not Found errors
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-001", 
    google_api_key=api_key,
    temperature=0
)

async def start_mcp_agent():
    # Use absolute path to ensure the subprocess finds server.py
    server_path = os.path.abspath("server.py")
    
    client = MultiServerMCPClient({
        "finance_analyst": {
            "command": "python",
            "args": [server_path],
            "transport": "stdio"
        }
    })
    
    tools = await client.get_tools()
    return create_react_agent(llm, tools)

# --- APP UI ---
st.title("💰 AI Personal Finance (MCP + LangGraph)")

uploaded_file = st.file_uploader("Upload transaction.xlsx", type=["xlsx", "csv"])

if uploaded_file:
    # 1. Process and cache the file locally for the server
    if 'file_ready' not in st.session_state:
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
        df.to_csv("transaction_data.csv", index=False)
        st.session_state.file_ready = True

    # 2. Initialize the Agent (Async Fix)
    if "agent" not in st.session_state:
        with st.spinner("Initializing AI Agent..."):
            loop = asyncio.get_event_loop()
            st.session_state.agent = loop.run_until_complete(start_mcp_agent())

    # 3. Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ex: What is my total spending for Dec 2025?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Calculating..."):
                # Run the graph
                result = st.session_state.agent.invoke({"messages": [("user", prompt)]})
                answer = result["messages"][-1].content
                st.write(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

else:
    st.info("Please upload your transaction file to start the analysis.")
