"""Auditable per-institute datasets for every Indian institute in the pinned CSRankings roster."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from fetch_dblp import fetch_papers
from institutes import load_rosters, slug
from prepare_sources import read_csv, canonical, verify_reference
from publisher_venues import classify_publisher
from venue_rules import REFERENCE, AREA_NAMES, AREA_GROUPS, OPTIONAL_VENUES, classify_csr, load_rules

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / 'data/processed'
INSTITUTES = OUTPUT / 'institutes'
INDEX = OUTPUT / 'institutes.json'
SOURCES = ['csrankings', 'core-a-star', 'core-a', 'ieee', 'acm']
DEFAULT_WINDOW = (2016, 2026)


def dataset_path(name):
    return INSTITUTES / f'{slug(name)}.json'


def summarize(dataset, start_year, end_year, sources=('csrankings',), areas=None, include_optional=False):
    if dataset['metadata'].get('data_source') == 'csrankings-published-counts':
        return summarize_reference(dataset, start_year, end_year, sources, areas, include_optional)
    selected = []
    for paper in dataset['publications']:
        memberships = [m for m in paper['memberships']
                       if m['source'] in sources and start_year <= m['year'] <= end_year
                       and (m['source'] != 'csrankings' or include_optional or m['area'] not in OPTIONAL_VENUES)
                       and (not areas or m['domain'] in areas)]
        if memberships:
            # CSRankings conference-year corrections take precedence in a union.
            selected.append((paper, memberships[0]))
    faculties = {f['name']: dict(f, papers=0, score=0.0, domains=Counter(), venues=Counter())
                 for f in dataset['faculty']}
    domains, venues = Counter(), Counter()
    adjusted_domains = Counter()
    for paper, membership in selected:
        domain, venue = membership['domain'], membership['venue']
        domains[domain] += 1
        venues[venue] += 1
        credit = 1 / len(paper['authors'])
        for name in paper['faculty']:
            faculty = faculties[name]
            faculty['papers'] += 1
            faculty['score'] += credit
            faculty['domains'][domain] += 1
            faculty['venues'][venue] += 1
            adjusted_domains[domain] += credit
    rows = []
    for faculty in faculties.values():
        faculty['adjusted_count'] = faculty['score']
        faculty['top_domain'] = max(faculty['domains'], key=faculty['domains'].get, default='No selected papers')
        faculty['top_venues'] = [{'venue': v, 'papers': c} for v, c in faculty.pop('venues').most_common()]
        rows.append(faculty)
    rows.sort(key=lambda f: (-f['score'], -f['papers'], f['name']))
    selected_areas = areas or list(AREA_GROUPS)
    return {
        'metadata': dataset['metadata'], 'filters': {'start_year': start_year, 'end_year': end_year,
        'sources': list(sources), 'areas': areas or [], 'include_optional': include_optional},
        'total_faculty': len(rows), 'total_papers': len(selected),
        'faculty_paper_count': sum(f['papers'] for f in rows),
        'adjusted_count': sum(f['score'] for f in rows),
        'average_count': (math.exp(sum(math.log1p(adjusted_domains[a]) for a in selected_areas) / len(selected_areas))
                          if set(sources) == {'csrankings'} else None),
        'domain_distribution': dict(domains),
        'top_areas': [{'area': a, 'papers': c} for a, c in domains.most_common()],
        'top_venues': [{'venue': v, 'papers': c} for v, c in venues.most_common()],
        'faculty_rankings': rows,
    }


def summarize_reference(dataset, start_year, end_year, sources, areas, include_optional):
    if set(sources) != {'csrankings'}:
        raise ValueError('CORE, IEEE and ACM require a complete DBLP bibliography build.')
    faculties = {f['name']: dict(f, papers=0, score=0.0, domains=Counter(), venues=Counter())
                 for f in dataset['faculty']}
    domains, venues, adjusted_domains = Counter(), Counter(), Counter()
    for cell in dataset['counts']:
        if not include_optional and cell['area'] in OPTIONAL_VENUES:
            continue
        domain = AREA_NAMES.get(cell['area'], cell['area'])
        if not start_year <= cell['year'] <= end_year or (areas and domain not in areas):
            continue
        faculty = faculties[cell['name']]
        faculty['papers'] += cell['count']
        faculty['score'] += cell['adjustedcount']
        faculty['domains'][domain] += cell['count']
        faculty['venues'][cell['area']] += cell['count']
        domains[domain] += cell['count']
        venues[cell['area']] += cell['count']
        adjusted_domains[domain] += cell['adjustedcount']
    rows = []
    for faculty in faculties.values():
        faculty['adjusted_count'] = faculty['score']
        faculty['top_domain'] = max(faculty['domains'], key=faculty['domains'].get, default='No selected papers')
        faculty['top_venues'] = [{'venue': v, 'papers': c} for v, c in faculty.pop('venues').most_common()]
        rows.append(faculty)
    rows.sort(key=lambda f: (-f['score'], -f['papers'], f['name']))
    return {'metadata': dataset['metadata'],
            'filters': {'start_year': start_year, 'end_year': end_year, 'sources': list(sources), 'areas': areas or [], 'include_optional': include_optional},
            'total_faculty': len(rows), 'total_papers': None,
            'faculty_paper_count': sum(f['papers'] for f in rows),
            'adjusted_count': sum(f['score'] for f in rows),
            'domain_distribution': dict(domains),
            'top_areas': [{'area': a, 'papers': c} for a, c in domains.most_common()],
            'top_venues': [{'venue': v, 'papers': c} for v, c in venues.most_common()],
            'faculty_rankings': rows}


def write_json(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def roster_aliases(roster):
    """Reference names (DBLP aliases and merged CSRankings duplicates) -> roster name."""
    aliases = {r['alias']: r['name'] for r in read_csv(REFERENCE / 'dblp-aliases.csv')}
    mapping = {}
    for member in roster['faculty']:
        mapping[member['name']] = member['name']
        for alias in filter(None, member.get('aliases', '').split('|')):
            mapping[alias] = member['name']
    return lambda name: mapping.get(canonical(name, aliases), mapping.get(name))


def build_reference(roster):
    """Explicit published-count baseline when live DBLP is unavailable."""
    verify_reference()
    resolve = roster_aliases(roster)
    names = [m['name'] for m in roster['faculty']]
    counts = []
    for row in read_csv(REFERENCE / 'generated-author-info.csv'):
        name = resolve(row['name'])
        if row['dept'] == roster['name'] and name:
            counts.append(dict(name=name, area=row['area'], year=int(row['year']),
                               count=int(float(row['count'])), adjustedcount=float(row['adjustedcount'])))
    dataset = {'metadata': {
        'schema_version': 3, 'institution': roster['name'], 'slug': roster['slug'], 'homepage': roster['homepage'],
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'reference_revision': (REFERENCE / 'revision.txt').read_text().strip(),
        'data_source': 'csrankings-published-counts',
        'available_sources': ['csrankings'], 'core_edition': 'CORE2023',
        'available_areas': list(AREA_GROUPS),
        'area_names': AREA_NAMES,
        'optional_venues': sorted(OPTIONAL_VENUES),
        'unresolved_faculty': roster['unresolved'],
        'counting': 'Published CSRankings faculty counts, including optional venues. Raw totals count faculty authorships; unique paper counts are unavailable.',
        'validation': {'mode': 'published-reference', 'independently_recomputed': False},
        'limitations': ['Live DBLP refresh is required for CORE A/A*, IEEE, ACM counts and unique publication totals.']},
        'faculty': [{'name': m['name'], 'dblp_url': m['dblp_url']} for m in roster['faculty']],
        'counts': counts, 'publications': []}
    write_json(dataset_path(roster['name']), dataset)
    print(f"Published reference baseline for {roster['name']}: {len(names)} faculty; {len(counts)} area/year cells.")
    return dataset


def compare_reference(dataset, reference, resolve):
    """Every faculty/venue/year cell against the pinned CSRankings counts."""
    names = {f['name'] for f in dataset['faculty']}
    expected, actual = defaultdict(lambda: [0, 0.0]), defaultdict(lambda: [0, 0.0])
    for row in read_csv(reference / 'generated-author-info.csv'):
        name = resolve(row['name'])
        if row['dept'] == dataset['metadata']['institution'] and name in names:
            key = (name, row['area'], int(row['year']))
            expected[key][0] += int(float(row['count']))
            expected[key][1] += float(row['adjustedcount'])
    for paper in dataset['publications']:
        for membership in paper['memberships']:
            if membership['source'] == 'csrankings':
                for name in paper['faculty']:
                    key = (name, membership['area'], membership['year'])
                    actual[key][0] += 1
                    actual[key][1] += 1 / len(paper['authors'])
    differences = []
    for key in sorted(expected.keys() | actual.keys()):
        e, a = expected[key], actual[key]
        # Upstream CSV serializes adjusted counts with five significant digits.
        tolerance = max(0.00006, abs(e[1]) * 0.00006)
        if e[0] != a[0] or abs(e[1] - a[1]) > tolerance:
            differences.append(dict(name=key[0], area=key[1], year=key[2],
                                    expected_papers=e[0], actual_papers=a[0],
                                    expected_adjusted=e[1], actual_adjusted=a[1]))
    missing = [d for d in differences if d['actual_papers'] < d['expected_papers']]
    return {'institution': dataset['metadata']['institution'],
            'reference_revision': dataset['metadata']['reference_revision'],
            'compared_cells': len(expected.keys() | actual.keys()),
            'expected_papers': sum(e[0] for e in expected.values()),
            'actual_papers': sum(a[0] for a in actual.values()),
            'matching': not differences, 'missing_cells': len(missing),
            'extra_cells': len(differences) - len(missing), 'differences': differences,
            'note': 'Live DBLP and the pinned CSRankings publication snapshot may differ; no counts are overwritten. '
                    'Missing cells: the reference counts papers this build does not. Extra cells: this build counts papers the reference does not.'}


def build_institute(roster, rules, core, fetch, refresh=False, offline=False, backend='sparql'):
    publications = {}
    for member in roster['faculty']:
        for paper in fetch(member['dblp_url'], member['name'], refresh, offline):
            if paper['key'] in publications:
                previous = publications[paper['key']]
                if any(previous[field] != paper[field] for field in ('authors', 'venue', 'year', 'pages')):
                    raise ValueError(f"Inconsistent cached records for {paper['key']}; refresh bibliographies together.")
                if member['name'] not in previous['faculty']:
                    previous['faculty'].append(member['name'])
                continue
            csr = classify_csr(paper, rules)
            memberships = [dict(csr, source='csrankings')] if csr else []
            if core:
                from core_venues import classify_core
                membership = classify_core(paper, csr, core, rules)
                if membership:
                    memberships.append(membership)
            membership = classify_publisher(paper, csr)
            if membership:
                memberships.append(membership)
            if memberships:
                publications[paper['key']] = dict(paper, faculty=[member['name']], memberships=memberships)
    return {
        'metadata': {
            'schema_version': 3, 'institution': roster['name'], 'slug': roster['slug'], 'homepage': roster['homepage'],
            'data_source': 'dblp-' + backend,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'reference_revision': (REFERENCE / 'revision.txt').read_text().strip(),
            'rules_sha256': hashlib.sha256((REFERENCE / 'csrankings.py').read_bytes()).hexdigest(),
            'available_sources': ['csrankings'] + (['core-a-star', 'core-a'] if core else []) + ['ieee', 'acm'],
            'core_edition': core['edition'] if core else None,
            'available_areas': list(AREA_GROUPS) + (['Other CORE areas'] if core else []) + ['Other IEEE/ACM areas'],
            'area_names': AREA_NAMES,
            'optional_venues': sorted(OPTIONAL_VENUES),
            'unresolved_faculty': [{'name': u['name'], 'reason': u['reason']} for u in roster['unresolved']],
            'counting': 'Unique DBLP keys; faculty credit is 1 / all authors; all reference venues, including optional venues.',
        },
        'faculty': [{'name': m['name'], 'dblp_url': m['dblp_url']} for m in roster['faculty']],
        'publications': sorted(publications.values(), key=lambda p: p['key']),
    }


def index_entry(dataset, report):
    start, end = DEFAULT_WINDOW
    totals = {}
    for key, sources in [(s, [s]) for s in dataset['metadata']['available_sources']] + [('all', dataset['metadata']['available_sources'])]:
        summary = summarize(dataset, start, end, sources)
        totals[key] = {'papers': summary['total_papers'], 'faculty_papers': summary['faculty_paper_count'],
                       'adjusted': round(summary['adjusted_count'], 4)}
    meta = dataset['metadata']
    return {'name': meta['institution'], 'slug': meta['slug'], 'homepage': meta['homepage'],
            'faculty': len(dataset['faculty']), 'unresolved': len(meta['unresolved_faculty']),
            'totals': totals, 'validation': {k: report[k] for k in ('compared_cells', 'missing_cells', 'extra_cells', 'expected_papers', 'actual_papers')}}


def write_index(entries, rosters, metadata):
    index = {'metadata': dict(metadata, generated_at=datetime.now(timezone.utc).isoformat(), default_window=list(DEFAULT_WINDOW)),
             'institutes': sorted(entries.values(), key=lambda e: e['name']),
             'faculty': sorted(({'name': m['name'], 'institution': r['name'], 'slug': r['slug'], 'dblp_url': m['dblp_url']}
                                for r in rosters.values() if r['name'] in entries for m in r['faculty']), key=lambda f: f['name'])}
    write_json(INDEX, index)


def build(only=None, offline=False, refresh=False, backend='sparql', allow_reference_differences=False):
    verify_reference()
    rules = load_rules()
    if backend == 'sparql':
        from fetch_sparql import fetch_papers as fetch
    else:
        fetch = fetch_papers
    core_path = BASE / 'data/raw/core_venues.json'
    core = json.loads(core_path.read_text(encoding='utf-8-sig')) if core_path.exists() else None
    rosters = load_rosters()
    selected = [rosters[name] for name in only] if only else list(rosters.values())
    # Stage every dataset in memory; nothing is written unless all builds succeed.
    built, failures = {}, []
    for roster in selected:
        print(f"Building {roster['name']} ({len(roster['faculty'])} faculty)...", flush=True)
        dataset = build_institute(roster, rules, core, fetch, refresh, offline, backend)
        report = compare_reference(dataset, REFERENCE, roster_aliases(roster))
        if report['missing_cells'] and not allow_reference_differences:
            failures.append(roster['name'])
            write_json(INSTITUTES / f"{roster['slug']}.validation_failed.json", report)
        dataset['metadata']['validation'] = {k: report[k] for k in ('matching', 'compared_cells', 'missing_cells', 'extra_cells')}
        built[roster['name']] = (dataset, report)
    if failures:
        raise ValueError(f'CSRankings reconciliation found papers missing for {failures}. Existing datasets preserved. '
                         'See institutes/<slug>.validation_failed.json; review before rebuilding.')
    for name, (dataset, report) in built.items():
        write_json(dataset_path(name), dataset)
        write_json(INSTITUTES / f"{dataset['metadata']['slug']}.validation.json", report)
    previous = json.loads(INDEX.read_text(encoding='utf-8'))['institutes'] if INDEX.exists() and only else []
    entries = {e['name']: e for e in previous if e['name'] in rosters}
    entries.update({name: index_entry(dataset, report) for name, (dataset, report) in built.items()})
    some = next(iter(built.values()))[0]['metadata']
    write_index(entries, rosters, {k: some[k] for k in ('reference_revision', 'core_edition', 'available_sources',
                                                         'available_areas', 'area_names', 'optional_venues')})
    for name, (dataset, report) in built.items():
        print(f"{name}: {len(dataset['faculty'])} faculty, {len(dataset['publications'])} publications; "
              f"reference cells missing {report['missing_cells']}, extra {report['extra_cells']}", flush=True)


def main(default_only=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--institute', action='append', help='Build only this institute (repeatable); default all')
    parser.add_argument('--offline', action='store_true', help='Use cached profiles only')
    parser.add_argument('--refresh', action='store_true', help='Refresh every DBLP bibliography')
    parser.add_argument('--reference-only', action='store_true', help='Explicitly use published CSRankings counts; CORE/IEEE/ACM unavailable')
    parser.add_argument('--backend', choices=['sparql', 'xml'], default='sparql')
    parser.add_argument('--allow-reference-differences', action='store_true',
                        help='Publish even when the reference counts papers this build does not')
    args = parser.parse_args()
    if args.offline and args.refresh:
        parser.error('--offline and --refresh cannot be combined')
    only = args.institute or default_only
    if args.reference_only:
        rosters = load_rosters()
        for name in only or rosters:
            build_reference(rosters[name])
    else:
        build(only, args.offline, args.refresh, args.backend, args.allow_reference_differences)


if __name__ == '__main__':
    main()
