import os
import requests
import pandas as pd
import xml.etree.ElementTree as ET

# Get the path of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Move one folder up to backend/
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# Path to data file
FACULTY_FILE = os.path.join(BASE_DIR, "data", "iiitd_faculty.csv")

faculty = pd.read_csv(FACULTY_FILE)

papers = []

for _, row in faculty.iterrows():

    pid = row["dblp_id"]

    url = f"https://dblp.org/pid/{pid}.xml"

    response = requests.get(url)

    root = ET.fromstring(response.content)

    for record in root:

        title = record.find("title")
        year = record.find("year")
        venue = record.find("journal") or record.find("booktitle")

        if title is None or year is None:
            continue

        papers.append({
            "title": title.text,
            "year": int(year.text),
            "venue": venue.text if venue is not None else "Unknown",
            "author": row["name"],
            "institute": row["institute"]
        })

df = pd.DataFrame(papers)

df.to_csv("../data/raw_papers.csv", index=False)

print("Saved raw papers")