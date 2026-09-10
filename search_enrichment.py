"""
search_enrichment.py - Uses Tavily API to find missing LinkedIn profiles (Bonus Feature)
"""
import os
import logging
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SearchEnricher:
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            logger.warning("⚠️ TAVILY_API_KEY not found in .env. Search enrichment disabled.")
            self.client = None
        else:
            self.client = TavilyClient(api_key=api_key)

    def enrich_leadership(self, intelligence_obj, domain: str):
        """
        Checks key_leadership for missing LinkedIn URLs and searches the web to find them.
        """
        if not self.client:
            return intelligence_obj

        # Simple heuristic to get company name from domain (e.g., postman.com -> Postman)
        company_name = domain.split('.')[0].capitalize()
        
        for person in intelligence_obj.key_leadership:
            # If we have a name but no LinkedIn URL, trigger a search
            if not person.linkedin_url and person.name:
                query = f'"{person.name}" "{company_name}" LinkedIn'
                logger.info(f"   Searching for {person.name}'s LinkedIn...")
                
                try:
                    # Ask Tavily to search
                    response = self.client.search(query, search_depth="basic", max_results=3)
                    
                    # Look for a linkedin.com/in/ link in the results
                    for result in response.get("results", []):
                        url = result.get("url", "")
                        if "linkedin.com/in/" in url:
                            person.linkedin_url = url  # Update the Pydantic object!
                            logger.info(f"      ✅ Found: {url}")
                            break
                            
                    if not person.linkedin_url:
                        logger.info(f"      ⚠️ Could not find LinkedIn for {person.name}")
                        
                except Exception as e:
                    logger.warning(f"      ❌ Search API error: {str(e)}")
                    
        return intelligence_obj