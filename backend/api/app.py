import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, jsonify
from flask_cors import CORS
from db import SessionLocal
from models import FacultyRanking

app = Flask(__name__)
CORS(app)

@app.route("/iiitd")
def iiitd():
    session = SessionLocal()
    rows = session.query(FacultyRanking).order_by(FacultyRanking.score.desc()).all()
    session.close()

    return jsonify([
        {
            "name": row.name,
            "papers": row.papers,
            "score": row.score
        }
        for row in rows
    ])

@app.route("/iiitd/domains")
def iiitd_domains():
    session = SessionLocal()
    rows = session.query(FacultyRanking).all()
    session.close()

    # Aggregate domains from all faculty
    domain_counts = {}
    for row in rows:
        if row.domains and isinstance(row.domains, dict):
            for domain, count in row.domains.items():
                if domain == "Other":
                    continue
                domain_counts[domain] = domain_counts.get(domain, 0) + count

    # Sort domains by count and get top 10
    top_areas = sorted(
        [{"area": domain, "papers": count} for domain, count in domain_counts.items()],
        key=lambda x: x["papers"],
        reverse=True
    )[:10]

    # Aggregate venues from all faculty
    venue_counts = {}
    for row in rows:
        if row.top_venues and isinstance(row.top_venues, list):
            for venue_item in row.top_venues:
                if isinstance(venue_item, dict):
                    venue_name = venue_item.get("venue", "")
                    venue_papers = venue_item.get("papers", 0)
                    venue_counts[venue_name] = venue_counts.get(venue_name, 0) + venue_papers

    # Sort venues by count and get top 10
    top_venues = sorted(
        [{"venue": venue, "papers": count} for venue, count in venue_counts.items()],
        key=lambda x: x["papers"],
        reverse=True
    )[:10]

    return jsonify({
        "total_faculty": len(rows),
        "total_papers": sum(r.papers for r in rows),
        "faculty_rankings": [
            {
                "name": row.name,
                "papers": row.papers,
                "score": row.score,
                "domains": row.domains,
                "top_domain": row.top_domain,
                "top_venues": row.top_venues,
            }
            for row in rows
        ],
        "top_areas": top_areas,
        "top_venues": top_venues
    })

if __name__ == "__main__":
    app.run(debug=True)