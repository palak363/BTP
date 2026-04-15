import sys
import os
sys.path.append(os.path.dirname(__file__))

import json
import pandas as pd
from collections import defaultdict
from fetch_dblp import fetch_papers

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
    """Strict exact match — only real CSRankings venues counted in top_venues."""
    if not venue:
        return False
    return venue.strip().lower() in VENUE_LOWER


def get_paper_venue(paper):
    for field in ("venue", "booktitle", "journal"):
        val = paper.get(field, "")
        if val:
            return val.strip()
    return ""


faculty = pd.read_csv("../data/raw/iiitd_faculty.csv")

results     = []
all_domains = defaultdict(int)
all_venues  = defaultdict(int)

for _, row in faculty.iterrows():
    name     = row["name"]
    dblp_url = row["dblp_url"]

    print(f"Processing {name}...")

    try:
        papers = fetch_papers(dblp_url)
        if not papers:
            print(f"  No papers.")
            results.append({"name": name, "papers": 0, "domains": {}, "top_domain": "N/A"})
            continue

        domain_counts = defaultdict(int)
        venue_counts  = defaultdict(int)

        cs_paper_count = 0

        for paper in papers:
            venue  = get_paper_venue(paper)
            domain = classify_venue(venue)

            domain_counts[domain] += 1
            all_domains[domain]   += 1

            # Only track venues that are in the CSRankings list
            if venue and is_csrankings_venue(venue):
                venue_counts[venue] += 1
                all_venues[venue]   += 1
                cs_paper_count += 1

        domain_counts.pop("Other", None)  # Remove "Other" from domain distribution
        top_domain = max(domain_counts, key=domain_counts.get)

        results.append({
            "name":       name,            
            "papers":     cs_paper_count,
            "domains":    dict(domain_counts),
            "top_domain": top_domain,
            "top_venues": [{"venue": v, "papers": c} for v, c in sorted(venue_counts.items(), key=lambda x: -x[1])[:5]],
        })

        print(f"  {cs_paper_count} papers | top: {top_domain}")

    except Exception as e:
        print(f"  Error: {e}")

results.sort(key=lambda x: x["papers"], reverse=True)

top_areas  = [{"area": a, "papers": c} for a, c in sorted(all_domains.items(), key=lambda x: -x[1]) if a != "Other"][:10]
top_venues = [{"venue": v, "papers": c} for v, c in sorted(all_venues.items(), key=lambda x: -x[1])][:10]

stats = {
    "total_faculty":       len(results),
    "total_papers":        sum(r["papers"] for r in results),
    "domain_distribution": dict(all_domains),
    "top_areas":           top_areas,   # → InstitutePage topAreas
    "top_venues":          top_venues,  # → InstitutePage topVenues
    "faculty_rankings":    results,
}

os.makedirs("../data/processed", exist_ok=True)
with open("../data/processed/iiitd_domains.json", "w") as f:
    json.dump(stats, f, indent=2)

print("\nDONE!")
print(f"Top areas:  {top_areas}")
print(f"Top venues: {top_venues}")