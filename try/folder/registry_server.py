from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import time

app = FastAPI()
registered_agents: Dict[str, Dict] = {}

class AgentCard(BaseModel):
    id: str
    name: str
    version: str
    description: str
    tags: List[str]
    endpoints: Dict[str, str]
    auth: Dict

@app.post("/register")
def register(agent: AgentCard):
    for tag in agent.tags:
        registered_agents[tag] = {
            "card": agent.dict(),
            "last_seen": time.time()
        }
    return {"status": "registered", "tags": agent.tags}

@app.get("/resolve")
def resolve(tag: str):
    if tag in registered_agents:
        return registered_agents[tag]["card"]
    raise HTTPException(status_code=404, detail=f"Agent with tag '{tag}' not found")

@app.get("/list")
def list_agents():
    return [info["card"] for info in registered_agents.values()]

@app.get("/")
def health():
    return {"status": "Registry is running"}
