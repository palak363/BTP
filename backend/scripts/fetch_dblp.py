"""Fetch complete, PID-identified DBLP bibliographies without losing metadata."""
import time
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import requests

CACHE = Path(__file__).resolve().parents[1] / 'data' / 'cache' / 'dblp'


def element_text(element, field):
    child = element.find(field)
    return ''.join(child.itertext()).strip() if child is not None else ''


def parse_profile(content, expected_name=None):
    root = ET.fromstring(content)
    if root.tag != 'dblpperson':
        raise ValueError('Response is not a DBLP person bibliography')
    aliases = {''.join(a.itertext()).strip() for a in root.findall('./person/author')}
    aliases.add(root.get('name', ''))
    if expected_name and expected_name not in aliases:
        raise ValueError(f'PID identity mismatch: {expected_name!r}; profile aliases: {sorted(aliases)}')
    papers = {}
    for wrapper in root.findall('r'):
        for entry in wrapper:
            if entry.tag not in {'article', 'inproceedings'}:
                continue
            key = entry.get('key')
            if not key:
                raise ValueError('Publication has no DBLP key')
            paper = {field: element_text(entry, field) for field in
                     ('title', 'year', 'booktitle', 'journal', 'volume', 'number', 'pages', 'url')}
            paper.update(key=key, type=entry.tag, authors=[
                ''.join(a.itertext()).strip() for a in entry.findall('author')])
            paper['venue'] = paper['booktitle'] or paper['journal']
            paper['year'] = int(paper['year'])
            if not paper['authors']:
                raise ValueError(f'Publication {key} has no authors')
            papers[key] = paper
    return list(papers.values())


def fetch_papers(dblp_url, expected_name=None, refresh=False, offline=False):
    parsed = urlsplit(dblp_url)
    if parsed.hostname not in {'dblp.org', 'dblp.uni-trier.de'} or not parsed.path.startswith('/pid/'):
        raise ValueError(f'Expected a DBLP PID URL: {dblp_url}')
    pid = parsed.path[5:].removesuffix('.html').removesuffix('.xml')
    cache = CACHE / (pid.replace('/', '_') + '.xml')
    if cache.exists() and not refresh:
        return parse_profile(cache.read_bytes(), expected_name)
    if offline:
        raise FileNotFoundError(f'No cached bibliography for {expected_name or pid}')
    for attempt in range(4):
        try:
            response = requests.get(f'https://dblp.org/pid/{pid}.xml', timeout=60,
                                    headers={'User-Agent': 'IIITD-Research-Pipeline/1.0'})
            response.raise_for_status()
            if 'html' in response.headers.get('Content-Type', ''):
                raise RuntimeError('DBLP returned an HTML challenge. No dataset was replaced; retry later or use cached XML.')
            papers = parse_profile(response.content, expected_name)
            CACHE.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(response.content)
            time.sleep(1)
            return papers
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))
