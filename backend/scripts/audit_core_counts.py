"""Audit CORE catalogue coverage and every faculty's cached/loaded/API paper counts."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from core_venues import classify_core, resolve_core_entry
from fetch_sparql import fetch_papers
from venue_rules import classify_csr, load_rules, OPTIONAL_VENUES

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / 'data/processed'


def audit(start=2016, end=2026, baseline=None):
    dataset = json.loads((OUTPUT / 'iiitd_dataset.json').read_text(encoding='utf-8'))
    catalogue = json.loads((BASE / 'data/raw/core_venues.json').read_text(encoding='utf-8'))
    rules = load_rules()
    raw = {}
    expected = defaultdict(set)
    expected_all_years = defaultdict(set)
    membership_differences = []
    loaded = {p['key']: p for p in dataset['publications']}
    for faculty in dataset['faculty']:
        name = faculty['name']
        for paper in fetch_papers(faculty['dblp_url'], name, offline=True):
            raw[paper['key']] = paper
            csr = classify_csr(paper, rules)
            core = classify_core(paper, csr, catalogue, rules)
            if core:
                expected_all_years[name].add(paper['key'])
                actual = loaded.get(paper['key'], {})
                if name not in actual.get('faculty', []) or core not in actual.get('memberships', []):
                    membership_differences.append({'name': name, 'key': paper['key'], 'expected': core})
            for membership in [m for m in (csr, core) if m]:
                source = membership.get('source', 'csrankings')
                if source == 'csrankings' and membership['area'] in OPTIONAL_VENUES:
                    continue
                if start <= membership['year'] <= end:
                    expected[name, source].add(paper['key'])

    sys.path.insert(0, str(BASE))
    from api.app import app
    client = app.test_client()
    selections = {'csrankings': ['csrankings'], 'core_a_star': ['core-a-star'], 'core_a': ['core-a'],
                  'core_union': ['core-a-star', 'core-a'], 'all_sources_union': ['csrankings', 'core-a-star', 'core-a']}
    api_rows = {}
    for label, sources in selections.items():
        response = client.get(f'/iiitd/domains?start_year={start}&end_year={end}&sources={",".join(sources)}')
        if response.status_code != 200:
            raise ValueError(f'API failed: {label}')
        api_rows[label] = response.get_json()
    rows, differences = [], []
    old = json.loads(Path(baseline).read_text(encoding='utf-8')) if baseline else None
    for faculty in dataset['faculty']:
        name = faculty['name']
        row = {'name': name}
        for label, sources in selections.items():
            keys = set().union(*(expected[name, source] for source in sources))
            actual = {p['key'] for p in dataset['publications'] if name in p['faculty'] and any(
                m['source'] in sources and start <= m['year'] <= end and
                (m['source'] != 'csrankings' or m['area'] not in OPTIONAL_VENUES) for m in p['memberships'])}
            api_count = next(f['papers'] for f in api_rows[label]['faculty_rankings'] if f['name'] == name)
            row[label] = len(keys)
            if keys != actual or api_count != len(keys):
                differences.append({'name': name, 'selection': label, 'cached': len(keys), 'loaded': len(actual), 'api': api_count})
        if old:
            before = {p['key'] for p in old['publications'] if name in p['faculty'] and any(
                m['source'].startswith('core-') and start <= m['year'] <= end for m in p['memberships'])}
            row.update(core_union_before=len(before), core_union_change=row['core_union'] - len(before))
        rows.append(row)

    reasons = Counter()
    unresolved = defaultdict(set)
    for paper in raw.values():
        csr = classify_csr(paper, rules)
        entry = resolve_core_entry(paper, csr, catalogue)
        if classify_core(paper, csr, catalogue, rules):
            reasons['included_core'] += 1
        elif entry and entry['rank'] in {'A*', 'A'}:
            reasons['ranked_venue_excluded_by_paper_policy'] += 1
        elif entry:
            reasons['venue_not_core_a_or_a_star'] += 1
        else:
            reasons['unmapped_venue_or_non_main_track'] += 1
            unresolved[paper['venue']].add(paper['key'])

    coverage = []
    for entry in catalogue['by_id'].values():
        if entry['rank'] not in {'A*', 'A'}:
            continue
        resolved = resolve_core_entry({'venue': entry['title']}, None, catalogue)
        coverage.append({**entry, 'exact_title_resolves': bool(resolved and resolved['id'] == entry['id']),
                         'loaded_unique_papers': len({p['key'] for p in dataset['publications'] if any(
                             m['source'].startswith('core-') and m['venue'] == entry['acronym'] for m in p['memberships'])})})
    changes = []
    if old:
        before = {p['key']: p for p in old['publications']}
        for paper in dataset['publications']:
            added = [m for m in paper['memberships'] if m['source'].startswith('core-')
                     and m not in before.get(paper['key'], {}).get('memberships', [])]
            if added:
                changes.append({'key': paper['key'], 'title': paper['title'], 'year': paper['year'],
                                'faculty': paper['faculty'], 'memberships_added': added})
    report = {'generated_at': datetime.now(timezone.utc).isoformat(), 'edition': catalogue['edition'],
              'scope': 'Cached DBLP bibliographies; not a live DBLP refresh or a ranking-edition upgrade.',
              'year_range': [start, end], 'faculty_count': len(rows), 'raw_unique_papers': len(raw),
              'catalogue_rank_counts': dict(Counter(v['rank'] for v in coverage)),
              'unique_papers_by_selection': {label: payload['total_papers'] for label, payload in api_rows.items()},
              'faculty_counts': rows, 'differences': differences, 'membership_differences': membership_differences,
              'raw_classification': dict(reasons), 'coverage': coverage, 'corrected_memberships': changes,
              'limitations': ['Exact-title coverage does not prove every historical DBLP alias is mapped.',
                              'CORE extension retains the six-page minimum for non-CSRankings conference papers.',
                              'Journal proceedings require CSRankings issue eligibility; Journal Published is not an A/A* rank.',
                              'Unmapped venues and non-main tracks are listed separately for review.'],
              'unmapped_venues': [{'venue': venue, 'papers': len(keys), 'keys': sorted(keys)} for venue, keys in sorted(unresolved.items())]}
    # Detect extra exported CORE memberships, not just missing ones.
    for faculty in dataset['faculty']:
        actual = {p['key'] for p in dataset['publications'] if faculty['name'] in p['faculty']
                  and any(m['source'].startswith('core-') for m in p['memberships'])}
        if actual != expected_all_years[faculty['name']]:
            differences.append({'name': faculty['name'], 'selection': 'all_years_core', 'missing': sorted(expected_all_years[faculty['name']] - actual), 'extra': sorted(actual - expected_all_years[faculty['name']])})
    (OUTPUT / 'iiitd_core_audit.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    with (OUTPUT / 'iiitd_core_faculty_counts.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({key: report[key] for key in ['catalogue_rank_counts', 'raw_unique_papers', 'unique_papers_by_selection', 'raw_classification', 'differences', 'membership_differences']}, indent=2))
    print('Changed faculty:', json.dumps([row for row in rows if row.get('core_union_change')], indent=2))
    if differences or membership_differences or not all(v['exact_title_resolves'] for v in coverage):
        raise ValueError('CORE audit failed; see iiitd_core_audit.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', type=int, default=2016)
    parser.add_argument('--end', type=int, default=2026)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    audit(args.start, args.end, args.baseline)
