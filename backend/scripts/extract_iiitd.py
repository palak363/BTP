"""Extract IIIT Delhi's reference roster with deterministic paths."""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def main():
    source = BASE / 'data/reference/csrankings.csv'
    if not source.exists():
        source = BASE / 'data/raw/csrankings.csv'
    with source.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        rows = [row for row in reader if row['affiliation'] == 'IIIT Delhi']
    destination = BASE / 'data/raw/iiitd_raw.csv'
    with destination.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Extracted {len(rows)} roster entries, including aliases. Run prepare_sources.py to canonicalize.')


if __name__ == '__main__':
    main()
