"""Import validated publication data into the API database atomically."""
import argparse
import json
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from repository import import_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=Path(__file__).parent / 'data/processed/iiitd_dataset.json')
    args = parser.parse_args()
    try:
        dataset = json.loads(args.dataset.read_text(encoding='utf-8-sig'))
        identifier = import_dataset(dataset)
    except SQLAlchemyError:
        raise SystemExit('Database import failed. Check DATABASE_URL and permissions. The active dataset was not replaced.') from None
    print(f"Imported {len(dataset['faculty'])} faculty and {len(dataset['publications'])} papers. Active dataset: {identifier[:12]}.")


if __name__ == '__main__':
    main()
