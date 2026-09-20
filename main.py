import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Import the custom tools we built
from tools import get_stock_price, view_portfolio, buy_stock, sell_stock
from database import init_db

# Load environment variables from .env
load_dotenv()

# 1. Initialize the Database Ledger
init_db()

# 2. Initialize the Groq LLM Brain
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

# 3. Gather our toolset
tools = [get_stock_price, view_portfolio, buy_stock, sell_stock]

# 4. Define the Agent Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert AI stock trading assistant managing a paper trading portfolio. "
               "Always check stock prices and view your portfolio before executing any buy or sell commands. "
               "Be precise, transparent, and report transaction results clearly."),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

# 5. Construct the Tool-Calling Agent and Executor
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 6. Interactive Chat Loop
if __name__ == "__main__":
    print("--- 🚀 AI Stock Paper Trading Agent Initialized ---")
    print("Type your commands below (e.g., 'Check my portfolio', 'Buy 2 shares of AAPL', or 'exit' to quit).\n")
    
    # Maintain chat history across turns if desired
    chat_history = []
    
    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.strip().lower() in ["exit", "quit"]:
                print("Exiting trading agent. Goodbye!")
                break
                
            if not user_input.strip():
                continue
                
            # Invoke agent with input and chat history
            response = agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history
            })
            
            print(f"\nAgent:\n{response['output']}")
            
            # Update chat history memory
            chat_history.append(("human", user_input))
            chat_history.append(("ai", response["output"]))
            
        except KeyboardInterrupt:
            print("\nExiting trading agent. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")