import pandas as pd

# load your CSV (rename your file if needed)
df = pd.read_csv("../data/raw/csrankings.csv")

# filter IIIT Delhi (handle variations)
iiitd = df[df["affiliation"].str.contains("IIIT Delhi", case=False, na=False)]

print(f"Found {len(iiitd)} IIITD faculty")

iiitd.to_csv("../data/raw/iiitd_raw.csv", index=False)