"""Optional legacy PostgreSQL export; the API serves the publication artifact."""
import json
from pathlib import Path
from sqlalchemy import Integer, inspect
from db import SessionLocal, engine
from models import FacultyRanking


def main():
    payload = json.loads((Path(__file__).parent / 'data/processed/iiitd_domains.json').read_text(encoding='utf-8'))
    columns = inspect(engine).get_columns('faculty_rankings')
    if any(c['name'] == 'score' and isinstance(c['type'], Integer) for c in columns):
        raise RuntimeError('Legacy score column is integer. Migrate it to DOUBLE PRECISION before exporting fractional credit.')
    with SessionLocal.begin() as session:
        session.query(FacultyRanking).delete()
        for item in payload['faculty_rankings']:
            session.add(FacultyRanking(
                name=item['name'], papers=item['papers'], score=item['score'],
                domains=item['domains'], top_domain=item['top_domain'], top_venues=item['top_venues']))
    print('Exported faculty summary to PostgreSQL. The API uses iiitd_dataset.json.')


if __name__ == '__main__':
    main()
