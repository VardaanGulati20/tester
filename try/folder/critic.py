from fastapi import FastAPI
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
import os, json, requests, re
from dotenv import load_dotenv


load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:9000")

app = FastAPI()


llm = ChatGroq(
    model_name="llama3-70b-8192",
    temperature=0.2,
    groq_api_key=GROQ_API_KEY
)

critic_prompt = PromptTemplate.from_template(
    """You are an educational critic reviewing an AI assistant's web-scraped answer to a student's question.

Question:
{question}

Assistant's Answer:
{answer}

Critique the answer constructively. Then provide a numeric score from 1 (poor) to 10 (excellent). Output your response in **strict JSON** format like this:

{{
  "score": <1-10>,
  "feedback": "<clear constructive feedback>"
}}"""
)

chain = LLMChain(llm=llm, prompt=critic_prompt)

AGENT_CARD = {
    "id": "critic-tool",
    "name": "Critic Tool",
    "version": "1.0.0",
    "description": "Provides feedback and scoring for scraped answers",
    "tags": ["critic"],
    "endpoints": {"a2a": "http://localhost:8002/a2a"},
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

class A2ARequest(BaseModel):
    input: str
    context: dict
    pipeline_trace: list = []
    intent: str = ""

MAX_ITER = 2

@app.post("/a2a")
def a2a_handler(req: A2ARequest):
    question = req.input
    answer = req.context.get("answer", "")
    phase = req.context.get("phase", "initial")
    iterations = req.context.get("iterations", 0)
    trace = req.pipeline_trace or []

    print(f" [CRITIC] Phase: {phase}, Iteration: {iterations}")

    try:
        result = chain.invoke({
            "question": question,
            "answer": answer
        })


        result_text = result if isinstance(result, str) else result.get("text", str(result))
        print(f" Raw Critic Result:\n{result_text}")

        
        match = re.search(r"\{[\s\S]*?\}", result_text)
        json_str = match.group(0) if match else result_text

        try:
            parsed = json.loads(json_str)
        except Exception as json_error:
            print(f"❌ JSON parse error: {json_error}")
            trace.append({
                "tool": "critic",
                "status": "error",
                "feedback": "[Invalid JSON format]",
                "score": 0,
                "phase": phase
            })
            return {"answer": answer, "pipeline_trace": trace, "status": "error"}

        score = parsed.get("score", 0)
        feedback = parsed.get("feedback", "[No feedback returned]")

        trace.append({
            "tool": "critic",
            "status": "ok",
            "phase": phase,
            "score": score,
            "feedback": feedback
        })

        if score >= 9 or iterations >= MAX_ITER:
            return {
                "status": "complete",
                "phase": phase,
                "answer": answer,
                "score": score,
                "feedback": feedback,
                "pipeline_trace": trace
            }

        # Forward to LLM Refiner
        try:
            res = requests.get(f"{REGISTRY_URL}/resolve?tag=llm")
            refiner_url = res.json().get("endpoints", {}).get("a2a")
        except:
            refiner_url = None

        if not refiner_url:
            return {
                "status": "incomplete",
                "note": "No LLM refiner found.",
                "pipeline_trace": trace
            }

        print(f" Forwarding to LLM Refiner: {refiner_url}")
        refine_response = requests.post(
            url=refiner_url,
            json={
                "input": question,
                "context": {
                    "answer": answer,
                    "feedback": feedback,
                    "iterations": iterations + 1,
                    "phase": "refined"
                },
                "pipeline_trace": trace,
                "intent": "refine_low_score_response"
            },
            timeout=60
        ).json()

        improved_answer = refine_response.get("answer", "[Refiner failed]")
        return a2a_handler(A2ARequest(
            input=question,
            context={
                "answer": improved_answer,
                "phase": "refined",
                "iterations": iterations + 1
            },
            pipeline_trace=refine_response.get("pipeline_trace", trace)
        ))

    except Exception as e:
        print(f" Exception during critique: {e}")
        trace.append({
            "tool": "critic",
            "status": "error",
            "feedback": f"[Error: {e}]",
            "score": 0,
            "phase": phase
        })
        return {"answer": answer, "pipeline_trace": trace, "status": "error"}


@app.get("/")
def health_check():
    return {"status": "Critic tool (A2A-enabled) is running"}
