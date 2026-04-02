import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import requests

from models import Paper

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def search(keywords: list[str], max_results: int = 25) -> list[Paper]:
    today = date.today()
    start = today - timedelta(days=30)

    query = " AND ".join(f'"{kw}"' for kw in keywords)
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "datetype": "edat",
        "mindate": start.strftime("%Y/%m/%d"),
        "maxdate": today.strftime("%Y/%m/%d"),
        "usehistory": "y",
        "retmode": "json",
    }

    print(f"  [PubMed] Searching: {query}")
    try:
        resp = requests.get(f"{BASE}/esearch.fcgi", params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [PubMed] Search failed: {e}")
        return []

    data = resp.json()
    id_list = data.get("esearchresult", {}).get("idlist", [])
    if not id_list:
        print("  [PubMed] No results found.")
        return []

    print(f"  [PubMed] Found {len(id_list)} IDs, fetching metadata...")
    time.sleep(0.4)  # rate limit courtesy

    try:
        fetch_resp = requests.get(
            f"{BASE}/efetch.fcgi",
            params={"db": "pubmed", "id": ",".join(id_list), "retmode": "xml"},
            timeout=30,
        )
        fetch_resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [PubMed] Fetch failed: {e}")
        return []

    return _parse_xml(fetch_resp.text)


def _parse_xml(xml_text: str) -> list[Paper]:
    papers = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        print("  [PubMed] XML parse error")
        return []

    for article in root.findall(".//PubmedArticle"):
        try:
            medline = article.find("MedlineCitation")
            art = medline.find("Article")

            title = art.findtext("ArticleTitle", "").strip()
            if not title:
                continue

            # Authors
            authors = []
            author_list = art.find("AuthorList")
            if author_list is not None:
                for author in author_list.findall("Author"):
                    last = author.findtext("LastName", "")
                    fore = author.findtext("ForeName", "")
                    if last:
                        authors.append(f"{fore} {last}".strip())

            # Abstract
            abstract_parts = []
            abstract_el = art.find("Abstract")
            if abstract_el is not None:
                for text_el in abstract_el.findall("AbstractText"):
                    label = text_el.get("Label", "")
                    content = "".join(text_el.itertext()).strip()
                    if label:
                        abstract_parts.append(f"{label}: {content}")
                    else:
                        abstract_parts.append(content)
            abstract = " ".join(abstract_parts)

            # Journal
            journal_el = art.find("Journal")
            journal = journal_el.findtext("Title", "") if journal_el is not None else ""

            # Date
            pub_date = ""
            date_el = medline.find(".//DateCompleted") or medline.find(".//DateRevised")
            if date_el is not None:
                y = date_el.findtext("Year", "")
                m = date_el.findtext("Month", "01").zfill(2)
                d = date_el.findtext("Day", "01").zfill(2)
                pub_date = f"{y}-{m}-{d}"

            # DOI
            doi = ""
            for eid in art.findall("EIdList/ELocationID"):
                if eid.get("EIdType") == "doi":
                    doi = eid.text or ""
                    break
            if not doi:
                for aid in article.findall(".//ArticleId"):
                    if aid.get("IdType") == "doi":
                        doi = aid.text or ""
                        break

            pmid = medline.findtext("PMID", "")
            url = f"https://doi.org/{doi}" if doi else f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

            papers.append(Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                journal=journal,
                date=pub_date,
                doi=doi,
                url=url,
                source="pubmed",
                is_preprint=False,
            ))
        except Exception:
            continue

    print(f"  [PubMed] Parsed {len(papers)} papers.")
    return papers
