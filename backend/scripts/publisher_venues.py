"""IEEE and ACM conference membership, identified by the publisher's DOI prefix."""
import re

PUBLISHERS = {'10.1109/': 'ieee', '10.1145/': 'acm'}
# Satellite proceedings rather than the main conference track. "@" marks a
# workshop co-located with another event, e.g. ARMS-CC@PODC.
SATELLITE = re.compile(r'workshop|companion|adjunct|extended abstract|poster|demo|doctoral|@', re.IGNORECASE)
# DBLP files workshop volumes such as CCGridW and HiPCW under <conf><year>w.
WORKSHOP_TOC = re.compile(r'\d{4}w(\.html)?$')
# DOI resolvers whose URL path is the DOI itself. DBLP sometimes records only
# such a link, e.g. https://doi.ieeecomputersociety.org/10.1109/MIPR.2018.00041.
DOI_URL = re.compile(r'https?://(?:(?:dx\.)?doi\.org|doi\.ieeecomputersociety\.org|dl\.acm\.org/doi(?:/abs|/pdf)?)/(10\.\d+/\S+)')
# DBLP lists these papers only by legacy ACM citation IDs. Each DOI was checked
# in Crossref: ACM proceedings article, same title, DOI suffix equals the ID.
VERIFIED_DOIS = {
    'conf/icdcn/Chatterjee17': '10.1145/3007748.3007771',
    'conf/imc/DasariVBBDF18': '10.1145/3278532.3278533',
    'conf/imc/YadavSGSC18': '10.1145/3278532.3278555',
}


def dois_from_links(doi_values, urls):
    """Normalized DOIs from DBLP DOI fields and DOI-resolver links."""
    found = {doi.removeprefix('https://doi.org/').lower() for doi in doi_values}
    found |= {match.group(1).lower() for url in urls if (match := DOI_URL.match(url))}
    return sorted(found)


def publisher(paper):
    dois = paper.get('dois', []) + ([VERIFIED_DOIS[paper['key']]] if paper.get('key') in VERIFIED_DOIS else [])
    found = {name for doi in dois for prefix, name in PUBLISHERS.items() if doi.lower().startswith(prefix)}
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
