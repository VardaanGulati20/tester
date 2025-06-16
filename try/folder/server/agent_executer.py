import asyncio
import os
from langchain.agents import initialize_agent, AgentType
from langchain_groq import ChatGroq
from server.tools import MCPTool
from utils.logger import save_to_pdf, sanitize_text
from dotenv import load_dotenv
import os

load_dotenv()



llm = ChatGroq(
    temperature=0,
    model_name="llama3-8b-8192",
    api_key=os.getenv("GROQ_API_KEY"),
)

async def get_agent_response(reference_site, query):
    try:
        tool = MCPTool(
            name="custom_search",
            description=f"Extract content from {reference_site}",
            serp_api_key=os.getenv("SERP_API_KEY"),
            reference_site=reference_site
        )

        agent = initialize_agent(
            tools=[tool],
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=1
        )

        print("[INFO] Running agent...")
        final_answer = agent.run(query)

        print("[INFO] Running MCPTool for full content...")
        scraped_content = tool._run(query)

        combined_output = (
            f"🧠 Final Agent Answer:\n{final_answer}\n\n"
            f"🔍 Full Scraped Content:\n{scraped_content}"
        )

        sanitized = sanitize_text(combined_output)
        save_to_pdf(sanitized)

        return sanitized

    except Exception as e:
        return f"[❌] Error in agent response: {str(e)}"
