from dataclasses import dataclass, field


@dataclass
class Paper:
    title: str
    authors: list[str]
    abstract: str
    journal: str
    date: str  # YYYY-MM-DD
    doi: str
    url: str
    source: str  # "pubmed", "arxiv", "crossref"
    is_preprint: bool

    def dedup_key(self) -> str:
        if self.doi:
            return self.doi.lower().strip()
        return self.title.lower().strip()
