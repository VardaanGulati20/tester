from fastapi import FastAPI, Request
from pydantic import BaseModel
from .agent_executer import get_agent_response

app = FastAPI()

class QueryRequest(BaseModel):
    reference_site: str
    query: str

@app.post("/ask")
async def ask(req: QueryRequest):
    response_text = await get_agent_response(req.reference_site, req.query)
    return {"response": response_text}
