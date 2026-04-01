import sys
import os
sys.path.append(os.path.dirname(__file__))

import json
import pandas as pd
from collections import defaultdict
from fetch_dblp import fetch_papers

def get_paper_venue(paper: dict) -> str:
    """Try all fields DBLP might use for venue."""
    for field in ("venue", "booktitle", "journal", "series", "crossref"):
        val = paper.get(field, "")
        if val:
            return val
    return ""

faculty = pd.read_csv("../data/raw/iiitd_faculty.csv")
for _, row in faculty.iterrows():
    if row["name"]=="Pushpendra Singh":
        dblp_url = row["dblp_url"]
        papers = fetch_papers(dblp_url)
        for paper in papers:
            print(paper)
        break
    