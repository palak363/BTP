import requests
import xml.etree.ElementTree as ET
import time

HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_papers(dblp_url):
    xml_url = dblp_url.replace(".html", ".xml")

    for attempt in range(3):
        try:
            res = requests.get(xml_url, headers=HEADERS, timeout=10)
            res.raise_for_status()

            root = ET.fromstring(res.content)

            papers = []

            for r in root.findall("r"):
                for child in r:
                    if child.tag in ["article", "inproceedings"]:
                        title = child.find("title")
                        year = child.find("year")
                        venue = child.find("booktitle") or child.find("journal")

                        if title is not None and year is not None:
                            venue_text = venue.text.strip() if venue is not None and venue.text else ""

                            # Fallback: parse venue from DBLP key attribute
                            # key="conf/nips/Smith23" → parts[1] = "nips"
                            # key="journals/jmlr/Lee22" → parts[1] = "jmlr"
                            if not venue_text:
                                key = child.get("key", "")
                                parts = key.split("/")
                                if len(parts) >= 2:
                                    venue_text = parts[1]

                            papers.append({
                                "title": title.text,
                                "year": year.text,
                                "venue": venue_text
                            })

            time.sleep(3)
            return papers

        except Exception as e:
            print(f"Retry {attempt+1} for {dblp_url}: {e}")
            time.sleep(3)

    print(f"❌ Failed for {dblp_url}")
    return []