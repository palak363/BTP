# India CS Research

A React + Flask research explorer, currently built for the 33 IIIT Delhi faculty in a pinned CSRankings roster. National rankings and institute comparisons remain explicitly labelled placeholders.

## Run the app

From this directory:

```powershell
npm.cmd install
npm.cmd run dev
```

Open http://localhost:5173. The UI includes the generated DBLP snapshot, so year, area, faculty search, sorting, and source selections also work without Flask. The interface labels this as a bundled snapshot.

To use the API, in a second terminal:

```powershell
python -m pip install -r backend/requirements.txt
python backend/api/app.py
```

Vite proxies /api to http://127.0.0.1:5000. A deployed frontend can set VITE_API_BASE_URL to the API origin. PostgreSQL is no longer required to run the pilot: the API reads the same publication artifact that generates the rankings and domain summaries. Existing database contents are not changed.

## Rebuild the IIITD dataset

```powershell
# Download checksum-verified reference inputs and resolve exact faculty identities.
python backend/scripts/prepare_sources.py

# Fetch complete DBLP bibliographies, classify venues, reconcile and publish outputs.
python backend/scripts/build_iiitd_dataset.py

# Repeat reproducibly from the downloaded bibliographies.
python backend/scripts/build_iiitd_dataset.py --offline

# Explicitly refresh every bibliography.
python backend/scripts/build_iiitd_dataset.py --refresh
```

Paths are relative to the scripts, so these commands do not depend on your working directory. run_pipeline.py and extract_domains.py call the same builder. convert_to_pipeline.py calls the exact-identity resolver.

The default fetcher uses DBLP's public SPARQL service. The XML endpoint currently returns an HTML challenge in this environment; it remains available via --backend xml. Neither fetcher silently turns failures into zero counts. Raw responses are cached in backend/data/cache; caches and downloaded upstream reference files are excluded from git.

prepare_sources.py --download-only downloads reference files without resolving identities. Add --core to import a fresh official CORE2023 export. The checked-in core_venues.json already contains that catalogue; its edition is explicit because ranks can change between editions.

--reference-only is an explicit diagnostic fallback that builds from published CSRankings aggregate counts. It cannot supply CORE or unique-paper totals and labels that limitation in both data and UI. It is not the normal DBLP pipeline.

## What was corrected

- The original roster had only 26 profiles; aliases are now canonicalized into 33 faculty, including zero-count researchers.
- Anubha Gupta and Ravi Anand were mapped to other people. The resolver now requires one exact DBLP identity; each fetched bibliography verifies that identity again.
- XML Element truthiness discarded booktitles. The parser now reads booktitle and journal explicitly and retains nested titles, DBLP keys, all authors, pages, volumes and issues.
- Conference event years are retained separately from publication years in the SPARQL graph. Conference filtering uses the event year when present. This fixes a NAACL 2024 paper incorrectly carrying publication year 2014 and an IROS 2023 paper with no publication year.
- The old ranking script counted every publication and applied an arbitrary recency bonus. The new pipeline applies venue and paper eligibility and awards each faculty author 1/N credit, where N includes every coauthor.
- Rankings, domains and institute totals now come from one artifact. Institute totals deduplicate DBLP keys and do not aggregate truncated faculty top-five lists.
- Default selections exclude optional CSRankings venues. The UI has an explicit option to include them.

## Counting and comparison

The inclusive default window is **2016–2026**. For this window and the default CSRankings venues, the current independent DBLP build gives **24 papers for Md. Shad Akhtar** and **18 for Pushpendra Singh 0001**. Pushpendra has **19 if the start year includes 2015**: his CHI 2015 paper is outside the 2016–2026 window.

Faculty paper count counts a shared paper for each faculty author. Unique institute papers counts each DBLP key once. Adjusted credit sums 1/N per faculty author. It is not the geometric-mean institute ranking. The API supplies an average_count for CSRankings-only selections, grouping adjusted credit by the selected research areas, including areas with zero papers.

CSRankings rules, aliases, roster and comparison data are pinned to revision b2e76bcec658a429c26011530767528839d524df. The reference manifest records SHA-256 checksums. Each build compares every faculty/venue/year cell against that reference, including optional venues and historical years; adjusted credits allow only the reference CSV's five-significant-digit rounding.

The normal build refuses to replace the dataset if reconciliation fails. It writes iiitd_validation_failed.json for investigation. --allow-reference-differences is an explicit escape hatch for reviewed differences after source updates. Raw paper counts are never overwritten to force agreement.

## CORE extension

Select CSRankings, CORE A*, CORE A, or their union. Overlapping papers count once. CORE uses the **CORE2023** catalogue, exact case-insensitive acronym matching, explicit DBLP aliases, and identified exceptions for ambiguous acronyms such as software-engineering FSE. Ambiguous unmapped acronyms are excluded.

CORE ranks venues, not individual paper tracks. This implementation includes conference papers with at least six pages, or papers that already pass the venue-specific CSRankings full-paper rules. It excludes workshop variants and does not classify arbitrary journal articles as conference papers. Shorter legitimate conference papers can therefore be excluded under this stated policy. Additional CORE venues outside the CSRankings area map appear under Other CORE areas.

## Generated artifacts and API

- backend/data/processed/iiitd_dataset.json: publication identifiers, metadata, faculty memberships, source memberships, and provenance.
- iiitd_domains.json: default filtered institute summary.
- iiitd_rankings.json: the same default faculty summary.
- iiitd_validation.json: independent faculty/venue/year reconciliation.

Endpoints:

```text
GET /iiitd
GET /iiitd/domains
GET /iiitd/validation
```

Both summary endpoints accept start_year, end_year, sources (comma-separated csrankings,core-a-star,core-a), repeated area parameters, and include_optional=true|false. Invalid ranges and unavailable selections return HTTP 400; an absent dataset returns HTTP 503.

The optional legacy backend/load_data.py exports the default faculty summary to PostgreSQL. Existing databases with an integer score column must migrate it to DOUBLE PRECISION first; the exporter refuses to truncate fractional credits. This database export is not used by the API.

## Verification

```powershell
python -m unittest discover -s backend/tests -v
npm.cmd run lint
npm.cmd run build
```

Browser checks cover desktop/mobile layouts, faculty search, optional venue filtering, and placeholder routes.

## Data sources

- DBLP public SPARQL service: https://sparql.dblp.org/sparql
- DBLP API documentation: https://blog.dblp.org/2024/09/09/introducing-our-public-sparql-query-service/
- CSRankings rules and reference data: https://github.com/emeryberger/CSrankings/tree/b2e76bcec658a429c26011530767528839d524df
- CORE2023 conference catalogue: https://portal.core.edu.au/conf-ranks/?source=CORE2023

Upstream sources retain their own licenses. Downloaded CSRankings code and full reference data are kept outside tracked project files. The product UI does not link out to CSRankings.
