"""Download pinned reference inputs and resolve exact DBLP identities."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import requests

BASE = Path(__file__).resolve().parents[1]
REFERENCE = BASE / 'data/reference'
MANIFEST = json.loads(Path(__file__).with_name('reference_manifest.json').read_text(encoding='utf-8'))
REVISION = MANIFEST['revision']
FILES = ['util/csrankings.py', 'sigcse-research-articles.csv',
         'csrankings.csv', 'dblp-aliases.csv', 'generated-author-info.csv']


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def canonical(name, aliases):
    seen = set()
    while name in aliases and name not in seen:
        seen.add(name)
        name = aliases[name]
    return name


def verify_reference(reference=REFERENCE):
    for filename, expected in MANIFEST['sha256'].items():
        path = reference / filename
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Missing or mismatched pinned source: {path}. Run prepare_sources.py --download-only.')


def prepare(download_only=False, core=False):
    REFERENCE.mkdir(parents=True, exist_ok=True)
    for filename in FILES:
        target = REFERENCE / Path(filename).name
        expected = MANIFEST['sha256'][target.name]
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            response = requests.get(
                f'https://raw.githubusercontent.com/emeryberger/CSrankings/{REVISION}/{filename}',
                timeout=120)
            response.raise_for_status()
            if hashlib.sha256(response.content).hexdigest() != expected:
                raise ValueError(f'Checksum mismatch for {filename}')
            target.write_bytes(response.content)
    verify_reference()
    (REFERENCE / 'revision.txt').write_text(REVISION)
    if core:
        response = requests.get('https://portal.core.edu.au/conf-ranks/',
            params={'search': '', 'by': 'all', 'source': 'CORE2023', 'sort': 'atitle', 'page': 1, 'do': 'Export'},
            timeout=120)
        response.raise_for_status()
        path = REFERENCE / 'core2023.csv'
        path.write_bytes(response.content)
        from core_venues import import_catalogue
        import_catalogue(path)
    if download_only:
        return
    aliases = {r['alias']: r['name'] for r in read_csv(REFERENCE / 'dblp-aliases.csv')}
    names = sorted({canonical(r['name'], aliases) for r in read_csv(REFERENCE / 'csrankings.csv')
                    if r['affiliation'] == 'IIIT Delhi'})
    query = ('PREFIX d: <https://dblp.org/rdf/schema#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> '
             'SELECT DISTINCT ?name ?person WHERE { VALUES ?name { ' + ' '.join(json.dumps(n) for n in names) +
             ' } ?person rdfs:label ?name ; a d:Person . }')
    response = requests.get('https://sparql.dblp.org/sparql', params={'query': query},
                            headers={'Accept': 'application/sparql-results+json'}, timeout=120)
    response.raise_for_status()
    matches = {}
    for binding in response.json()['results']['bindings']:
        matches.setdefault(binding['name']['value'], set()).add(binding['person']['value'])
    result = []
    for name in names:
        candidates = matches.get(name, set())
        if len(candidates) != 1:
            raise ValueError(f'Expected one exact DBLP identity for {name}: {candidates}')
        url = next(iter(candidates))
        result.append({'name': name, 'dblp_url': url, 'area': 'Unknown'})
        print(name, url, flush=True)
    destination = BASE / 'data/raw/iiitd_faculty.csv'
    temporary = destination.with_suffix('.tmp')
    with temporary.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['name', 'dblp_url', 'area'])
        writer.writeheader()
        writer.writerows(result)
    temporary.replace(destination)
    print(f'Resolved {len(result)} faculty.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download-only', action='store_true')
    parser.add_argument('--core', action='store_true', help='Refresh the official CORE2023 catalogue')
    args = parser.parse_args()
    prepare(args.download_only, args.core)
