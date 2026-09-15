"""One auditable IIITD dataset for rankings, domains and the API."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from fetch_dblp import fetch_papers
from prepare_sources import read_csv, canonical, verify_reference
from venue_rules import REFERENCE, AREA_NAMES, AREA_GROUPS, OPTIONAL_VENUES, classify_csr, load_rules

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / 'data/processed'


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
        raise ValueError('CORE requires a complete DBLP bibliography build.')
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


def build_reference():
    """Explicit published-count baseline when live DBLP is unavailable."""
    verify_reference()
    aliases = {r['alias']: r['name'] for r in read_csv(REFERENCE / 'dblp-aliases.csv')}
    old = {canonical(r['name'], aliases): r['dblp_url']
           for r in read_csv(BASE / 'data/raw/iiitd_faculty.csv')}
    names = sorted({canonical(r['name'], aliases) for r in read_csv(REFERENCE / 'csrankings.csv')
                    if r['affiliation'] == 'IIIT Delhi'})
    counts = []
    for row in read_csv(REFERENCE / 'generated-author-info.csv'):
        name = canonical(row['name'], aliases)
        if row['dept'] == 'IIIT Delhi' and name in names:
            counts.append(dict(name=name, area=row['area'], year=int(row['year']),
                               count=int(float(row['count'])), adjustedcount=float(row['adjustedcount'])))
    dataset = {'metadata': {
        'schema_version': 2, 'institution': 'IIIT Delhi',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'reference_revision': (REFERENCE / 'revision.txt').read_text().strip(),
        'data_source': 'csrankings-published-counts',
        'available_sources': ['csrankings'], 'core_edition': 'CORE2023',
        'available_areas': list(AREA_GROUPS),
        'area_names': AREA_NAMES,
        'optional_venues': sorted(OPTIONAL_VENUES),
        'counting': 'Published CSRankings faculty counts, including optional venues. Raw totals count faculty authorships; unique paper counts are unavailable.',
        'validation': {'mode': 'published-reference', 'independently_recomputed': False},
        'limitations': ['Live DBLP refresh is required for CORE A/A* counts and unique publication totals.']},
        'faculty': [{'name': name, 'dblp_url': old.get(name, '')} for name in names],
        'counts': counts, 'publications': []}
    summary = summarize(dataset, 2016, 2026)
    OUTPUT.mkdir(exist_ok=True)
    for filename, content in {'iiitd_dataset.json': dataset, 'iiitd_domains.json': summary,
                              'iiitd_rankings.json': summary['faculty_rankings'],
                              'iiitd_validation.json': dataset['metadata']['validation']}.items():
        path = OUTPUT / filename
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding='utf-8')
        temporary.replace(path)
    print(f'Published reference baseline: {len(names)} faculty; {len(counts)} area/year cells.')


def compare_reference(dataset, reference):
    aliases = {r['alias']: r['name'] for r in read_csv(reference / 'dblp-aliases.csv')}
    names = {f['name'] for f in dataset['faculty']}
    expected, actual = defaultdict(lambda: [0, 0.0]), defaultdict(lambda: [0, 0.0])
    for row in read_csv(reference / 'generated-author-info.csv'):
        name = canonical(row['name'], aliases)
        if row['dept'] == 'IIIT Delhi' and name in names:
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
    return {'reference_revision': dataset['metadata']['reference_revision'],
            'compared_cells': len(expected.keys() | actual.keys()),
            'matching': not differences, 'differences': differences,
            'note': 'Live DBLP and the pinned CSRankings publication snapshot may differ; no counts are overwritten.'}


def build(offline=False, refresh=False, backend='sparql', allow_reference_differences=False):
    verify_reference()
    rules = load_rules()
    if backend == 'sparql':
        from fetch_sparql import fetch_papers as fetch
    else:
        fetch = fetch_papers
    faculty = read_csv(BASE / 'data/raw/iiitd_faculty.csv')
    aliases = {r['alias']: r['name'] for r in read_csv(REFERENCE / 'dblp-aliases.csv')}
    roster = {canonical(r['name'], aliases) for r in read_csv(REFERENCE / 'csrankings.csv')
              if r['affiliation'] == 'IIIT Delhi'}
    if {f['name'] for f in faculty} != roster:
        raise ValueError('Faculty mapping does not match the reference roster. Run prepare_sources.py.')
    if len({f['dblp_url'].removesuffix('.html') for f in faculty}) != len(faculty):
        raise ValueError('Duplicate DBLP identities in roster')
    publications = {}
    core_path = BASE / 'data/raw/core_venues.json'
    core = json.loads(core_path.read_text(encoding='utf-8-sig')) if core_path.exists() else None
    for member in faculty:
        print(f"Fetching {member['name']}...", flush=True)
        for paper in fetch(member['dblp_url'], member['name'], refresh, offline):
            if paper['key'] in publications:
                previous = publications[paper['key']]
                if any(previous[field] != paper[field] for field in ('authors', 'venue', 'year', 'pages')):
                    raise ValueError(f"Inconsistent cached records for {paper['key']}; refresh bibliographies together.")
                publications[paper['key']]['faculty'].append(member['name'])
                continue
            csr = classify_csr(paper, rules)
            memberships = [dict(csr, source='csrankings')] if csr else []
            if core:
                from core_venues import classify_core
                membership = classify_core(paper, csr, core, rules)
                if membership:
                    memberships.append(membership)
            if memberships:
                publications[paper['key']] = dict(paper, faculty=[member['name']], memberships=memberships)
    result = {
        'metadata': {
            'schema_version': 2, 'institution': 'IIIT Delhi',
            'data_source': 'dblp-' + backend,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'reference_revision': (REFERENCE / 'revision.txt').read_text().strip(),
            'rules_sha256': hashlib.sha256((REFERENCE / 'csrankings.py').read_bytes()).hexdigest(),
            'available_sources': ['csrankings'] + (['core-a-star', 'core-a'] if core else []),
            'core_edition': core['edition'] if core else None,
            'available_areas': list(AREA_GROUPS) + (['Other CORE areas'] if core else []),
            'area_names': AREA_NAMES,
            'optional_venues': sorted(OPTIONAL_VENUES),
            'counting': 'Unique DBLP keys; faculty credit is 1 / all authors; all reference venues, including optional venues.',
        },
        'faculty': faculty, 'publications': sorted(publications.values(), key=lambda p: p['key']),
    }
    report = compare_reference(result, REFERENCE)
    if not report['matching'] and not allow_reference_differences:
        OUTPUT.mkdir(exist_ok=True)
        (OUTPUT / 'iiitd_validation_failed.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        raise ValueError('CSRankings reconciliation failed. Existing dataset preserved. '
                         'See iiitd_validation_failed.json; review source changes before rebuilding.')
    result['metadata']['validation'] = {
        'matching': report['matching'], 'differing_cells': len(report['differences']),
        'compared_cells': report['compared_cells']}
    OUTPUT.mkdir(exist_ok=True)
    # Stage all outputs only after every profile has fetched and parsed successfully.
    summary = summarize(result, 2016, 2026)
    artifacts = {'iiitd_dataset.json': result, 'iiitd_domains.json': summary,
                 'iiitd_rankings.json': summary['faculty_rankings'], 'iiitd_validation.json': report}
    for filename, content in artifacts.items():
        path = OUTPUT / filename
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding='utf-8')
        temporary.replace(path)
    print(f"Built {len(faculty)} faculty, {len(publications)} selected publications. "
          f"Reference differences: {len(report['differences'])}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true', help='Use cached profiles only')
    parser.add_argument('--refresh', action='store_true', help='Refresh every DBLP bibliography')
    parser.add_argument('--reference-only', action='store_true', help='Explicitly use published CSRankings counts; CORE unavailable')
    parser.add_argument('--backend', choices=['sparql', 'xml'], default='sparql')
    parser.add_argument('--allow-reference-differences', action='store_true', help='Publish despite reviewed reference differences')
    args = parser.parse_args()
    if args.offline and args.refresh:
        parser.error('--offline and --refresh cannot be combined')
    if args.reference_only:
        build_reference()
    else:
        build(args.offline, args.refresh, args.backend, args.allow_reference_differences)


if __name__ == '__main__':
    main()
