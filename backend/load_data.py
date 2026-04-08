import json
from db import SessionLocal
from models import FacultyRanking

if __name__ == "__main__":
    session = SessionLocal()

    with open("data/processed/iiitd_domains.json", "r", encoding="utf-8") as f:
        payload = json.load(f)

    for item in payload.get("faculty_rankings", []):
        row = FacultyRanking(
            name=item["name"],
            papers=item.get("papers", 0),
            score=item.get("score", 0),
            domains=item.get("domains", {}),
            top_domain=item.get("top_domain"),
            top_venues=item.get("top_venues", []),
        )
        session.merge(row)

    session.commit()
    session.close()
    print("✅ Loaded data into PostgreSQL")
