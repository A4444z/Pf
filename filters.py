import re

from models import Paper

# High-impact journals for Biology, Chemistry, AI4S
HIGH_IMPACT_JOURNALS = {
    # Nature family
    "nature",
    "nature methods",
    "nature biotechnology",
    "nature chemistry",
    "nature chemical biology",
    "nature machine intelligence",
    "nature computational science",
    "nature catalysis",
    "nature synthesis",
    "nature communications",
    "nature biomedical engineering",
    "nature structural & molecular biology",
    "nature structural and molecular biology",
    "nature cell biology",
    "nature genetics",
    "nature reviews chemistry",
    "nature reviews drug discovery",
    "nature protocols",
    "nature materials",
    "nature nanotechnology",
    "nature physics",
    "nature medicine",
    "nature energy",
    "nature aging",
    "nature metabolism",
    "nature immunology",
    "nature microbiology",
    "nature plants",
    "nature reviews molecular cell biology",
    "nature chemical engineering",
    # Science family
    "science",
    "science advances",
    "science robotics",
    "science translational medicine",
    # Cell family
    "cell",
    "cell chemical biology",
    "cell reports",
    "cell systems",
    "cell research",
    "molecular cell",
    "cell stem cell",
    "chem",
    "joule",
    "matter",
    "cell reports physical science",
    # Chemistry top-tier
    "journal of the american chemical society",
    "jacs",
    "jacs au",
    "angewandte chemie",
    "angewandte chemie international edition",
    "chemical reviews",
    "chemical society reviews",
    "acs nano",
    "acs catalysis",
    "chemistry of materials",
    "acs central science",
    "acs energy letters",
    "nano letters",
    "accounts of chemical research",
    "journal of chemical information and modeling",
    # AI/ML for science
    "proceedings of the national academy of sciences",
    "pnas",
    "physical review letters",
    "physical review x",
    "journal of machine learning research",
    "jmlr",
    "digital discovery",
    "journal of chemical theory and computation",
    "journal of medicinal chemistry",
    # Additional broad-impact
    "advanced materials",
    "advanced functional materials",
    "advanced energy materials",
    "advanced science",
    "nucleic acids research",
    "genome biology",
    "genome research",
}

# Patterns for fuzzy matching (handles "Nature Foo" variants)
JOURNAL_PREFIXES = ["nature", "science", "cell", "acs", "advanced"]


def is_high_impact(journal_name: str) -> bool:
    if not journal_name:
        return False
    normalized = journal_name.lower().strip()
    # Remove common suffixes/noise
    normalized = re.sub(r"\s*\(.*?\)\s*$", "", normalized)

    if normalized in HIGH_IMPACT_JOURNALS:
        return True

    # Check if journal starts with a known high-impact prefix family
    for prefix in JOURNAL_PREFIXES:
        if normalized.startswith(prefix + " ") or normalized == prefix:
            return True

    # Partial match for common variations
    for hj in HIGH_IMPACT_JOURNALS:
        if hj in normalized or normalized in hj:
            return True

    return False


def filter_and_deduplicate(papers: list[Paper]) -> tuple[list[Paper], list[Paper]]:
    seen_keys = set()
    peer_reviewed = []
    preprints = []

    for paper in papers:
        key = paper.dedup_key()
        if key in seen_keys:
            continue
        seen_keys.add(key)

        if paper.is_preprint:
            preprints.append(paper)
        elif is_high_impact(paper.journal):
            peer_reviewed.append(paper)

    # Sort by date descending
    peer_reviewed.sort(key=lambda p: p.date, reverse=True)
    preprints.sort(key=lambda p: p.date, reverse=True)

    return peer_reviewed, preprints
