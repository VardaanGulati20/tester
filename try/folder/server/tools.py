

import requests
from langchain.tools import BaseTool
from bs4 import BeautifulSoup

class MCPTool(BaseTool):
    name: str
    description: str
    serp_api_key: str
    reference_site: str

    def _run(self, query: str) -> str:
        try:
            full_query = f"site:{self.reference_site} {query}"
            params = {
                "q": full_query,
                "api_key": self.serp_api_key,
                "engine": "google",
                "num": "3"
            }
            response = requests.get("https://serpapi.com/search", params=params)
            data = response.json()

            if "organic_results" not in data:
                return "[❌] No search results found."

            results = data["organic_results"]
            extracted_text = ""

            for item in results:
                link = item.get("link", "")
                try:
                    page = requests.get(link, timeout=10)
                    soup = BeautifulSoup(page.text, "html.parser")

                    
                    headings = [h.get_text() for h in soup.find_all(["h1", "h2", "h3"])]
                    paragraphs = [p.get_text() for p in soup.find_all("p")]

                    content = "\n".join(headings + paragraphs)

                    if len(content) > 4000:
                        content = content[:4000] + "\n...[truncated]"

                    extracted_text += f"\n🔗 {link}\n{content}\n\n"

                except Exception as e:
                    extracted_text += f"[⚠️] Failed to scrape {link}: {str(e)}\n"

            return extracted_text.strip() if extracted_text else "[❌] No content extracted."

        except Exception as e:
            return f"[❌] Error: {str(e)}"

    def _arun(self, query: str):
        raise NotImplementedError("Async not supported for MCPTool")
