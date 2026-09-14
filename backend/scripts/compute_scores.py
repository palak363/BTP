"""Fractional publication credit; no arbitrary recency multiplier."""


def compute_score(papers):
    return sum(1 / len(paper['authors']) for paper in papers)
