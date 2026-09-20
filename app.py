import ast
import re
from typing import Any

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from yaml.loader import SafeLoader

from tools import buy_stock, get_stock_price, sell_stock, view_portfolio

load_dotenv()

st.set_page_config(
    page_title="AI Stock Trading Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #0e1117;
    --panel: #161b22;
    --panel-elevated: #1c232d;
    --border: #303943;
    --muted: #8b949e;
    --text: #f0f6fc;
    --green: #2ea043;
    --green-soft: #3fb950;
    --red: #da3633;
}

html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
.stApp { background: var(--bg); color: var(--text); }
[data-testid="stHeader"] { background: rgba(14,17,23,.9); }
[data-testid="stSidebar"] {
    background: #11161d;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] > div:first-child { padding: 2rem 1.25rem; }
.block-container { max-width: 1500px; padding: 2rem 3rem 6rem; }
h1, h2, h3 { letter-spacing: -0.03em; }
h1 { font-weight: 800; font-size: clamp(2rem, 4vw, 3.2rem); }
h2 { font-size: 1.35rem; }
.eyebrow {
    color: var(--green-soft); font: 500 .72rem 'DM Mono', monospace;
    letter-spacing: .12em; text-transform: uppercase; margin-bottom: .45rem;
}
.hero {
    background: linear-gradient(135deg, #18232b 0%, #131a22 65%, #11161d 100%);
    border: 1px solid #34414b; border-radius: 18px; padding: 2rem 2.2rem;
    margin-bottom: 1.5rem; box-shadow: 0 18px 45px rgba(0,0,0,.2);
}
.hero h1 { margin: 0; }
.hero-copy { color: #aab6c3; margin: .6rem 0 1.3rem; }
.status-pill {
    display: inline-flex; align-items: center; gap: .4rem; border: 1px solid #245d38;
    border-radius: 999px; background: rgba(35,134,54,.14); color: #7ee787;
    padding: .35rem .7rem; font-size: .78rem; font-weight: 700;
}
.welcome { color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .1em; }
.welcome-name { color: var(--text); font-size: 1.25rem; font-weight: 800; margin: .25rem 0 1rem; }
.section-label { color: var(--muted); font: 500 .72rem 'DM Mono', monospace; text-transform: uppercase; letter-spacing: .1em; margin: 1rem 0 .6rem; }
.metric-card {
    background: var(--panel); border: 1px solid var(--border); border-radius: 14px;
    padding: .75rem 1rem; box-shadow: 0 8px 25px rgba(0,0,0,.12);
}
[data-testid="stMetric"] { background: transparent; }
[data-testid="stMetricLabel"] { color: var(--muted); }
[data-testid="stMetricValue"] { color: var(--text); font-weight: 800; }
[data-testid="stMetricDelta"] svg { display: none; }
.stButton > button {
    width: 100%; border: 1px solid #3b4b59; border-radius: 9px; background: #1b2630;
    color: var(--text); font-weight: 700; transition: all .2s ease;
}
.stButton > button:hover { border-color: var(--green-soft); color: #7ee787; }
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.chat-row { margin: .5rem 0; }
[data-testid="stChatMessage"] {
    border: 1px solid var(--border); border-radius: 15px; padding: .2rem .9rem;
    background: var(--panel); margin-bottom: .75rem;
}
[data-testid="stChatMessage"][data-testid*="user"] { background: #17232c; border-color: #2a4b5c; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { line-height: 1.65; }
.receipt {
    border-left: 3px solid var(--green); background: rgba(46,160,67,.09);
    border-radius: 0 10px 10px 0; padding: .85rem 1rem; margin-top: .5rem;
}
.tip-card {
    color: #aab6c3; background: #121922; border: 1px dashed #364352;
    border-radius: 12px; padding: 1rem 1.1rem; font-size: .85rem;
}
footer { visibility: hidden; }
@media (max-width: 800px) {
    .block-container { padding: 1rem 1rem 5rem; }
    .hero { padding: 1.4rem; }
}
</style>
""",
    unsafe_allow_html=True,
)


def parse_portfolio(raw_summary: str) -> dict[str, Any]:
    """Extract the stable fields emitted by tools.view_portfolio for presentation."""
    result: dict[str, Any] = {"cash": None, "value": None, "holdings": {}, "raw": raw_summary}
    cash_match = re.search(r"Cash:\s*\$?([\d,]+(?:\.\d+)?)", raw_summary)
    value_match = re.search(r"Portfolio Value:\s*\$?([\d,]+(?:\.\d+)?)", raw_summary)
    holdings_match = re.search(r"Holdings:\s*(\{.*\})\s*$", raw_summary)
    if cash_match:
        result["cash"] = float(cash_match.group(1).replace(",", ""))
    if value_match:
        result["value"] = float(value_match.group(1).replace(",", ""))
    if holdings_match:
        try:
            parsed = ast.literal_eval(holdings_match.group(1))
            if isinstance(parsed, dict):
                result["holdings"] = parsed
        except (SyntaxError, ValueError):
            pass
    return result


def money(value: float | None) -> str:
    return "—" if value is None else f"${value:,.2f}"


def render_portfolio(summary: dict[str, Any]) -> None:
    st.markdown('<div class="section-label">Live portfolio dashboard</div>', unsafe_allow_html=True)
    metric_left, metric_right = st.columns(2)
    with metric_left:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("💵 Cash balance", money(summary["cash"]))
        st.markdown("</div>", unsafe_allow_html=True)
    with metric_right:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📊 Portfolio value", money(summary["value"]))
        st.markdown("</div>", unsafe_allow_html=True)

    holdings = summary["holdings"]
    if holdings:
        rows = [
            {
                "Ticker": ticker,
                "Shares": position.get("shares", "—"),
                "Avg price": money(position.get("avg_price")),
                "Market value": money(position.get("market_value")),
            }
            for ticker, position in holdings.items()
            if isinstance(position, dict)
        ]
        st.dataframe(rows, hide_index=True, use_container_width=True)
    else:
        st.caption("No open positions — your buying power is ready.")


def render_agent_output(output_text: str) -> None:
    """Keep trade and portfolio responses visually grouped in the terminal."""
    is_receipt = any(
        keyword in output_text.lower()
        for keyword in ("order id", "successfully placed", "portfolio", "buy order", "sell order")
    )
    if is_receipt:
        st.markdown('<div class="receipt">', unsafe_allow_html=True)
    st.markdown(output_text)
    if is_receipt:
        st.markdown("</div>", unsafe_allow_html=True)


@st.cache_resource
def get_agent_executor() -> AgentExecutor:
    llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
    agent_tools = [get_stock_price, view_portfolio, buy_stock, sell_stock]
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert AI stock trading assistant managing an Alpaca paper trading portfolio. "
                "Always check stock prices and view your portfolio before executing any buy or sell commands. "
                "Be precise, transparent, and report transaction results clearly.",
            ),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, agent_tools, prompt)
    return AgentExecutor(agent=agent, tools=agent_tools, verbose=False)


with open("config.yaml") as config_file:
    config = yaml.load(config_file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)
authenticator.login(location="main")
authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name") or "Trader"

if authentication_status is False:
    st.error("Username/password is incorrect.")
    st.stop()
if authentication_status is None:
    st.markdown(
        '<div class="hero"><div class="eyebrow">Secure paper trading terminal</div>'
        "<h1>Welcome to your trading desk</h1>"
        '<p class="hero-copy">Sign in to access your AI-powered Alpaca sandbox portfolio.</p></div>',
        unsafe_allow_html=True,
    )
    st.stop()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "portfolio_summary" not in st.session_state:
    st.session_state.portfolio_summary = None

with st.sidebar:
    st.markdown('<div class="welcome">Account command center</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="welcome-name">Welcome back, {name}</div>', unsafe_allow_html=True)
    authenticator.logout("Log out", location="sidebar")
    st.divider()

    if st.button("🔄 Refresh portfolio", use_container_width=True):
        st.session_state.portfolio_summary = None
        st.rerun()

    if st.session_state.portfolio_summary is None:
        with st.spinner("Syncing Alpaca account..."):
            try:
                raw_portfolio = view_portfolio.invoke({})
                st.session_state.portfolio_summary = parse_portfolio(raw_portfolio)
            except Exception as exc:
                st.error(f"Portfolio sync failed: {exc}")
                st.session_state.portfolio_summary = {"cash": None, "value": None, "holdings": {}, "raw": ""}
    render_portfolio(st.session_state.portfolio_summary)
    st.divider()
    st.markdown(
        '<div class="tip-card">🛡️ <strong>Sandbox mode</strong><br>'
        "Orders are simulated through Alpaca paper trading. No real funds are at risk.</div>",
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="hero"><div class="eyebrow">AI-powered execution terminal</div>'
    "<h1>📈 Stock Trading Assistant</h1>"
    '<p class="hero-copy">Research markets, review your positions, and execute paper trades with a transparent AI copilot.</p>'
    '<span class="status-pill">🟢 Connected to Alpaca Sandbox</span></div>',
    unsafe_allow_html=True,
)

agent_executor = get_agent_executor()
for human_message, ai_message in st.session_state.chat_history:
    with st.chat_message("human", avatar="🧑‍💼"):
        st.markdown(human_message)
    with st.chat_message("ai", avatar="🤖"):
        render_agent_output(ai_message)

if user_input := st.chat_input("Ask your agent (e.g., “Check AAPL price and buy 1 share”)..."):
    with st.chat_message("human", avatar="🧑‍💼"):
        st.markdown(user_input)
    with st.chat_message("ai", avatar="🤖"):
        with st.spinner("Reviewing your portfolio and executing securely..."):
            try:
                formatted_history = [
                    item
                    for human_message, ai_message in st.session_state.chat_history
                    for item in (("human", human_message), ("ai", ai_message))
                ]
                response = agent_executor.invoke(
                    {"input": user_input, "chat_history": formatted_history}
                )
                output_text = response["output"]
                render_agent_output(output_text)
                st.session_state.chat_history.append((user_input, output_text))
                st.session_state.portfolio_summary = None
            except Exception as exc:
                st.error(f"Agent error: {exc}")
                st.stop()
    st.rerun()
