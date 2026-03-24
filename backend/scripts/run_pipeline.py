import sys
import os
sys.path.append(os.path.dirname(__file__))

import json
import pandas as pd

from fetch_dblp import fetch_papers
from filter_publications import is_top_venue
from compute_scores import compute_score

# Load faculty CSV
faculty = pd.read_csv("../data/raw/iiitd_faculty.csv")

results = []

for _, row in faculty.iterrows():
    name = row["name"]
    dblp_url = row["dblp_url"]

    print(f"Processing {name}...")

    try:
        # Fetch papers
        papers = fetch_papers(dblp_url)

        if not papers:
            print(f"⚠️ No data for {name}")
            results.append({
                "name": name,
                "papers": 0,
                "score": 0
            })
            continue

        # TEMP: use all papers
        filtered = papers
        score = compute_score(filtered)

        results.append({
            "name": name,
            "papers": len(filtered),
            "score": score
        })

    except Exception as e:
        print(f"❌ Error processing {name}: {e}")

# Sort by score
results.sort(key=lambda x: x["score"], reverse=True)

# Save output
os.makedirs("../data/processed", exist_ok=True)

with open("../data/processed/iiitd_rankings.json", "w") as f:
    json.dump(results, f, indent=2)

print("✅ PIPELINE COMPLETE!")