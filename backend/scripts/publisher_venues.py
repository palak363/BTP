"""IEEE and ACM Transactions journal membership."""
import re

from journal_policy import transaction_publisher

# DOI resolvers whose URL path is the DOI itself. DBLP sometimes records only
# such a link, e.g. https://doi.ieeecomputersociety.org/10.1109/MIPR.2018.00041.
DOI_URL = re.compile(r'https?://(?:(?:dx\.)?doi\.org|doi\.ieeecomputersociety\.org|dl\.acm\.org/doi(?:/abs|/pdf)?)/(10\.\d+/\S+)')


def dois_from_links(doi_values, urls):
    """Normalized DOIs from DBLP DOI fields and DOI-resolver links."""
    found = {doi.removeprefix('https://doi.org/').lower() for doi in doi_values}
    found |= {match.group(1).lower() for url in urls if (match := DOI_URL.match(url))}
    return sorted(found)


def classify_publisher(paper, csr):
    """Classify ACM/IEEE Transactions articles; conference proceedings are excluded."""
    if paper['year'] < 1970:
        return None
    source = transaction_publisher(paper)
    if not source:
        return None
    return {'source': source, 'venue': paper.get('journal') or paper['venue'],
            'area': csr['area'] if csr else 'publisher-other',
            'domain': csr['domain'] if csr else 'Other IEEE/ACM areas',
            'year': csr['year'] if csr else paper['year']}
