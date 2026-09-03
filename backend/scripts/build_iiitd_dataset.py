"""
Builds backend/data/processed/iiitd_domains.json — the single dataset
load_data.py loads into PostgreSQL — from the verified faculty roster in
backend/data/raw/iiitd_faculty.csv.

Faculty roster source: https://iiitd.ac.in/people/faculty (current CSE-tagged
faculty, including Emeritus), each manually mapped to a verified DBLP profile.

Usage:
    python build_iiitd_dataset.py            # use cached DBLP data where available
    python build_iiitd_dataset.py --refresh  # re-fetch every faculty member from DBLP
"""

import argparse
import hashlib
import json
import os
from collections import defaultdict
from datetime import datetime

import pandas as pd
from fetch_dblp import fetch_papers

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(SCRIPT_DIR, "..", "data", "raw")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "..", "data", "processed")
CACHE_DIR = os.path.join(RAW_DIR, "dblp_cache")

# Recent papers are weighted higher than older ones when computing `score`,
# so ranking by score rewards sustained/recent output, not just lifetime volume.
RECENT_YEAR_CUTOFF = datetime.now().year - 5
RECENT_WEIGHT = 2
OLDER_WEIGHT = 1

VENUE_TO_CSAREA = {
    "AAAI":             "Artificial intelligence",
    "IJCAI":            "Artificial intelligence",
    "CVPR":             "Computer vision",
    "ICCV":             "Computer vision",
    "ECCV":             "Computer vision",
    "ICML":             "Machine learning",
    "NeurIPS":          "Machine learning",
    "ICLR":             "Machine learning",
    "ACL":              "Natural language processing",
    "EMNLP":            "Natural language processing",
    "NAACL":            "Natural language processing",
    "EACL":             "Natural language processing",
    "WWW":              "The Web & information retrieval",
    "SIGIR":            "The Web & information retrieval",
    "WSDM":             "The Web & information retrieval",
    "CIKM":             "The Web & information retrieval",
    "RecSys":           "The Web & information retrieval",
    "ASPLOS":           "Computer architecture",
    "ISCA":             "Computer architecture",
    "MICRO":            "Computer architecture",
    "HPCA":             "Computer architecture",
    "SIGCOMM":          "Computer networks",
    "NSDI":             "Computer networks",
    "CoNEXT":           "Computer networks",
    "MobiCom":          "Mobile computing",
    "MobiSys":          "Mobile computing",
    "SenSys":           "Mobile computing",
    "IMC":              "Measurement & perf. analysis",
    "CCS":              "Computer security",
    "NDSS":             "Computer security",
    "SIGMOD":           "Databases",
    "VLDB":             "Databases",
    "PVLDB":            "Databases",
    "ICDE":             "Databases",
    "DAC":              "Design automation",
    "ICCAD":            "Design automation",
    "EMSOFT":           "Embedded & real-time systems",
    "RTSS":             "Embedded & real-time systems",
    "SC":               "High-performance computing",
    "IPDPS":            "High-performance computing",
    "PPoPP":            "High-performance computing",
    "OSDI":             "Operating systems",
    "SOSP":             "Operating systems",
    "EuroSys":          "Operating systems",
    "FAST":             "Operating systems",
    "PLDI":             "Programming languages",
    "POPL":             "Programming languages",
    "OOPSLA":           "Programming languages",
    "ICSE":             "Software engineering",
    "FSE":              "Software engineering",
    "ASE":              "Software engineering",
    "ISSTA":            "Software engineering",
    "STOC":             "Algorithms & complexity",
    "FOCS":             "Algorithms & complexity",
    "SODA":             "Algorithms & complexity",
    "CRYPTO":           "Cryptography",
    "EUROCRYPT":        "Cryptography",
    "CAV":              "Logic & verification",
    "LICS":             "Logic & verification",
    "RECOMB":           "Comp. bio & bioinformatics",
    "ISMB":             "Comp. bio & bioinformatics",
    "SIGGRAPH":         "Computer graphics",
    "IEEE VIS":         "Visualization",
    "CHI":              "Human-computer interaction",
    "UIST":             "Human-computer interaction",
    "CSCW":             "Human-computer interaction",
    "UbiComp":          "Human-computer interaction",
    "EC":               "Economics & computation",
    "ICRA":             "Robotics",
    "IROS":             "Robotics",
    "RSS":              "Robotics",
    "HRI":              "Robotics",
}

VENUE_LOWER = {k.lower(): v for k, v in VENUE_TO_CSAREA.items()}


def classify_venue(venue):
    """Used for domain classification — allows substring match."""
    if not venue:
        return "Other"
    v_lower = venue.strip().lower()
    if v_lower in VENUE_LOWER:
        return VENUE_LOWER[v_lower]
    for keyword, area in VENUE_LOWER.items():
        if keyword in v_lower and area != "Economics & computation":
            return area
    return "Other"


def is_csrankings_venue(venue):
    """Strict exact match — only real CSRankings-tracked venues count."""
    if not venue:
        return False
    return venue.strip().lower() in VENUE_LOWER


def get_paper_venue(paper):
    for field in ("venue", "booktitle", "journal"):
        val = paper.get(field, "")
        if val:
            return val.strip()
    return ""


def cache_path(dblp_url):
    key = hashlib.sha1(dblp_url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.json")


def fetch_papers_cached(dblp_url, refresh=False):
    path = cache_path(dblp_url)
    if not refresh and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    papers = fetch_papers(dblp_url)
    if papers:
        # Don't cache empty results — an empty list usually means a transient
        # fetch failure (DBLP timeout/DNS blip), not a real "0 papers" faculty
        # member, and caching it would make the failure permanent on reruns.
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(papers, f)
    return papers


def build(refresh=False):
    faculty = pd.read_csv(os.path.join(RAW_DIR, "iiitd_faculty.csv"))

    results = []
    all_domains = defaultdict(int)
    all_venues = defaultdict(int)
    failures = []

    for _, row in faculty.iterrows():
        name = row["name"]
        dblp_url = row["dblp_url"]
        print(f"Processing {name}...")

        try:
            papers = fetch_papers_cached(dblp_url, refresh=refresh)
        except Exception as e:
            print(f"  Error fetching: {e}")
            failures.append(f"{name}: fetch error ({e})")
            results.append({"name": name, "papers": 0, "score": 0, "domains": {}, "top_domain": "N/A", "top_venues": []})
            continue

        if not papers:
            print("  No papers found.")
            failures.append(f"{name}: no papers returned from DBLP")
            results.append({"name": name, "papers": 0, "score": 0, "domains": {}, "top_domain": "N/A", "top_venues": []})
            continue

        domain_counts = defaultdict(int)
        venue_counts = defaultdict(int)
        cs_paper_count = 0
        score = 0

        for paper in papers:
            venue = get_paper_venue(paper)
            domain = classify_venue(venue)
            domain_counts[domain] += 1
            all_domains[domain] += 1

            if venue and is_csrankings_venue(venue):
                venue_counts[venue] += 1
                all_venues[venue] += 1
                cs_paper_count += 1

                try:
                    year = int(paper.get("year", 0))
                except (TypeError, ValueError):
                    year = 0
                score += RECENT_WEIGHT if year >= RECENT_YEAR_CUTOFF else OLDER_WEIGHT

        domain_counts.pop("Other", None)
        top_domain = max(domain_counts, key=domain_counts.get) if domain_counts else "N/A"

        results.append({
            "name": name,
            "papers": cs_paper_count,
            "score": score,
            "domains": dict(domain_counts),
            "top_domain": top_domain,
            "top_venues": [{"venue": v, "papers": c} for v, c in sorted(venue_counts.items(), key=lambda x: -x[1])[:5]],
        })
        print(f"  {cs_paper_count} papers | score {score} | top: {top_domain}")

    results.sort(key=lambda x: x["papers"], reverse=True)

    top_areas = [{"area": a, "papers": c} for a, c in sorted(all_domains.items(), key=lambda x: -x[1]) if a != "Other"][:10]
    top_venues = [{"venue": v, "papers": c} for v, c in sorted(all_venues.items(), key=lambda x: -x[1])][:10]

    stats = {
        "total_faculty": len(results),
        "total_papers": sum(r["papers"] for r in results),
        "domain_distribution": dict(all_domains),
        "top_areas": top_areas,
        "top_venues": top_venues,
        "faculty_rankings": results,
    }

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    with open(os.path.join(PROCESSED_DIR, "iiitd_domains.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print("\nDONE!")
    print(f"Faculty processed: {stats['total_faculty']}")
    print(f"Total papers (CSRankings-tracked venues only): {stats['total_papers']}")
    if failures:
        print(f"\n{len(failures)} faculty had issues:")
        for f_msg in failures:
            print(f"  - {f_msg}")
    else:
        print("No failures.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="bypass the DBLP cache and re-fetch every faculty member")
    args = parser.parse_args()
    build(refresh=args.refresh)
