import streamlit as st
import os
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tools import get_stock_price, view_portfolio, buy_stock, sell_stock

load_dotenv()

# --- 1. PAGE CONFIG MUST BE FIRST ---
st.set_page_config(
    page_title="AI Stock Trading Assistant",
    page_icon="📈",
    layout="wide"
)

# --- 2. LOAD CONFIGURATION FOR AUTH ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- 3. RENDER LOGIN SCREEN ---
authenticator.login(location='main')

# Fetch authentication status from session state safely
authentication_status = st.session_state.get('authentication_status')
name = st.session_state.get('name')
username = st.session_state.get('username')

if authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
    st.stop()  # Stops execution here until logged in

# --- 4. PROTECTED APP CONTENT (Only loads if logged in) ---

# Add a logout button and portfolio status to the sidebar
with st.sidebar:
    st.write(f"Welcome back, *{name}*!")
    try:
        authenticator.logout('Logout', location='sidebar')
    except Exception:
        pass  # Gracefully handle any state race conditions on logout
        
    st.divider()
    
    st.header("💼 Alpaca Portfolio Dashboard")
    if st.button("🔄 Refresh Portfolio"):
        st.rerun()
        
    try:
        portfolio_summary = view_portfolio.invoke({})
        st.success("Connected to Alpaca Sandbox")
        st.markdown(f"**Status Info:**\n{portfolio_summary}")
    except Exception as e:
        st.error(f"Could not load portfolio: {str(e)}")

st.title("📈 AI Stock Paper Trading Assistant (Secure)")
st.markdown("Your autonomous agent connected to Alpaca with user authentication enabled.")

# --- Initialize LangChain Agent ---
@st.cache_resource
def get_agent_executor():
    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
    tools = [get_stock_price, view_portfolio, buy_stock, sell_stock]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert AI stock trading assistant managing an Alpaca paper trading portfolio. "
                   "Always check stock prices and view your portfolio before executing any buy or sell commands. "
                   "Be precise, transparent, and report transaction results clearly."),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)

agent_executor = get_agent_executor()

# --- Main Chat Interface ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for human_msg, ai_msg in st.session_state.chat_history:
    with st.chat_message("human"):
        st.markdown(human_msg)
    with st.chat_message("ai"):
        st.markdown(ai_msg)

if user_input := st.chat_input("Ask your agent (e.g., 'Check EG price and buy 1 share'):"):
    with st.chat_message("human"):
        st.markdown(user_input)
        
    with st.chat_message("ai"):
        with st.spinner("Agent is thinking and executing Alpaca trades..."):
            try:
                formatted_history = []
                for h, a in st.session_state.chat_history:
                    formatted_history.append(("human", h))
                    formatted_history.append(("ai", a))
                
                response = agent_executor.invoke({
                    "input": user_input,
                    "chat_history": formatted_history
                })
                output_text = response["output"]
                st.markdown(output_text)
                
                st.session_state.chat_history.append((user_input, output_text))
                st.rerun()
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")