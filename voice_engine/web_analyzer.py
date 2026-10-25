import os
import re
import json
import urllib.parse
import logging
from typing import Dict, Any, List, Optional
import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

logger = logging.getLogger("WebAnalyzer")


class WebAnalyzer:
    """
    Intelligent Web Search & Content Analysis Engine.
    Executes web queries, parses web pages, extracts core content,
    and produces structured summaries and key takeaways with citations.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search DuckDuckGo HTML / Instant Answers."""
        results = []
        try:
            # 1. Try DuckDuckGo Instant Answer API
            api_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            resp = requests.get(api_url, headers=self.headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("AbstractText"):
                    results.append({
                        "title": data.get("Heading", query),
                        "snippet": data.get("AbstractText"),
                        "url": data.get("AbstractURL", "https://duckduckgo.com")
                    })
                # Check related topics
                for topic in data.get("RelatedTopics", [])[:3]:
                    if isinstance(topic, dict) and "Text" in topic and "FirstURL" in topic:
                        results.append({
                            "title": topic["Text"].split(" - ")[0] if " - " in topic["Text"] else topic["Text"][:40],
                            "snippet": topic["Text"],
                            "url": topic["FirstURL"]
                        })

            # 2. Try DuckDuckGo HTML search for broader organic results
            if len(results) < max_results:
                html_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                html_resp = requests.post(
                    "https://html.duckduckgo.com/html/",
                    data={"q": query},
                    headers=self.headers,
                    timeout=6
                )
                if html_resp.status_code == 200 and BeautifulSoup:
                    soup = BeautifulSoup(html_resp.text, "html.parser")
                    links = soup.find_all("a", class_="result__snippet")
                    titles = soup.find_all("a", class_="result__url")
                    
                    for row in soup.find_all("div", class_="result__body"):
                        title_elem = row.find("a", class_="result__a")
                        snippet_elem = row.find("a", class_="result__snippet")
                        url_elem = row.find("a", class_="result__url")

                        if title_elem and snippet_elem:
                            title = title_elem.get_text(strip=True)
                            snippet = snippet_elem.get_text(strip=True)
                            raw_href = title_elem.get("href", "")

                            # Extract clean destination URL
                            if "uddg=" in raw_href:
                                m = re.search(r"uddg=([^&]+)", raw_href)
                                clean_url = urllib.parse.unquote(m.group(1)) if m else raw_href
                            else:
                                clean_url = raw_href

                            results.append({
                                "title": title,
                                "snippet": snippet,
                                "url": clean_url
                            })
                            if len(results) >= max_results:
                                break
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")

        # 3. Fallback to Wikipedia API if general query
        if not results:
            results = self._search_wikipedia(query)

        return results[:max_results]

    def _search_wikipedia(self, query: str) -> List[Dict[str, str]]:
        """Search Wikipedia for encyclopedic queries."""
        results = []
        try:
            wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(query)}&limit=3&namespace=0&format=json"
            resp = requests.get(wiki_url, headers=self.headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) >= 4 and len(data[1]) > 0:
                    for i in range(len(data[1])):
                        results.append({
                            "title": data[1][i],
                            "snippet": data[2][i] if data[2][i] else f"Wikipedia article on {data[1][i]}",
                            "url": data[3][i]
                        })
        except Exception as e:
            logger.warning(f"Wikipedia search error: {e}")
        return results

    def extract_page_text(self, url: str, max_chars: int = 2500) -> str:
        """Fetch and extract readable clean text from a web page."""
        if not BeautifulSoup:
            return ""
        try:
            resp = requests.get(url, headers=self.headers, timeout=6)
            if resp.status_code != 200:
                return ""
            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove scripts, styles, navigations
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
                tag.decompose()

            # Extract text from paragraphs
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
            full_text = " ".join(paragraphs)
            return full_text[:max_chars]
        except Exception as e:
            logger.debug(f"Failed to fetch content from {url}: {e}")
            return ""

    def summarize_content(self, query: str, search_results: List[Dict[str, str]], page_contents: List[str]) -> Dict[str, Any]:
        """
        Synthesize search results and page content into an executive summary
        and bullet-point takeaways.
        """
        # If Gemini API key is available, use Gemini for high-level synthesis
        if self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                context = f"Query: {query}\n\nSearch Snippets:\n"
                for res in search_results:
                    context += f"- {res['title']}: {res['snippet']}\n"
                for content in page_contents:
                    if content:
                        context += f"\nPage Content: {content[:1000]}\n"

                prompt = (
                    "You are Ether, an intelligent voice AI assistant. Based on the following research context, "
                    "provide:\n"
                    "1. A concise, spoken-friendly summary (1-2 sentences, max 35 words) suitable for TTS playback.\n"
                    "2. 3-4 key factual bullet points.\n"
                    "Format as valid JSON with keys 'spoken_summary' (string) and 'key_takeaways' (list of strings)."
                )

                response = model.generate_content([prompt, context])
                raw = response.text.strip()
                # Parse JSON
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()
                data = json.loads(raw)
                return {
                    "spoken_summary": data.get("spoken_summary", ""),
                    "key_takeaways": data.get("key_takeaways", []),
                    "method": "gemini-ai"
                }
            except Exception as e:
                logger.info(f"Gemini synthesis unavailable ({e}), using built-in NLP summarizer")

        # Built-in Extractive NLP Summarizer
        sentences = []
        for r in search_results:
            if r.get("snippet"):
                # Clean snippet
                clean_s = re.sub(r"\s+", " ", r["snippet"]).strip()
                for sent in re.split(r"(?<=[.!?])\s+", clean_s):
                    if len(sent) > 25 and sent not in sentences:
                        sentences.append(sent)

        for content in page_contents:
            if content:
                for sent in re.split(r"(?<=[.!?])\s+", content):
                    if len(sent) > 35 and sent not in sentences:
                        sentences.append(sent)
                        if len(sentences) > 15:
                            break

        if not sentences:
            return {
                "spoken_summary": f"I searched the web for {query}, but could not find detailed information.",
                "key_takeaways": ["No authoritative web sources returned results for this query."],
                "method": "fallback"
            }

        # Select top sentence for spoken summary
        spoken_summary = sentences[0]
        if len(spoken_summary) > 200:
            spoken_summary = spoken_summary[:197] + "..."

        # Select up to 4 key takeaways
        takeaways = sentences[1:5] if len(sentences) > 1 else [spoken_summary]

        return {
            "spoken_summary": spoken_summary,
            "key_takeaways": takeaways,
            "method": "nlp-extractive"
        }

    def analyze_web(self, query: str) -> Dict[str, Any]:
        """
        Complete end-to-end web analysis pipeline:
        Search -> Scrape -> Synthesize -> Return structured card data.
        """
        logger.info(f"Analyzing web for query: '{query}'")
        search_results = self.search_duckduckgo(query, max_results=4)

        page_texts = []
        for res in search_results[:2]:
            url = res.get("url", "")
            if url and not url.endswith((".pdf", ".zip", ".exe")):
                text = self.extract_page_text(url, max_chars=1200)
                if text:
                    page_texts.append(text)

        summary_data = self.summarize_content(query, search_results, page_texts)

        return {
            "query": query,
            "spoken_summary": summary_data["spoken_summary"],
            "key_takeaways": summary_data["key_takeaways"],
            "sources": search_results,
            "synthesis_method": summary_data["method"]
        }
