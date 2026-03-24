import requests
import xml.etree.ElementTree as ET
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_papers(dblp_url):
    xml_url = dblp_url.replace(".html", ".xml")

    for attempt in range(3):
        try:
            res = requests.get(xml_url, headers=HEADERS, timeout=10)
            res.raise_for_status()

            root = ET.fromstring(res.content)

            papers = []

            # 🔥 FIX: correct traversal
            for r in root.findall("r"):
                for child in r:
                    if child.tag in ["article", "inproceedings"]:
                        title = child.find("title")
                        year = child.find("year")
                        venue = child.find("booktitle") or child.find("journal")

                        if title is not None and year is not None:
                            papers.append({
                                "title": title.text,
                                "year": year.text,
                                "venue": venue.text if venue is not None else ""
                            })

            time.sleep(3)
            return papers

        except Exception as e:
            print(f"Retry {attempt+1} for {dblp_url}...")
            time.sleep(3)

    print(f"❌ Failed for {dblp_url}")
    return []