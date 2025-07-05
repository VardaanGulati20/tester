from fastapi import FastAPI
from pydantic import BaseModel
from server.tools.dynamic_scraper_tool import scrape_web
import requests
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


llm = ChatGroq(
    temperature=0,
    model_name="llama3-70b-8192",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

class QuestionInput(BaseModel):
    input: str

CRITIC_URL = "http://localhost:8002/evaluate"

@app.post("/invoke")
def invoke_tool(input: QuestionInput):
    question = input.input

    # === PHASE 1: SCRAPING ===
    scraped_content = scrape_web(question)
    initial_answer = scraped_content

    # === PHASE 2: INITIAL CRITIC EVALUATION ===
    critic_payload_1 = {"question": question, "answer": initial_answer}
    try:
        r1 = requests.post(CRITIC_URL, json=critic_payload_1).json()
        score_1 = r1.get("score", 0)
        critic_feedback_1 = r1.get("feedback", "")
    except Exception as e:
        score_1 = 0
        critic_feedback_1 = f"Critic 1 failed: {e}"

    # === PHASE 3: LLM IMPROVEMENT (only if score < 7) ===
    if score_1 < 9:
        improvement_prompt = PromptTemplate.from_template(
            "The following content was scraped from the web for the question:\n{question}\n\nScraped Answer:\n{answer}\n\nCritic Feedback:\n{feedback}\n\nUsing this feedback, write a clearer, more complete, and accurate educational answer:"
        )
        chain = LLMChain(llm=llm, prompt=improvement_prompt)
        final_answer = chain.run({
            "question": question,
            "answer": initial_answer,
            "feedback": critic_feedback_1
        })
    else:
        final_answer = initial_answer

    # === PHASE 4: FINAL CRITIC EVALUATION ===
    critic_payload_2 = {"question": question, "answer": final_answer}
    try:
        r2 = requests.post(CRITIC_URL, json=critic_payload_2).json()
        score_2 = r2.get("score", 0)
        critic_feedback_2 = r2.get("feedback", "")
    except Exception as e:
        score_2 = 0
        critic_feedback_2 = f"Critic 2 failed: {e}"

    return {
        "question": question,
        "initial_answer": initial_answer,
        "critic_feedback_1": critic_feedback_1,
        "score_1": score_1,
        "final_answer": final_answer,
        "critic_feedback_2": critic_feedback_2,
        "score_2": score_2
    }



