from fastapi import FastAPI, Request
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()

llm = ChatGroq(
    model_name="llama3-8b-8192",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

critic_prompt = PromptTemplate.from_template("""
You are an educational content critic.

Given the user's question:
{input}

And the assistant's answer:
{answer}

Please give a score from 0 to 10 and provide feedback on correctness, completeness, and clarity.
If you do not think that the answer is precise with respect to the question then u can score it low.
If the answer do not match your expectations and there are more bullet points rather than factual answers then score it low.
Respond in this format:
Score: <number>
Feedback: <text>
""")

critic_chain = LLMChain(llm=llm, prompt=critic_prompt)

@app.post("/evaluate")
async def evaluate(request: Request):
    data = await request.json()
    input_text = data.get("input", "")
    answer = data.get("answer", "")

    result = critic_chain.run({"input": input_text, "answer": answer})

    score_line = next((line for line in result.split("\n") if line.lower().startswith("score:")), "Score: 0")
    feedback_line = next((line for line in result.split("\n") if line.lower().startswith("feedback:")), "Feedback: Not provided")

    score_str = score_line.split(":")[1].strip()
    score = float(score_str)

    feedback = feedback_line.split(":", 1)[1].strip()

    return {"score": score, "feedback": feedback}
