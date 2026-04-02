#!/usr/bin/env python3
"""Academic Paper Tracker - Search and report recent papers from top journals."""

import argparse
import sys
from datetime import datetime

from apis import pubmed, arxiv, crossref
from filters import filter_and_deduplicate
from report import generate_html


def main():
    parser = argparse.ArgumentParser(
        description="Track recent academic papers by keywords. "
        "Searches PubMed, arXiv, and Crossref for papers from the past 30 days."
    )
    parser.add_argument(
        "keywords",
        nargs="+",
        help="Search keywords (e.g., 'CRISPR' 'gene editing')",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output HTML file path (default: report_YYYYMMDD_HHMMSS.html)",
    )
    parser.add_argument(
        "--max-results", "-n",
        type=int,
        default=25,
        help="Max results per API source (default: 25)",
    )
    args = parser.parse_args()

    keywords = args.keywords
    max_results = args.max_results

    if args.output:
        output_path = args.output
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"report_{ts}.html"

    print(f"Academic Paper Tracker")
    print(f"Keywords: {', '.join(keywords)}")
    print(f"Searching papers from the past 30 days...\n")

    # Collect papers from all sources
    all_papers = []

    print("[1/3] Searching PubMed...")
    all_papers.extend(pubmed.search(keywords, max_results))

    print("\n[2/3] Searching arXiv...")
    all_papers.extend(arxiv.search(keywords, max_results))

    print("\n[3/3] Searching Crossref...")
    all_papers.extend(crossref.search(keywords, max_results))

    print(f"\nTotal raw results: {len(all_papers)}")

    # Filter and deduplicate
    peer_reviewed, preprints = filter_and_deduplicate(all_papers)
    print(f"After filtering: {len(peer_reviewed)} peer-reviewed, {len(preprints)} preprints")

    # Generate report
    print(f"\nGenerating HTML report...")
    path = generate_html(keywords, peer_reviewed, preprints, output_path)
    print(f"Report saved to: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
