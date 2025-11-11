thonimport logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

from .utils_search import search_bing, is_probable_linkedin_company_url

@dataclass
class LinkedInFinderConfig:
    search_engine: str = "bing"
    timeout: int = 10
    user_agent: str = "LinkedInCompanyFinderBot/1.0"

class LinkedInFinder:
    """
    Responsible for transforming a company name into a LinkedIn company URL
    using a web search engine.
    """

    def __init__(self, search_engine: str = "bing", timeout: int = 10, user_agent: str = ""):
        self.config = LinkedInFinderConfig(
            search_engine=search_engine,
            timeout=timeout,
            user_agent=user_agent or LinkedInFinderConfig.user_agent,
        )
        if self.config.search_engine.lower() != "bing":
            logging.warning(
                "Unsupported search engine '%s'; falling back to 'bing'.",
                self.config.search_engine,
            )
            self.config.search_engine = "bing"

    def _build_search_query(self, company_name: str) -> str:
        """
        Build a search query string for a given company.
        """
        return f"linkedin company {company_name}"

    def _search(self, query: str):
        """
        Call the configured search engine.
        """
        if self.config.search_engine.lower() == "bing":
            return search_bing(
                query=query,
                timeout=self.config.timeout,
                user_agent=self.config.user_agent,
            )
        raise RuntimeError(f"Unsupported search engine: {self.config.search_engine}")

    def _select_linkedin_url(self, results) -> Optional[str]:
        """
        Given a list of search results, select the most likely LinkedIn company URL.
        """
        for result in results:
            url = result.get("url")
            if not url:
                continue
            if is_probable_linkedin_company_url(url):
                return url

        for result in results:
            url = result.get("url")
            if url and "linkedin.com" in url:
                return url

        return None

    def find_company_profile(self, company_name: str) -> Dict[str, Any]:
        """
        Public API: Given a company name, return a normalized record.

        Returns:
            {
                "companyName": <input>,
                "searchQuery": <query used>,
                "linkedinUrl": <found url or None>,
                "infoStatus": "LinkedIn Found" | "LinkedIn Not Found" | "Error"
            }
        """
        query = self._build_search_query(company_name)
        logging.debug("Searching for company '%s' with query '%s'", company_name, query)

        try:
            search_results = self._search(query)
            linkedin_url = self._select_linkedin_url(search_results)
            if linkedin_url:
                status = "LinkedIn Found"
            else:
                status = "LinkedIn Not Found"
        except Exception as exc:
            logging.exception("Error while searching for '%s': %s", company_name, exc)
            linkedin_url = None
            status = "Error"

        return {
            "companyName": company_name,
            "searchQuery": query,
            "linkedinUrl": linkedin_url,
            "infoStatus": status,
        }