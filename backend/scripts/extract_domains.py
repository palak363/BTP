import sys
import os
sys.path.append(os.path.dirname(__file__))

import json
import time
import requests
import pandas as pd
from collections import defaultdict
from fetch_dblp import fetch_papers

# OpenAlex free API — no key needed
# Polite pool (faster): add your email as mailto param
# Docs: https://docs.openalex.org
OPENALEX_URL = "https://api.openalex.org/works"
YOUR_EMAIL = "9047arnav@dpsmathuraroad.org"  # replace — gets you into the polite pool (faster responses)


def get_openalex_domains(title: str, year: str = None) -> tuple[str, str]:
    """
    Query OpenAlex by title.
    Returns (domain, field) e.g. ("Physical Sciences", "Computer Science")

    OpenAlex topic hierarchy:
      Domain > Field > Subfield > Topic
      e.g. "Physical Sciences" > "Computer Science" > "Artificial Intelligence" > "Machine Learning"

    We return (field, subfield) since domain is too coarse ("Physical Sciences" for all CS).
    """
    params = {
        "search": title,
        "per_page": 1,
        "select": "title,publication_year,topics,primary_topic",
        "mailto": YOUR_EMAIL,
    }
    if year:
        params["filter"] = f"publication_year:{year}"

    try:
        resp = requests.get(OPENALEX_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        works = data.get("results", [])
        if not works:
            return "Other", "Other"

        work = works[0]

        # primary_topic is the single best match
        # Structure: {"id": ..., "display_name": "Machine Learning",
        #              "subfield": {"display_name": "Artificial Intelligence"},
        #              "field":    {"display_name": "Computer Science"},
        #              "domain":   {"display_name": "Physical Sciences"}}
        primary = work.get("primary_topic")
        if not primary:
            return "Other", "Other"

        field    = primary.get("field", {}).get("display_name", "Other")
        subfield = primary.get("subfield", {}).get("display_name", "Other")

        return field, subfield

    except Exception as e:
        print(f"    [OpenAlex error] {e}")
        return "Other", "Other"


def enrich_papers(papers: list[dict]) -> list[dict]:
    for i, paper in enumerate(papers):
        title = paper.get("title", "").strip()
        year  = paper.get("year", "")

        if not title:
            paper["field"]    = "Other"
            paper["subfield"] = "Other"
            continue

        field, subfield = get_openalex_domains(title, year)
        paper["field"]    = field
        paper["subfield"] = subfield

        time.sleep(0.15)  # ~7 req/sec — well within OpenAlex limits

        if (i + 1) % 20 == 0:
            print(f"      ... {i+1}/{len(papers)} papers enriched")

    return papers


# ── Main ──────────────────────────────────────────────────────────────────────

faculty = pd.read_csv("../data/raw/iiitd_faculty.csv")

results          = []
all_fields       = defaultdict(int)
all_subfields    = defaultdict(int)

for _, row in faculty.iterrows():
    name     = row["name"]
    dblp_url = row["dblp_url"]

    print(f"\nProcessing {name}...")

    try:
        papers = fetch_papers(dblp_url)

        if not papers:
            print(f"  ⚠️  No papers found.")
            results.append({"name": name, "papers": 0, "fields": {}, "subfields": {}})
            continue

        papers = enrich_papers(papers)

        field_counts    = defaultdict(int)
        subfield_counts = defaultdict(int)

        for p in papers:
            field_counts[p["field"]]       += 1
            subfield_counts[p["subfield"]] += 1
            all_fields[p["field"]]         += 1
            all_subfields[p["subfield"]]   += 1

        top_field    = max(field_counts,    key=field_counts.get)
        top_subfield = max(subfield_counts, key=subfield_counts.get)

        results.append({
            "name":        name,
            "papers":      len(papers),
            "fields":      dict(field_counts),
            "subfields":   dict(subfield_counts),
            "top_field":   top_field,
            "top_subfield":top_subfield,
        })

        print(f"  ✅  {len(papers)} papers | top field: {top_field} | top subfield: {top_subfield}")

    except Exception as e:
        print(f"  ❌  Error: {e}")

# ── Save ──────────────────────────────────────────────────────────────────────

results.sort(key=lambda x: x["papers"], reverse=True)

stats = {
    "total_faculty":      len(results),
    "total_papers":       sum(r["papers"] for r in results),
    "field_distribution": dict(all_fields),
    "subfield_distribution": dict(all_subfields),
    "faculty_rankings":   results,
}

os.makedirs("../data/processed", exist_ok=True)

with open("../data/processed/iiitd_domains.json", "w") as f:
    json.dump(stats, f, indent=2)

print("\n✅  DONE!")
print(f"Fields found    : {dict(all_fields)}")
print(f"Subfields found : {dict(all_subfields)}")