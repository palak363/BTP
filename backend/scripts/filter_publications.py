"""Paper-level filtering requires metadata, not substring venue matching."""
from venue_rules import classify_csr, load_rules


def filter_publications(papers):
    rules = load_rules()
    return [paper for paper in papers if classify_csr(paper, rules) is not None]
