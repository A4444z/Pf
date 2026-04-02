#!/usr/bin/env python3
"""MCP Server for the Academic Paper Tracker.

Exposes paper search as tools that Claude Code can call directly.
Add to your Claude Code settings to enable.
"""

import os
import sys
from dataclasses import asdict
from datetime import datetime

# Ensure the project root is on the path so apis/ imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

from apis import pubmed, arxiv, crossref
from filters import filter_and_deduplicate
from report import generate_html

mcp = FastMCP("academic-paper-tracker")


def _paper_to_dict(paper) -> dict:
    return {
        "title": paper.title,
        "authors": paper.authors[:5],
        "abstract": paper.abstract[:600] if paper.abstract else "",
        "journal": paper.journal,
        "date": paper.date,
        "doi": paper.doi,
        "url": paper.url,
        "source": paper.source,
        "is_preprint": paper.is_preprint,
    }


@mcp.tool()
def search_papers(
    keywords: list[str],
    max_results_per_source: int = 25,
    generate_report: bool = True,
    output_path: str = "",
) -> dict:
    """Search for recent academic papers (past 30 days) across PubMed, arXiv, and Crossref.

    Filters peer-reviewed results to high-impact journals in biology, chemistry,
    and AI for science (Nature/Science/Cell families, JACS, Angew, etc.).
    Preprints from arXiv are included without tier restriction.

    Args:
        keywords: Search keywords, e.g. ["CRISPR", "gene editing"]
        max_results_per_source: Maximum results to fetch per API (default 25)
        generate_report: Whether to generate an HTML report file (default True)
        output_path: Custom output path for the HTML report (optional)

    Returns:
        Dictionary with peer_reviewed papers, preprints, and report file path.
    """
    all_papers = []

    # Search all three APIs
    all_papers.extend(pubmed.search(keywords, max_results_per_source))
    all_papers.extend(arxiv.search(keywords, max_results_per_source))
    all_papers.extend(crossref.search(keywords, max_results_per_source))

    # Filter and deduplicate
    peer_reviewed, preprints = filter_and_deduplicate(all_papers)

    result = {
        "keywords": keywords,
        "total_raw": len(all_papers),
        "peer_reviewed_count": len(peer_reviewed),
        "preprint_count": len(preprints),
        "peer_reviewed": [_paper_to_dict(p) for p in peer_reviewed],
        "preprints": [_paper_to_dict(p) for p in preprints],
        "report_path": None,
    }

    # Generate HTML report
    if generate_report:
        if not output_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                f"report_{ts}.html",
            )
        path = generate_html(keywords, peer_reviewed, preprints, output_path)
        result["report_path"] = path

    return result


@mcp.tool()
def search_papers_text(
    keywords: list[str],
    max_results_per_source: int = 25,
) -> str:
    """Search for recent academic papers and return a text summary.

    Same search as search_papers but returns a concise text summary
    instead of structured data. Useful for quick lookups.

    Args:
        keywords: Search keywords, e.g. ["CRISPR", "gene editing"]
        max_results_per_source: Maximum results to fetch per API (default 25)

    Returns:
        Formatted text summary of found papers.
    """
    all_papers = []
    all_papers.extend(pubmed.search(keywords, max_results_per_source))
    all_papers.extend(arxiv.search(keywords, max_results_per_source))
    all_papers.extend(crossref.search(keywords, max_results_per_source))

    peer_reviewed, preprints = filter_and_deduplicate(all_papers)

    lines = []
    lines.append(f"# Paper Search: {', '.join(keywords)}")
    lines.append(f"Found {len(peer_reviewed)} peer-reviewed + {len(preprints)} preprints\n")

    if peer_reviewed:
        lines.append("## Peer-Reviewed (High-Impact Journals)")
        for i, p in enumerate(peer_reviewed, 1):
            authors = ", ".join(p.authors[:3])
            if len(p.authors) > 3:
                authors += " et al."
            lines.append(f"\n{i}. **{p.title}**")
            lines.append(f"   {authors}")
            lines.append(f"   {p.journal} | {p.date}")
            if p.abstract:
                lines.append(f"   {p.abstract[:300]}...")
            lines.append(f"   URL: {p.url}")

    if preprints:
        lines.append("\n## Preprints")
        for i, p in enumerate(preprints, 1):
            authors = ", ".join(p.authors[:3])
            if len(p.authors) > 3:
                authors += " et al."
            lines.append(f"\n{i}. **{p.title}**")
            lines.append(f"   {authors}")
            lines.append(f"   {p.journal} | {p.date}")
            if p.abstract:
                lines.append(f"   {p.abstract[:300]}...")
            lines.append(f"   URL: {p.url}")

    if not peer_reviewed and not preprints:
        lines.append("No papers found matching these keywords in the past 30 days.")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
