# # import pandas as pd
# # import urllib.parse

# # df = pd.read_csv("../data/raw/iiitd_raw.csv")

# # def make_dblp_search(name):
# #     query = urllib.parse.quote(name)
# #     return f"https://dblp.org/search?q={query}"

# # df["dblp_url"] = df["name"].apply(make_dblp_search)
# # df["area"] = "Unknown"

# # df = df[["name", "dblp_url", "area"]]

# # df.to_csv("../data/raw/iiitd_faculty.csv", index=False)

# # print("✅ Converted to pipeline format")

# import pandas as pd
# import requests
# import time

# df = pd.read_csv("../data/raw/iiitd_raw.csv")

# def get_dblp_profile(name):
#     url = f"https://dblp.org/search/author/api?q={name}&format=json"
    
#     try:
#         res = requests.get(url).json()
#         hits = res["result"]["hits"]["hit"]

#         if isinstance(hits, list) and len(hits) > 0:
#             return hits[0]["info"]["url"]
#         elif isinstance(hits, dict):
#             return hits["info"]["url"]

#     except:
#         return None

#     return None


# dblp_urls = []

# for name in df["name"]:
#     print(f"Fetching DBLP for {name}...")
#     dblp_urls.append(get_dblp_profile(name))
#     time.sleep(0.5)   # avoid rate limit

# df["dblp_url"] = dblp_urls
# df["area"] = "Unknown"
# df = df[df["dblp_url"].notnull()]
# df["dblp_url"] = df["dblp_url"].apply(lambda x: x + ".html" if pd.notnull(x) else x)
# df = df.drop_duplicates(subset=["dblp_url"])

# df = df[["name", "dblp_url", "area"]]

# df.to_csv("../data/raw/iiitd_faculty.csv", index=False)

# print("✅ DBLP mapping complete")

import pandas as pd
import requests
import time

df = pd.read_csv("../data/raw/iiitd_raw.csv")

def get_dblp_profile(name):
    url = f"https://dblp.org/search/author/api?q={name}&format=json"
    
    try:
        res = requests.get(url).json()
        hits = res["result"]["hits"]["hit"]

        if isinstance(hits, list) and len(hits) > 0:
            return hits[0]["info"]["url"]
        elif isinstance(hits, dict):
            return hits["info"]["url"]

    except:
        return None

    return None

dblp_urls = []

for name in df["name"]:
    print(f"Fetching DBLP for {name}...")
    dblp_urls.append(get_dblp_profile(name))
    time.sleep(0.5)

df["dblp_url"] = dblp_urls

# ✅ CLEANING STEPS
df = df[df["dblp_url"].notnull()]
df["dblp_url"] = df["dblp_url"].apply(lambda x: x + ".html")
df = df.drop_duplicates(subset=["dblp_url"])

df["area"] = "Unknown"

df = df[["name", "dblp_url", "area"]]

df.to_csv("../data/raw/iiitd_faculty.csv", index=False)

print("✅ CLEAN DATA READY")