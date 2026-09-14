"""CORE2023 venue membership, separate from CSRankings eligibility."""
import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
# Explicit DBLP-to-CORE aliases. No substring or DBLP key-prefix matching.
ALIASES = {
    'SIGMOD Conference': 'SIGMOD',
    'NIPS': 'NeurIPS', 'ICLR (Poster)': 'ICLR',
    'IEEE Symposium on Security and Privacy': 'S&P', 'SP': 'S&P',
    'USENIX Security Symposium': 'USENIX-Security', 'USENIX Security': 'USENIX-Security',
    'USENIX Annual Technical Conference': 'USENIX', 'USENIX ATC': 'USENIX',
    'Robotics: Science and Systems': 'RSS', 'Internet Measurement Conference': 'IMC',
    'Proc. VLDB Endow.': 'VLDB', 'PVLDB': 'VLDB',
    'Proc. ACM Interact. Mob. Wearable Ubiquitous Technol.': 'UbiComp',
    'IMWUT': 'UbiComp', 'SIGGRAPH Asia': 'SIGGRAPH Asia',
    'ACM Conference on Computer and Communications Security': 'CCS',
    'Proc. ACM Meas. Anal. Comput. Syst.': 'SIGMETRICS',
}
VENUE_IDS = {'SIGSOFT FSE': '52', 'ESEC/SIGSOFT FSE': '52', 'Proc. ACM Softw. Eng.': '52'}


def import_catalogue(path):
    entries = {}
    ambiguous = set()
    by_id = {}
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.reader(stream):
            if not row:
                continue
            if len(row) < 5 or row[3] != 'CORE2023':
                raise ValueError('Expected a headerless official CORE2023 CSV export')
            acronym = row[2].strip().casefold()
            value = {'id': row[0], 'title': row[1].strip(), 'acronym': row[2].strip(), 'rank': row[4]}
            by_id[row[0]] = value
            if acronym in entries and entries[acronym]['id'] != row[0]:
                ambiguous.add(acronym)
            entries[acronym] = value
    for acronym in ambiguous:
        del entries[acronym]
    if len(entries) < 100:
        raise ValueError('Incomplete CORE catalogue')
    payload = {'edition': 'CORE2023', 'source': 'https://portal.core.edu.au/conf-ranks/?source=CORE2023',
               'venues': entries, 'by_id': by_id, 'excluded_ambiguous_acronyms': sorted(ambiguous)}
    (BASE / 'data/raw/core_venues.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return payload


def classify_core(paper, csr, catalogue, rules):
    if paper['year'] < 1970:
        return None
    venue = csr['venue'] if csr else paper['venue']
    venue = re.sub(r' \(\d+\)$', '', venue)
    acronym = ALIASES.get(venue, venue)
    entry = (catalogue.get('by_id', {}).get(VENUE_IDS[venue]) if venue in VENUE_IDS
             else catalogue['venues'].get(acronym.casefold()))
    if not entry or entry['rank'] not in {'A*', 'A'}:
        return None
    # CORE ranks venues, not paper tracks. Our extension counts full papers;
    # journal proceedings must already pass the CSRankings issue-level checks.
    if not csr and (paper['type'] != 'inproceedings' or rules.pagecount(paper.get('pages', '')) < 6):
        return None
    return {'source': 'core-a-star' if entry['rank'] == 'A*' else 'core-a',
            'venue': entry['acronym'], 'area': csr['area'] if csr else 'core-other',
            'domain': csr['domain'] if csr else 'Other CORE areas',
            'year': csr['year'] if csr else paper['year']}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv')
    import_catalogue(parser.parse_args().csv)
