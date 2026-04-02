import re
from datetime import date, timedelta

import requests

from models import Paper

BASE = "https://api.crossref.org/works"


def search(keywords: list[str], max_results: int = 25) -> list[Paper]:
    today = date.today()
    start = today - timedelta(days=30)

    query = " ".join(keywords)
    params = {
        "query": query,
        "filter": f"from-pub-date:{start.isoformat()}",
        "rows": max_results,
        "sort": "published",
        "order": "desc",
        "mailto": "academic-tracker@example.com",
    }

    print(f"  [Crossref] Searching: {query}")
    try:
        resp = requests.get(BASE, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [Crossref] Search failed: {e}")
        return []

    data = resp.json()
    items = data.get("message", {}).get("items", [])
    return _parse_items(items)


def _parse_items(items: list[dict]) -> list[Paper]:
    papers = []
    for item in items:
        try:
            title_list = item.get("title", [])
            title = title_list[0] if title_list else ""
            title = _clean_html(title)
            if not title:
                continue

            authors = []
            for auth in item.get("author", []):
                given = auth.get("given", "")
                family = auth.get("family", "")
                if family:
                    authors.append(f"{given} {family}".strip())

            abstract = _clean_html(item.get("abstract", ""))

            journal_list = item.get("container-title", [])
            journal = journal_list[0] if journal_list else ""

            # Parse date
            pub_date = ""
            date_parts = item.get("published", {}).get("date-parts", [[]])
            if date_parts and date_parts[0]:
                parts = date_parts[0]
                y = str(parts[0]) if len(parts) > 0 else ""
                m = str(parts[1]).zfill(2) if len(parts) > 1 else "01"
                d = str(parts[2]).zfill(2) if len(parts) > 2 else "01"
                pub_date = f"{y}-{m}-{d}"

            doi = item.get("DOI", "")
            url = f"https://doi.org/{doi}" if doi else item.get("URL", "")

            # Determine if preprint
            item_type = item.get("type", "")
            is_preprint = item_type == "posted-content" or "rxiv" in journal.lower()

            papers.append(Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                journal=journal,
                date=pub_date,
                doi=doi,
                url=url,
                source="crossref",
                is_preprint=is_preprint,
            ))
        except Exception:
            continue

    print(f"  [Crossref] Parsed {len(papers)} papers.")
    return papers


def _clean_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()
