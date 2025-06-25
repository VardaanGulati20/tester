
from fastapi import FastAPI
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain_groq import ChatGroq
from logger import sanitize_text, save_to_pdf
from server.tools.dynamic_scraper_tool import DynamicScraperTool
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.get("/")
def root():
    return {"message": "✅ MCP Educational Server running. POST to /invoke."}

# LLM setup
llm = ChatGroq(
    temperature=0,
    model_name="llama3-8b-8192",
    api_key=os.getenv("GROQ_API_KEY")
)

fallback_prompt = PromptTemplate(
    input_variables=["input"],
    template="""
You are a helpful educational assistant. Based on the user query below, generate a clear, structured, and useful output.

User Query:
{input}

Provide directly relevant, actionable information.
"""
)

class RequestModel(BaseModel):
    input: str
    context: dict = {}

@app.post("/invoke")
async def invoke(request: RequestModel):
    query = request.input
    context = request.context or {}

    try:
        tool = DynamicScraperTool(
            name="dynamic_scraper",
            description="Dynamically scrapes content using SerpAPI and summarizes",
            serp_api_key=os.getenv("SERP_API_KEY"),
            llm=llm
        )

        scraped_result = tool._run(query)
        scraped_result = sanitize_text(scraped_result)

        if "No useful content" in scraped_result or scraped_result.strip() == "":
            print("[⚠️] No educational content found. Falling back to direct LLM generation...")
            chain = LLMChain(prompt=fallback_prompt, llm=llm)
            final_answer = chain.run({"input": query})
        else:
            final_answer = "Content successfully extracted and summarized from trusted websites."

        final_answer = sanitize_text(final_answer)
        query = sanitize_text(query)

        full_output = (
            f"Final Agent Answer:\n{final_answer}\n\n"
            f"Full Scraped Content:\n{scraped_result}"
        )

        save_to_pdf(full_output, question=query)

        return {"output": full_output}

    except Exception as e:
        return {"output": f"[❌] Error: {str(e)}"}


