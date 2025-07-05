import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import os
from dotenv import load_dotenv
load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")

# Block domains that typically prevent scraping
BLOCKED_DOMAINS = ["quora.com", "medium.com", "linkedin.com", "facebook.com"]

def is_readable(text: str) -> bool:
    return len(text.split()) >= 30  

def scrape_page(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        
        blocks = soup.find_all(["p", "li", "h2"])
        texts = [tag.get_text(strip=True) for tag in blocks if tag.get_text(strip=True)]
        combined = "\n".join(texts)

        if is_readable(combined):
            return f"Source: {url}\n\n{combined[:5000]}"
    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
    return None

def scrape_web(question: str) -> str:
    if not SERP_API_KEY:
        return "⚠️ SERPAPI_API_KEY not set in environment."

    try:
        
        search = GoogleSearch({
            "q": question,
            "api_key": SERP_API_KEY,
            "num": 10
        })

        results = search.get_dict()
        links = [r.get("link", "") for r in results.get("organic_results", [])]

        if not links:
            return "❌ No search results found."

        
        for url in links:
            if any(domain in url for domain in BLOCKED_DOMAINS):
                print(f"⛔ Skipping blocked domain: {url}")
                continue

            print(f"🔍 Trying: {url}")
            result = scrape_page(url)
            if result:
                print(f"✅ Successfully scraped: {url}")
                return result

        return "❌ No usable educational content found from the top sources."
    
    except Exception as e:
        return f"❌ Search or scraping failed: {e}"
