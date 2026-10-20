"""Optional legacy PostgreSQL export; the API serves the publication artifact."""
import json
import sys
from pathlib import Path
from sqlalchemy import Integer, inspect
from db import SessionLocal, engine
from models import FacultyRanking


def main():
    sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
    from build_institutes import summarize
    dataset = json.loads((Path(__file__).parent / 'data/processed/institutes/iiit-delhi.json').read_text(encoding='utf-8'))
    payload = summarize(dataset, 2016, 2026)
    columns = inspect(engine).get_columns('faculty_rankings')
    if any(c['name'] == 'score' and isinstance(c['type'], Integer) for c in columns):
        raise RuntimeError('Legacy score column is integer. Migrate it to DOUBLE PRECISION before exporting fractional credit.')
    with SessionLocal.begin() as session:
        session.query(FacultyRanking).delete()
        for item in payload['faculty_rankings']:
            session.add(FacultyRanking(
                name=item['name'], papers=item['papers'], score=item['score'],
                domains=item['domains'], top_domain=item['top_domain'], top_venues=item['top_venues']))
    print('Exported faculty summary to PostgreSQL. The API uses data/processed/institutes/.')


if __name__ == '__main__':
    main()
