"""CORE2023 venue membership, separate from CSRankings eligibility."""
import csv
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
# Explicit DBLP-to-CORE aliases. No substring or DBLP key-prefix matching.
ALIASES = {
    'ACM Multimedia': 'ACMMM',
    'NAACL-HLT': 'NAACL', 'HLT-NAACL': 'NAACL', 'NAACL (Long Papers)': 'NAACL',
    'EMNLP/IJCNLP': 'EMNLP', 'EMNLP-IJCNLP': 'EMNLP', 'HLT/EMNLP': 'EMNLP',
    'ACL/IJCNLP': 'ACL', 'COLING-ACL': 'ACL',
    'SIGMOD Conference': 'SIGMOD',
    'NIPS': 'NeurIPS', 'ICLR (Poster)': 'ICLR',
    'IEEE Symposium on Security and Privacy': 'SP', 'S&P': 'SP',
    'USENIX Security Symposium': 'USENIX-Security', 'USENIX Security': 'USENIX-Security',
    'USENIX Annual Technical Conference': 'USENIX', 'USENIX ATC': 'USENIX',
    'Robotics: Science and Systems': 'RSS', 'Internet Measurement Conference': 'IMC',
    'Proc. VLDB Endow.': 'VLDB', 'PVLDB': 'VLDB',
    'Proc. ACM Interact. Mob. Wearable Ubiquitous Technol.': 'UbiComp',
    'IMWUT': 'UbiComp', 'SIGGRAPH Asia': 'SIGGRAPH Asia',
    'ACM Conference on Computer and Communications Security': 'CCS',
    'Proc. ACM Meas. Anal. Comput. Syst.': 'SIGMETRICS',
    'ECML/PKDD': 'ECML PKDD',
    'APPROX-RANDOM': 'APPROX/RANDOM',
    'ICSM': 'ICSME',
    'OOPSLA1': 'OOPSLA', 'OOPSLA2': 'OOPSLA',
    'Proc. Priv. Enhancing Technol.': 'PETS',
    'IEEE Trans. Vis. Comput. Graph.': 'IEEE VIS',
    'IEEE Visualization': 'IEEE VIS', 'VIS': 'IEEE VIS',
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


def resolve_core_entry(paper, csr, catalogue):
    """Resolve exact names; disambiguate Semantic Web using its verified DBLP series."""
    venue = csr['venue'] if csr else paper['venue']
    venue = re.sub(r' \(\d+\)$', '', venue)
    if venue == 'ISWC' and paper.get('key', '').startswith('conf/semweb/'):
        return catalogue.get('by_id', {}).get('1338')
    if venue == 'FSE' and csr and csr['area'] == 'fse':
        return catalogue.get('by_id', {}).get('52')
    # Only validated VIS journal issues may use the IEEE VIS rank.
    if venue == 'IEEE Trans. Vis. Comput. Graph.' and (not csr or csr['area'] != 'vis'):
        return None
    acronym = ALIASES.get(venue, venue)
    entry = (catalogue.get('by_id', {}).get(VENUE_IDS[venue]) if venue in VENUE_IDS
             else catalogue['venues'].get(acronym.casefold()))
    if entry is None:
        matches = [value for value in catalogue.get('by_id', {}).values()
                   if value['title'].casefold() == venue.casefold()]
        entry = matches[0] if len(matches) == 1 else None
    return entry


def classify_core(paper, csr, catalogue, rules):
    if paper['year'] < 1970:
        return None
    entry = resolve_core_entry(paper, csr, catalogue)
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
