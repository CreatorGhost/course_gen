import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from langchain.tools import Tool
from tavily import TavilyClient

# Load environment variables
load_dotenv()

# Initialize Tavily client if API key is available
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

class WebResearcher:
    """Class for conducting web research."""
    
    def __init__(self):
        if TAVILY_API_KEY:
            self.tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        else:
            self.tavily_client = None
            print("Warning: TAVILY_API_KEY not found. Web research functionality will be limited.")
    
    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web for information related to the query.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of dictionaries containing search results
        """
        if self.tavily_client:
            try:
                # Use Tavily for web search
                search_results = self.tavily_client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=max_results
                )
                return search_results.get("results", [])
            except Exception as e:
                print(f"Error during Tavily search: {str(e)}")
                return self._fallback_search(query, max_results)
        else:
            return self._fallback_search(query, max_results)
    
    def _fallback_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Fallback method for web search when Tavily is not available.
        Uses a simple HTTP request to search engines.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of dictionaries containing search results
        """
        # This is a simplified fallback implementation
        # In a production system, you would implement a more robust fallback
        return [
            {
                "title": "Fallback Result",
                "url": "https://example.com",
                "content": "This is a fallback result as the primary search service is unavailable."
            }
        ]
    
    def extract_content(self, url: str) -> str:
        """
        Extract content from a webpage.
        
        Args:
            url: URL of the webpage
            
        Returns:
            Extracted text content
        """
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                
                # Get text
                text = soup.get_text(separator="\n")
                
                # Break into lines and remove leading and trailing space on each
                lines = (line.strip() for line in text.splitlines())
                # Break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                # Drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return text[:10000]  # Limit text length
            else:
                return f"Failed to retrieve content. Status code: {response.status_code}"
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    
    def research_topic(self, topic: str) -> Dict[str, Any]:
        """
        Conduct research on a specific topic.
        
        Args:
            topic: The topic to research
            
        Returns:
            Dictionary containing research results
        """
        results = self.search_web(topic)
        research_data = {
            "topic": topic,
            "sources": [],
            "summary": "",
        }
        
        for result in results:
            source = {
                "title": result.get("title", "Unknown Title"),
                "url": result.get("url", ""),
                "snippet": result.get("content", "")
            }
            
            # If we have access to the full content, extract it
            if source["url"]:
                try:
                    full_content = self.extract_content(source["url"])
                    if len(full_content) > 500:  # Only use if we got meaningful content
                        source["full_content"] = full_content
                except Exception as e:
                    source["extraction_error"] = str(e)
            
            research_data["sources"].append(source)
        
        return research_data

# Create a tool for LangChain integration
def get_web_research_tool():
    """
    Create a LangChain tool for web research.
    
    Returns:
        A LangChain Tool instance
    """
    researcher = WebResearcher()
    
    web_research_tool = Tool(
        name="web_research",
        description="Search the web for information on a specific topic.",
        func=researcher.research_topic
    )
    
    return web_research_tool 