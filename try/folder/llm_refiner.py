from fastapi import FastAPI
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
import os, json, requests
from dotenv import load_dotenv

# ----------------------------
# 🔑 Load Keys
# ----------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:9000")

# ----------------------------
# ⚙️ FastAPI Setup
# ----------------------------
app = FastAPI()

# ----------------------------
# 🤖 LLM Setup
# ----------------------------
llm = ChatGroq(
    model_name="llama3-70b-8192",
    temperature=0.5,
    groq_api_key=GROQ_API_KEY
)

refiner_prompt = PromptTemplate.from_template(
    """You are a helpful AI tutor tasked with improving an assistant's answer based on critique feedback.

Question:
{question}

Original Answer:
{answer}

Critic Feedback:
{feedback}

Update the answer to address **every issue** raised by the critic. Be specific, concise, and clear. Add test cases, examples, and ensure technical accuracy. Avoid vague tips or filler content.

Return only the improved answer below:
"""
)

refine_chain = LLMChain(llm=llm, prompt=refiner_prompt)

# ----------------------------
# 🔁 Self-register with Registry
# ----------------------------
AGENT_CARD = {
    "id": "llm-refiner",
    "name": "LLM Refiner",
    "version": "1.0.0",
    "description": "Improves answers based on critic feedback",
    "tags": ["llm"],
    "endpoints": {"a2a": "http://localhost:8003/a2a"},
    "auth": {"type": "none"}
}

try:
    res = requests.post(f"{REGISTRY_URL}/register", json=AGENT_CARD)
    print("✅ Registered with registry:", res.json())
except Exception as e:
    print("❌ Failed to register with registry:", e)

@app.get("/.well-known/agent.json")
def agent_card():
    return AGENT_CARD

# ----------------------------
# 📡 A2A Model Definition
# ----------------------------
class A2ARequest(BaseModel):
    input: str
    context: dict
    pipeline_trace: list = []
    intent: str = ""

# ----------------------------
# 🚀 A2A Endpoint
# ----------------------------
@app.post("/a2a")
def a2a_handler(req: A2ARequest):
    question = req.input
    original_answer = req.context.get("answer", "")
    feedback = req.context.get("feedback", "")
    trace = req.pipeline_trace or []

    print("🌟 [LLM Refiner] Improving answer...")

    try:
        improved_answer = refine_chain.run({
            "question": question,
            "answer": original_answer,
            "feedback": feedback
        }).strip()

        trace.append({
            "tool": "llm",
            "status": "ok",
            "phase": "refined"
        })

        return {
            "answer": improved_answer,
            "pipeline_trace": trace,
            "status": "complete"
        }

    except Exception as e:
        print(f"❌ [LLM Refiner Error] {e}")
        trace.append({
            "tool": "llm",
            "status": "error",
            "phase": "refined",
            "error": str(e)
        })
        return {
            "answer": "[Refiner failed]",
            "pipeline_trace": trace,
            "status": "error"
        }

# ----------------------------
# ✅ Health Check
# ----------------------------
@app.get("/")
def health_check():
    return {"status": "LLM Refiner tool is running"}
