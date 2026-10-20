"""IEEE and ACM conference membership, identified by the publisher's DOI prefix."""
import re

PUBLISHERS = {'10.1109/': 'ieee', '10.1145/': 'acm'}
# Satellite proceedings rather than the main conference track. "@" marks a
# workshop co-located with another event, e.g. ARMS-CC@PODC.
SATELLITE = re.compile(r'workshop|companion|adjunct|extended abstract|poster|demo|doctoral|@', re.IGNORECASE)
# DBLP files workshop volumes such as CCGridW and HiPCW under <conf><year>w.
WORKSHOP_TOC = re.compile(r'\d{4}w(\.html)?$')


def publisher(paper):
    found = {name for doi in paper.get('dois', []) for prefix, name in PUBLISHERS.items() if doi.lower().startswith(prefix)}
    return found.pop() if len(found) == 1 else None


def is_main_conference(paper):
    toc = paper.get('url', '').split('#')[0]
    return (paper['type'] == 'inproceedings' and not SATELLITE.search(paper.get('booktitle') or paper['venue'])
            and not WORKSHOP_TOC.search(toc))


def classify_publisher(paper, csr):
    """Main-conference papers of any length; journals and satellite events are excluded."""
    if paper['year'] < 1970 or not is_main_conference(paper):
        return None
    source = publisher(paper)
    if not source:
        return None
    return {'source': source, 'venue': re.sub(r' \(\d+\)$', '', paper.get('booktitle') or paper['venue']),
            'area': csr['area'] if csr else 'publisher-other',
            'domain': csr['domain'] if csr else 'Other IEEE/ACM areas',
            'year': csr['year'] if csr else paper['year']}
