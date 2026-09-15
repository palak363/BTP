"""Audit every IIITD faculty count from cached DBLP through exported data to CSRankings."""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from fetch_sparql import fetch_papers
from prepare_sources import canonical, read_csv
from venue_rules import load_rules, OPTIONAL_VENUES

BASE = Path(__file__).resolve().parents[1]


def audit(reference, start, end):
    from venue_rules import classify_csr
    dataset = json.loads((BASE / 'data/processed/iiitd_dataset.json').read_text(encoding='utf-8'))
    aliases = {r['alias']: r['name'] for r in read_csv(reference / 'dblp-aliases.csv')}
    expected_names = {canonical(r['name'], aliases) for r in read_csv(reference / 'csrankings.csv')
                      if r['affiliation'] == 'IIIT Delhi'}
    names = {f['name'] for f in dataset['faculty']}
    if expected_names != names:
        raise ValueError(f'Roster mismatch: missing={expected_names - names}, extra={names - expected_names}')
    actual, expected, exported = [defaultdict(lambda: [0, 0.0]) for _ in range(3)]
    rules = load_rules()
    for faculty in dataset['faculty']:
        for paper in fetch_papers(faculty['dblp_url'], faculty['name'], offline=True):
            membership = classify_csr(paper, rules)
            if membership:
                key = (faculty['name'], membership['area'], membership['year'])
                actual[key][0] += 1
                actual[key][1] += 1 / len(paper['authors'])
    for paper in dataset['publications']:
        for membership in paper['memberships']:
            if membership['source'] == 'csrankings':
                for name in paper['faculty']:
                    key = (name, membership['area'], membership['year'])
                    exported[key][0] += 1
                    exported[key][1] += 1 / len(paper['authors'])
    for row in read_csv(reference / 'generated-author-info.csv'):
        if row['dept'] == 'IIIT Delhi':
            name = canonical(row['name'], aliases)
            if name not in names:
                raise ValueError(f'Publication record outside reference roster: {name}')
            key = (name, row['area'], int(row['year']))
            expected[key][0] += int(float(row['count']))
            expected[key][1] += float(row['adjustedcount'])
    keys = set(actual) | set(expected) | set(exported)
    differences = []
    for key in sorted(keys):
        a, e, x = actual[key], expected[key], exported[key]
        tolerance = max(.00006, abs(e[1]) * .00006)
        if a[0] != e[0] or abs(a[1] - e[1]) > tolerance or a[0] != x[0] or abs(a[1] - x[1]) > 1e-9:
            differences.append(dict(name=key[0], venue=key[1], year=key[2],
                                    dblp=a, csrankings=e, exported=x))
    rows = []
    def total(matrix, name, optional):
        cells = [value for (n, area, year), value in matrix.items()
                 if n == name and start <= year <= end and (optional or area not in OPTIONAL_VENUES)]
        return sum(c[0] for c in cells), sum(c[1] for c in cells)
    for name in sorted(names):
        a, e = total(actual, name, False), total(expected, name, False)
        all_a, all_e = total(actual, name, True), total(expected, name, True)
        rows.append(dict(name=name, papers=a[0], csrankings_papers=e[0],
                         adjusted_count=round(a[1], 8), csrankings_adjusted_count=round(e[1], 8),
                         papers_with_optional=all_a[0], csrankings_papers_with_optional=all_e[0],
                         status='MATCH' if not any(d['name'] == name for d in differences) else 'MISMATCH'))
    report = dict(
        checked_at=datetime.now(timezone.utc).isoformat(), start_year=start, end_year=end,
        default_selection='CSRankings default venues; optional venues excluded',
        reference_directory=str(reference), reference_sha256={
            filename: hashlib.sha256((reference / filename).read_bytes()).hexdigest()
            for filename in ['generated-author-info.csv', 'csrankings.csv', 'dblp-aliases.csv']},
        faculty_count=len(rows), checked_faculty_venue_year_cells=len(keys),
        matching=not differences, differences=differences, faculty=rows,
        note='Recomputed from all 33 cached DBLP bibliographies, then checked against exported publications and reference counts. Adjusted reference credit is rounded to five significant digits per cell.')
    out = BASE / 'data/processed'
    (out / 'iiitd_faculty_audit.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    with (out / 'iiitd_faculty_audit.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(report, indent=2))
    if differences:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-dir', type=Path, default=BASE / 'data/reference')
    parser.add_argument('--start-year', type=int, default=2016)
    parser.add_argument('--end-year', type=int, default=2026)
    args = parser.parse_args()
    if args.start_year > args.end_year:
        parser.error('Start year must not exceed end year')
    audit(args.reference_dir.resolve(), args.start_year, args.end_year)
