import requests
from bs4 import BeautifulSoup
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
import re
import unicodedata

class DynamicScraperTool(BaseTool):
    name: str
    description: str
    serp_api_key: str
    llm: any  # Pass LangChain LLM from outside

    def _clean_text(self, text: str) -> str:
        text = unicodedata.normalize("NFKD", text)
        return ''.join([c for c in text if ord(c) < 256])

    def _scrape_urls(self, query: str) -> list:
        try:
            search_query = f"{query} site:geeksforgeeks.org OR site:softwaretestinghelp.com"
            params = {
                "q": search_query,
                "api_key": self.serp_api_key,
                "engine": "google",
                "num": "5"
            }
            res = requests.get("https://serpapi.com/search", params=params)
            data = res.json()
            if "organic_results" not in data:
                return []
            return [r.get("link") for r in data["organic_results"] if r.get("link")]
        except:
            return []

    def _extract_html_content(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        headings = [tag.get_text() for tag in soup.find_all(['h1', 'h2', 'h3'])]
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        return "\n".join(headings + paragraphs)

    def _run(self, query: str) -> str:
        urls = self._scrape_urls(query)
        if not urls:
            return "[❌] No relevant content found on known educational sites."

        accumulated_text = ""
        for link in urls:
            try:
                response = requests.get(link, timeout=10)
                html = response.text
                content = self._extract_html_content(html)
                cleaned = self._clean_text(content)

                # Summarize this page's content using the LLM
                summarizer = LLMChain(
                    llm=self.llm,
                    prompt=PromptTemplate(
                        input_variables=["input", "source"],
                        template="""
Based on the web content below, extract or generate relevant educational material for the user query.

User Query:
{input}

Web Content:
{source}

If there's not enough information, say so clearly.
"""
                    )
                )

                summary = summarizer.run({"input": query, "source": cleaned[:4000]})
                accumulated_text += f"Link: {link}\n\n{summary}\n\n{'-'*80}\n"

            except Exception as e:
                accumulated_text += f"[⚠️] Failed to process {link}: {str(e)}\n"

        return accumulated_text.strip() if accumulated_text else "[❌] No useful content found."

    def _arun(self, query: str):
        raise NotImplementedError("Async not supported.")
