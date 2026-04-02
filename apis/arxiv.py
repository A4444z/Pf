import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

import requests

from models import Paper

BASE = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def search(keywords: list[str], max_results: int = 50) -> list[Paper]:
    query = "+AND+".join(f'all:"{kw}"' for kw in keywords)
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    print(f"  [arXiv] Searching: {query}")
    try:
        resp = requests.get(BASE, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [arXiv] Search failed: {e}")
        return []

    return _parse_feed(resp.text)


def _parse_feed(xml_text: str) -> list[Paper]:
    papers = []
    cutoff = date.today() - timedelta(days=30)

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        print("  [arXiv] XML parse error")
        return []

    for entry in root.findall("atom:entry", NS):
        try:
            title = entry.findtext("atom:title", "", NS).strip().replace("\n", " ")
            if not title or title.startswith("Error"):
                continue

            published = entry.findtext("atom:published", "", NS)
            if not published:
                continue
            pub_date = datetime.fromisoformat(published.replace("Z", "+00:00")).date()
            if pub_date < cutoff:
                continue

            authors = []
            for author_el in entry.findall("atom:author", NS):
                name = author_el.findtext("atom:name", "", NS).strip()
                if name:
                    authors.append(name)

            abstract = entry.findtext("atom:summary", "", NS).strip().replace("\n", " ")

            # Get arxiv ID and links
            arxiv_id = entry.findtext("atom:id", "", NS).strip()
            pdf_url = ""
            for link in entry.findall("atom:link", NS):
                if link.get("title") == "pdf":
                    pdf_url = link.get("href", "")
                    break

            url = pdf_url or arxiv_id

            # Categories
            categories = []
            for cat in entry.findall("atom:category", NS):
                term = cat.get("term", "")
                if term:
                    categories.append(term)

            doi = ""
            # arXiv sometimes includes DOI in links
            for link in entry.findall("atom:link", NS):
                href = link.get("href", "")
                if "doi.org" in href:
                    doi = href.replace("https://doi.org/", "").replace("http://doi.org/", "")

            papers.append(Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                journal=f"arXiv [{', '.join(categories[:3])}]",
                date=pub_date.isoformat(),
                doi=doi,
                url=url,
                source="arxiv",
                is_preprint=True,
            ))
        except Exception:
            continue

    print(f"  [arXiv] Found {len(papers)} papers within 30 days.")
    return papers
