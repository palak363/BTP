"""Complete DBLP bibliographies from the documented public SPARQL API."""
from collections import defaultdict
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import requests

CACHE = Path(__file__).resolve().parents[1] / 'data/cache/sparql'
SCHEMA = 'https://dblp.org/rdf/schema#'
RDF_TYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'


def parse_results(payload, pid_url, expected_name):
    rows = payload['results']['bindings']
    total = payload.get('meta', {}).get('result-size-total')
    if total is not None and total != len(rows):
        raise ValueError(f'Truncated SPARQL bibliography: {len(rows)} of {total} rows')
    subjects = defaultdict(lambda: defaultdict(set))
    for row in rows:
        subjects[row['subject']['value']][row['p']['value']].add(row['o']['value'])
    person = subjects.get(pid_url, {})
    names = (person.get(SCHEMA + 'creatorName', set()) | person.get(SCHEMA + 'primaryCreatorName', set())
             | person.get('http://www.w3.org/2000/01/rdf-schema#label', set()))
    if expected_name not in names:
        raise ValueError(f'PID identity mismatch for {expected_name}: {sorted(names)}')
    papers = []
    for uri, values in subjects.items():
        kinds = values.get(RDF_TYPE, set())
        kind = 'inproceedings' if SCHEMA + 'Inproceedings' in kinds else 'article' if SCHEMA + 'Article' in kinds else None
        if not kind:
            continue
        def value(field, default=''):
            entries = values.get(SCHEMA + field, set())
            if len(entries) > 1:
                raise ValueError(f'Ambiguous {field} in {uri}: {entries}')
            return next(iter(entries), default)
        authors = sorted(values.get(SCHEMA + 'authoredBy', set()))
        if not authors or pid_url not in authors:
            raise ValueError(f'Missing author identities: {uri}')
        if int(value('numberOfCreators', str(len(authors)))) != len(authors):
            raise ValueError(f'Creator count mismatch: {uri}')
        papers.append({
            'key': uri.removeprefix('https://dblp.org/rec/'), 'type': kind,
            'title': value('title'), 'year': int(value('yearOfPublication', '-1')),
            'venue': value('publishedInBook') or value('publishedInJournal') or value('publishedIn'),
            'booktitle': value('publishedInBook'), 'journal': value('publishedInJournal'),
            'volume': value('publishedInJournalVolume'),
            'number': value('publishedInJournalVolumeIssue'),
            'pages': value('pagination'), 'authors': authors,
            'url': value('listedOnTocPage') + '#' + uri.removeprefix('https://dblp.org/rec/'),
        })
    return papers


def fetch_papers(dblp_url, expected_name, refresh=False, offline=False):
    parsed = urlsplit(dblp_url)
    pid = parsed.path.removeprefix('/pid/').removesuffix('.html').removesuffix('.xml')
    if parsed.hostname not in {'dblp.org', 'dblp.uni-trier.de'} or not re.fullmatch(r'[A-Za-z0-9/-]+', pid):
        raise ValueError('Expected a valid DBLP PID URL')
    pid_url = 'https://dblp.org/pid/' + pid
    path = CACHE / (pid.replace('/', '_') + '.json')
    if path.exists() and not refresh:
        return parse_results(json.loads(path.read_text(encoding='utf-8')), pid_url, expected_name)
    if offline:
        raise FileNotFoundError(f'No SPARQL cache for {expected_name}')
    query = ('PREFIX d: <https://dblp.org/rdf/schema#> SELECT ?subject ?p ?o WHERE { '
             '{ VALUES ?subject { <' + pid_url + '> } } UNION { ?subject d:authoredBy <' + pid_url +
             '> } ?subject ?p ?o . FILTER(!isBlank(?o)) }')
    for attempt in range(4):
        try:
            response = requests.get('https://sparql.dblp.org/sparql', params={'query': query},
                                    headers={'Accept': 'application/sparql-results+json'}, timeout=120)
            response.raise_for_status()
            payload = response.json()
            papers = parse_results(payload, pid_url, expected_name)
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding='utf-8')
            time.sleep(1)
            return papers
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))
