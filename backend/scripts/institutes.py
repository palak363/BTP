"""Indian institute rosters from the pinned CSRankings snapshot, with exact DBLP identities."""
import argparse
import csv
import json
import re
from pathlib import Path

import requests

from prepare_sources import REFERENCE, canonical, read_csv, verify_reference

BASE = Path(__file__).resolve().parents[1]
ROSTER = BASE / 'data/raw/india_faculty.csv'
UNRESOLVED = BASE / 'data/raw/india_unresolved.csv'
SPARQL = 'https://sparql.dblp.org/sparql'
IIT_CITIES = {'IIT (BHU) Varanasi': ['bhu', 'varanasi'], 'IIT (ISM) Dhanbad': ['ism', 'dhanbad']}
# Affiliation phrases that identify an institute in DBLP person records. Used only
# to choose between several DBLP people who share the CSRankings name.
AFFILIATION_HINTS = {
    'Ashoka University': ['ashoka university'],
    'BITS Pilani': ['birla institute of technology and science pilani', 'bits pilani'],
    'BITS Pilani-Goa': ['bits pilani goa', 'goa campus'],
    'CMI': ['chennai mathematical institute'],
    'DAIICT': ['dhirubhai ambani', 'daiict', 'da iict'],
    'IACS': ['indian association for the cultivation of science'],
    'IGDTUW': ['indira gandhi delhi technical university'],
    'IIIT Bangalore': ['iiit bangalore', 'international institute of information technology bangalore', 'iiit b'],
    'IIIT Delhi': ['iiit delhi', 'indraprastha institute of information technology', 'iiit d'],
    'IIIT Hyderabad': ['iiit hyderabad', 'international institute of information technology hyderabad', 'iiit h'],
    'IISc Bangalore': ['indian institute of science bangalore', 'indian institute of science bengaluru', 'iisc'],
    'IMSc': ['institute of mathematical sciences'],
    'ISI Kolkata': ['indian statistical institute'],
    'Jadavpur University': ['jadavpur university'],
    'Jaypee Univ. of Info. Tech.': ['jaypee university of information technology'],
    'KIIT Bhubaneswar': ['kiit', 'kalinga institute of industrial technology'],
    'Manipal Academy of Higher Education': ['manipal'],
    'NISER': ['national institute of science education and research', 'niser'],
    'NIT Jalandhar': ['national institute of technology jalandhar', 'nit jalandhar'],
    'National Inst. of Tech. Silchar': ['national institute of technology silchar', 'nit silchar'],
    'National Inst. of Tech. Warangal': ['national institute of technology warangal', 'nit warangal'],
    'Plaksha University': ['plaksha'],
    'Ravenshaw University': ['ravenshaw'],
    'SRM Inst. of Science and Tech.': ['srm institute of science and technology'],
    'Shiv Nadar University': ['shiv nadar'],
    'South Asian University': ['south asian university'],
    'Tata Inst. of Fundamental Research': ['tata institute of fundamental research', 'tata institute for fundamental research', 'tifr'],
    'University of Delhi': ['university of delhi', 'delhi university'],
    'VNIT Nagpur': ['visvesvaraya national institute of technology', 'vnit'],
}


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def normalize(text):
    return ' ' + re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip() + ' '


def hints(institution):
    if institution in AFFILIATION_HINTS:
        return AFFILIATION_HINTS[institution]
    cities = IIT_CITIES.get(institution, [institution.removeprefix('IIT ').lower()])
    return [form for city in cities for form in (f'indian institute of technology {city}', f'iit {city}')]


def indian_institutes(reference=REFERENCE):
    return {r['institution']: r['homepage'] for r in read_csv(reference / 'institutions.csv') if r['countryabbrv'] == 'in'}


def reference_rosters(reference=REFERENCE):
    """Canonical CSRankings faculty per Indian institute, in name order."""
    institutes = indian_institutes(reference)
    aliases = {r['alias']: r['name'] for r in read_csv(reference / 'dblp-aliases.csv')}
    people = {}
    for row in read_csv(reference / 'csrankings.csv'):
        if row['affiliation'] in institutes:
            name = canonical(row['name'], aliases)
            people.setdefault(name, {'institution': row['affiliation'], 'homepage': row['homepage']})
            if people[name]['institution'] != row['affiliation']:
                raise ValueError(f'{name} has several Indian affiliations in the reference')
    return institutes, people


def sparql(query):
    response = requests.get(SPARQL, params={'query': query}, headers={'Accept': 'application/sparql-results+json'}, timeout=180)
    response.raise_for_status()
    return response.json()['results']['bindings']


def candidates(names, predicate):
    """DBLP Person records whose label or alternate name equals each name exactly."""
    found = {}
    for start in range(0, len(names), 150):
        values = ' '.join(json.dumps(n) for n in names[start:start + 150])
        rows = sparql('PREFIX d: <https://dblp.org/rdf/schema#> SELECT DISTINCT ?name ?person ?affiliation ?webpage WHERE { '
                      f'VALUES ?name {{ {values} }} ?person {predicate} ?name ; a d:Person . '
                      'OPTIONAL { ?person d:affiliation ?affiliation } OPTIONAL { ?person d:webpage ?webpage } }')
        for row in rows:
            person = found.setdefault(row['name']['value'], {}).setdefault(row['person']['value'], {'affiliations': set(), 'webpages': set()})
            if 'affiliation' in row:
                person['affiliations'].add(row['affiliation']['value'])
            if 'webpage' in row:
                person['webpages'].add(row['webpage']['value'].rstrip('/').lower())
    return found


def choose(name, entry, matches, require_evidence=False):
    """Return (pid_url, method) or (None, reason).

    An alternate DBLP name can belong to a different person (CSRankings' T. V.
    Prabhakar is not DBLP's Prabhakar Venkata Tamma), so those matches need
    homepage or affiliation evidence even when there is a single candidate.
    """
    if len(matches) == 1 and not require_evidence:
        return next(iter(matches)), 'single match'
    if not matches:
        return None, 'no DBLP person with this name'
    homepage = entry['homepage'].rstrip('/').lower()
    by_page = [pid for pid, info in matches.items() if homepage and homepage in info['webpages']]
    if len(by_page) == 1:
        return by_page[0], 'homepage match'
    phrases = hints(entry['institution'])
    by_affiliation = [pid for pid, info in matches.items()
                      if any(f' {p} ' in normalize(a) for a in info['affiliations'] for p in phrases)]
    if len(by_affiliation) == 1:
        return by_affiliation[0], 'affiliation match'
    if len(matches) == 1:
        return None, 'only DBLP person with this alternate name has no homepage or affiliation evidence for this institute'
    return None, f'{len(matches)} DBLP people share this name; affiliation does not identify one'


def merge_duplicates(resolved):
    """CSRankings sometimes lists one person under an old and a numbered DBLP name."""
    by_person = {}
    for row in resolved:
        by_person.setdefault(row['dblp_url'], []).append(row)
    merged = []
    for rows in by_person.values():
        if len({r['institution'] for r in rows}) != 1:
            raise ValueError(f'One DBLP person in several institutes: {rows}')
        # Prefer the name DBLP itself uses, then the longest (most specific) name.
        rows.sort(key=lambda r: (r['resolution'] != 'exact name', -len(r['name']), r['name']))
        merged.append(dict(rows[0], aliases='|'.join(r['name'] for r in rows[1:])))
    return merged


def resolve():
    verify_reference()
    institutes, people = reference_rosters()
    names = sorted(people)
    exact = candidates(names, '<http://www.w3.org/2000/01/rdf-schema#label>')
    remaining = [n for n in names if len(exact.get(n, {})) != 1]
    alternate = candidates(remaining, 'd:creatorName')
    resolved, unresolved = [], []
    for name in names:
        matches = exact[name] if len(exact.get(name, {})) == 1 else alternate.get(name, {})
        pid, method = choose(name, people[name], matches, require_evidence=name in remaining)
        method = 'exact name' if name not in remaining else method
        row = {'institution': people[name]['institution'], 'name': name}
        if pid:
            resolved.append(dict(row, dblp_url=pid, resolution=method))
        else:
            unresolved.append(dict(row, reason=method, candidates=sorted(matches)))
    # A name with no evidence of its own may be CSRankings' second listing of a
    # person already resolved at the same institute, e.g. Y. Narahari / Y. Narahari 0001.
    known = {(r['institution'], r['dblp_url']) for r in resolved}
    for row in list(unresolved):
        same = [pid for pid in row['candidates'] if (row['institution'], pid) in known]
        if len(same) == 1:
            unresolved.remove(row)
            resolved.append({'institution': row['institution'], 'name': row['name'], 'dblp_url': same[0], 'resolution': 'duplicate listing'})
    for row in unresolved:
        row['candidates'] = ' '.join(p.removeprefix('https://dblp.org/pid/') for p in row['candidates'])
    resolved = merge_duplicates(resolved)
    for path, rows, fields in ((ROSTER, resolved, ['institution', 'name', 'dblp_url', 'resolution', 'aliases']),
                               (UNRESOLVED, unresolved, ['institution', 'name', 'reason', 'candidates'])):
        temporary = path.with_suffix('.tmp')
        with temporary.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(sorted(rows, key=lambda r: (r['institution'], r['name'])))
        temporary.replace(path)
    print(f'{len(institutes)} institutes; resolved {len(resolved)} of {len(names)} faculty; {len(unresolved)} unresolved.')


def load_rosters():
    """Resolved and unresolved faculty grouped by institute."""
    institutes, _ = reference_rosters()
    rosters = {name: {'name': name, 'slug': slug(name), 'homepage': homepage, 'faculty': [], 'unresolved': []}
               for name, homepage in sorted(institutes.items())}
    for row in read_csv(ROSTER):
        rosters[row['institution']]['faculty'].append(row)
    for row in read_csv(UNRESOLVED):
        rosters[row['institution']]['unresolved'].append(row)
    return {name: roster for name, roster in rosters.items() if roster['faculty'] or roster['unresolved']}


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    resolve()
