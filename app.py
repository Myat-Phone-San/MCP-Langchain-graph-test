import streamlit as st
import pandas as pd
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# --- INITIALIZE ---
st.set_page_config(page_title="MCP Finance Tracker")
api_key = st.secrets["GEMINI_API_KEY"]
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

async def initialize_agent():
    # Connect to our local MCP server
    # Note: In a real environment, provide the absolute path to server.py
    client = MultiServerMCPClient({
        "finance_server": {
            "command": "python",
            "args": ["server.py"],
            "transport": "stdio"
        }
    })
    
    tools = await client.get_tools()
    return create_react_agent(llm, tools)

# --- UI LOGIC ---
st.title("🔌 MCP-Powered Finance Analyst")

uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])

if uploaded_file:
    # Save file locally for the MCP Server to read
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.to_csv("transaction_data.csv", index=False)
    
    if "agent" not in st.session_state:
        with st.spinner("Connecting to MCP Server..."):
            st.session_state.agent = asyncio.run(initialize_agent())

    # Chat UI
    if prompt := st.chat_input("Analyze my spending..."):
        st.chat_message("user").write(prompt)
        
        with st.chat_message("assistant"):
            # Run the LangGraph agent
            config = {"configurable": {"thread_id": "finance_thread"}}
            response = st.session_state.agent.invoke(
                {"messages": [("user", prompt)]}, 
                config
            )
            # The last message in the response is the AI's answer
            st.write(response["messages"][-1].content)

else:
    st.info("Please upload your data to start the MCP Server.")