from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import os, json
from dotenv import load_dotenv


load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:9000")


app = FastAPI()


class A2ARequest(BaseModel):
    input: str
    context: dict
    pipeline_trace: list = []
    intent: str = ""


AGENT_CARD = {
    "id": "scraper-tool",
    "name": "Scraper Tool",
    "version": "1.0.0",
    "description": "Scrapes the web using SerpAPI and returns content",
    "tags": ["scraper"],
    "endpoints": {"a2a": "https://f9cf1b13c40d.ngrok-free.app/a2a"},
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

def resolve_agent(tag):
    try:
        res = requests.get(f"{REGISTRY_URL}/resolve?tag={tag}")
        return res.json().get("endpoints", {}).get("a2a")
    except:
        return None


BLOCKED_DOMAINS = ["quora.com", "linkedin.com", "facebook.com"]

def is_readable(text: str) -> bool:
    return len(text.split()) >= 30

def scrape_page(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        content_blocks = soup.find_all(["p", "li", "h2"])
        texts = [tag.get_text(strip=True) for tag in content_blocks if tag.get_text(strip=True)]
        combined = "\n".join(texts)
        if is_readable(combined):
            return f"Source: {url}\n\n{combined[:5000]}"
    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
    return None

def scrape_web(query: str) -> str:
    if not SERP_API_KEY:
        return "⚠️ SERP_API_KEY not set."
    try:
        search = GoogleSearch({"q": query, "api_key": SERP_API_KEY, "num": 10})
        results = search.get_dict()
        links = [r.get("link", "") for r in results.get("organic_results", [])]
        for url in links:
            if any(domain in url for domain in BLOCKED_DOMAINS):
                continue
            result = scrape_page(url)
            if result:
                return result
        return "❌ No usable educational content found."
    except Exception as e:
        return f"❌ Search/scraping failed: {e}"


@app.post("/a2a")
def a2a_scraper(req: A2ARequest):
    question = req.input
    trace = req.pipeline_trace or []

    print(f"🔍 Scraping for: {question}")
    scraped = scrape_web(question)

    status = "ok" if scraped and "Source:" in scraped else "error"
    trace.append({
        "tool": "scraper",
        "status": status,
        "phase": "scraped",
        "content": scraped
    })

    if status == "error":
        return {
            "status": "error",
            "phase": "scraped",
            "answer": scraped,
            "pipeline_trace": trace,
            "note": "No valid content found."
        }

    # Forward to critic
    critic_url = resolve_agent("critic")
    if not critic_url:
        print("⚠️ No critic found, returning scraped content as-is")
        return {
            "status": "ok",
            "phase": "scraped",
            "answer": scraped,
            "context": {"answer": scraped, "phase": "scraped"},
            "pipeline_trace": trace,
            "note": "No critic found"
        }

    try:
        print(f"➡️ Forwarding to Critic: {critic_url}")
        res = requests.post(
            url=critic_url,
            json={
                "input": question,
                "context": {
                    "answer": scraped,
                    "phase": "initial"
                },
                "pipeline_trace": trace,
                "intent": "evaluate_scraped_content"
            },
            timeout=60
        )
        return res.json()
    except Exception as e:
        print(f"❌ Error calling critic: {e}")
        return {
            "status": "error",
            "phase": "scraped",
            "answer": scraped,
            "context": {"answer": scraped, "phase": "scraped"},
            "pipeline_trace": trace,
            "error": f"Failed to contact critic: {e}"
        }


@app.get("/")
def health_check():
    return {"status": "Scraper tool (A2A-enabled) is running"}
