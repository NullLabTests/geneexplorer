import re
import requests
from langchain_core.tools import tool
from typing import Optional

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@tool
def web_search(query: str) -> str:
    """General web search for public genetics information. Use for confirmation, finding relevant studies, or when primary databases are insufficient. Input: a search query string."""

    # Try NCBI EUtilities as a reliable public source for literature
    try:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": 5,
            "retmode": "json",
        }
        search_resp = requests.get(
            f"{PUBMED_BASE}/esearch.fcgi",
            params=params,
            timeout=30,
        )
        search_resp.raise_for_status()
        search_data = search_resp.json()

        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return f"No PubMed results found for query: {query}"

        # Fetch summaries for top results
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list[:5]),
            "rettype": "abstract",
            "retmode": "xml",
        }
        fetch_resp = requests.get(
            f"{PUBMED_BASE}/efetch.fcgi",
            params=fetch_params,
            timeout=30,
        )
        fetch_resp.raise_for_status()

        # Simple extraction of titles and DOIs from XML
        titles = re.findall(r"<ArticleTitle>(.*?)</ArticleTitle>", fetch_resp.text, re.DOTALL)
        dois = re.findall(r"<ELocationID EIdType=\"doi\"[^>]*>(.*?)</ELocationID>", fetch_resp.text)

        results = [f"PubMed search results for '{query}':"]
        for i, title in enumerate(titles[:5]):
            doi = dois[i] if i < len(dois) else ""
            pmid = id_list[i] if i < len(id_list) else ""
            line = f"- {title.strip()}"
            if pmid:
                line += f"\n  PMID: {pmid}"
            if doi:
                line += f"\n  DOI: {doi}"
            results.append(line)

        if len(results) == 1:
            return f"No article details could be parsed for query: {query}"

        return "\n".join(results)

    except requests.exceptions.RequestException as e:
        return f"Error searching PubMed for '{query}': {e}"


@tool
def fetch_pubmed_abstract(pmid: str) -> str:
    """Fetch the abstract of a PubMed article by its PMID. Input: PMID as a string of digits."""
    pmid = pmid.strip()
    if not pmid.isdigit():
        return f"Invalid PMID: '{pmid}'. Please provide a numeric PubMed ID."

    try:
        params = {
            "db": "pubmed",
            "id": pmid,
            "rettype": "abstract",
            "retmode": "xml",
        }
        resp = requests.get(
            f"{PUBMED_BASE}/efetch.fcgi",
            params=params,
            timeout=30,
        )
        resp.raise_for_status()

        title = re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", resp.text, re.DOTALL)
        abstract = re.search(r"<AbstractText[^>]*>(.*?)</AbstractText>", resp.text, re.DOTALL)
        journal = re.search(r"<Journal><Title>(.*?)</Title>", resp.text, re.DOTALL)
        year = re.search(r"<PubDate><Year>(.*?)</Year>", resp.text, re.DOTALL)

        lines = [f"PubMed article PMID: {pmid}"]
        if title:
            lines.append(f"Title: {title.group(1).strip()}")
        if journal:
            lines.append(f"Journal: {journal.group(1).strip()}")
        if year:
            lines.append(f"Year: {year.group(1).strip()}")
        if abstract:
            text = abstract.group(1).strip()
            if len(text) > 1500:
                text = text[:1500] + "..."
            lines.append(f"Abstract: {text}")
        else:
            lines.append("(No abstract available)")

        return "\n".join(lines)

    except requests.exceptions.RequestException as e:
        return f"Error fetching PubMed article {pmid}: {e}"
