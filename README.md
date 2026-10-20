# India CS Research

A React + Flask research explorer for every Indian institute in a pinned CSRankings roster. Each institute has its own DBLP-built dataset; the home page ranks institutes and the compare page shows them side by side.

## Run the app

From this directory:

```powershell
npm.cmd install
npm.cmd run dev
```

Open http://localhost:5173. The UI includes the generated DBLP snapshots, so year, area, faculty search, sorting, and source selections also work without Flask. Each institute's snapshot is a separate file that loads only when its page is opened. The interface labels this as a bundled snapshot.

To use the API, in a second terminal:

```powershell
python -m pip install -r backend/requirements.txt
python backend/api/app.py
```

Vite proxies /api to http://127.0.0.1:5000. A deployed frontend can set VITE_API_BASE_URL to the API origin. PostgreSQL is no longer required to run the pilot: the API reads the same publication artifact that generates the rankings and domain summaries. Existing database contents are not changed.

## Rebuild the datasets

```powershell
# Download checksum-verified reference inputs.
python backend/scripts/prepare_sources.py --download-only

# Resolve every Indian institute's CSRankings faculty to exact DBLP identities.
python backend/scripts/institutes.py

# Fetch complete DBLP bibliographies, classify venues, reconcile and publish all institutes.
python backend/scripts/build_institutes.py

# Repeat reproducibly from the downloaded bibliographies, or rebuild selected institutes.
python backend/scripts/build_institutes.py --offline
python backend/scripts/build_institutes.py --offline --institute "IIT Bombay" --institute "IISc Bangalore"

# Explicitly refresh every bibliography.
python backend/scripts/build_institutes.py --refresh
```

Paths are relative to the scripts, so these commands do not depend on your working directory. build_iiitd_dataset.py, run_pipeline.py and extract_domains.py build IIIT Delhi only, with the same options. A first full build fetches about 1,100 bibliographies and takes roughly 20–60 minutes; later builds reuse the cache.

## Institutes and faculty identities

Indian institutes are those with country code `in` in the pinned CSRankings `institutions.csv`. Their faculty come from the pinned `csrankings.csv`, with DBLP aliases applied. institutes.py writes `backend/data/raw/india_faculty.csv` (resolved faculty) and `india_unresolved.csv`.

Each name is resolved to exactly one DBLP person, in order: the DBLP primary name; otherwise a unique DBLP person with that alternate name; otherwise, when several DBLP people share the name, the one whose DBLP homepage equals the CSRankings homepage or whose DBLP affiliations name the institute. Anything still ambiguous or missing is never guessed: it is listed in `india_unresolved.csv` and on the institute page, and contributes no papers. Where CSRankings lists one person under an old and a numbered DBLP name (for example Y. Narahari and Y. Narahari 0001), both rows merge into one faculty member and the reference counts of both names are compared against that person.

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

Each institute's report separates missing cells (the reference counts papers this build does not) from extra cells (this build counts papers the reference does not, typically papers DBLP added after the snapshot). The normal build refuses to replace any dataset if an institute has missing cells and writes `institutes/<slug>.validation_failed.json` for investigation. --allow-reference-differences is an explicit escape hatch for reviewed differences after source updates. Raw paper counts are never overwritten to force agreement.

## CORE extension

Select CSRankings, CORE A*, CORE A, or their union. Overlapping papers count once. CORE uses the **CORE2023** catalogue, exact case-insensitive acronym matching, explicit DBLP aliases, and identified exceptions for ambiguous acronyms such as software-engineering FSE. Ambiguous unmapped acronyms are excluded.

CORE ranks venues, not individual paper tracks. This implementation includes conference papers with at least six pages, or papers that already pass the venue-specific CSRankings full-paper rules. It excludes workshop variants and does not classify arbitrary journal articles as conference papers. Shorter legitimate conference papers can therefore be excluded under this stated policy. Additional CORE venues outside the CSRankings area map appear under Other CORE areas.

The CORE coverage audit checks all 60 A* and 117 A entries in the pinned CORE2023 catalogue and recomputes all 33 IIIT Delhi faculty counts from cached bibliographies. Corrected aliases include ECML/PKDD, APPROX-RANDOM, ICSM, OOPSLA1/2, PoPETs and IEEE S&P. Semantic Web ISWC is resolved using its exact venue name plus the verified DBLP `conf/semweb/` series, keeping Wearable Computers and named satellite tracks separate. Full catalogue titles also resolve exactly. This does not establish complete coverage of every historical DBLP alias or refresh the catalogue to ICORE2026.

Run `python backend/scripts/audit_core_counts.py` after rebuilding. It writes `iiitd_core_audit.json` (catalogue coverage, unmapped venues, exclusions and source/API checks) and `iiitd_core_faculty_counts.csv` (all faculty counts for 2016–2026). Optional `--baseline path/to/previous-dataset.json` records before/after changes. The audit uses cached records and the existing paper eligibility policy; it does not fetch new bibliographies.

## IEEE and ACM extension

The IEEE and ACM sources count main-conference papers of any length whose DBLP DOI has the publisher prefix 10.1109 (IEEE) or 10.1145 (ACM). Journal articles and satellite proceedings are excluded: workshops (including DBLP volumes such as CCGridW filed as `<conf><year>w`), companion and adjunct volumes, extended abstracts, posters, demos, doctoral symposia, and co-located events named `X@Y`. Papers in a CSRankings area keep that area; all others appear under Other IEEE/ACM areas. Overlapping papers in a union count once.

## Generated artifacts and API

- backend/data/processed/institutes.json: every institute with faculty counts and 2016–2026 totals per source, plus the faculty directory.
- backend/data/processed/institutes/<slug>.json: one institute's publication identifiers, metadata, faculty memberships, source memberships, unresolved faculty and provenance.
- backend/data/processed/institutes/<slug>.validation.json: that institute's independent faculty/venue/year reconciliation.

Endpoints (slug is the lower-case institute name with non-alphanumerics as hyphens, e.g. `iit-bhu-varanasi`):

```text
GET /institutes
GET /institutes/<slug>
GET /institutes/<slug>/domains
GET /institutes/<slug>/validation
GET /faculty/<URL-encoded faculty name>
```

The earlier /iiitd, /iiitd/domains, /iiitd/validation and /iiitd/faculty/<name> routes remain as aliases for IIIT Delhi.

Both summary endpoints accept start_year, end_year, sources (comma-separated csrankings,core-a-star,core-a,ieee,acm), repeated area parameters, and include_optional=true|false. Invalid ranges and unavailable selections return HTTP 400; an absent dataset returns HTTP 503.

The faculty endpoint returns every loaded publication record for an exact faculty name, independently of institute filters, and returns HTTP 404 for an unknown name. Professor names open an internal bibliography with title/venue search, year and venue sorting, and a publication-venue pie chart. An all-years venue chart appears in the left margin on hover or keyboard focus in the institute table when there is enough space beside the name. On narrow screens, open the professor page to see the chart. Professor pages support multiple conference sources, individual venues, and inclusive year periods; the chart, totals, and bibliography follow these filters. Selections within each filter are combined as a union, and the different filters intersect. Overlapping periods do not duplicate papers. Reset filters restores all loaded records. Both views deduplicate DBLP keys and fall back to the bundled snapshot when the API is unavailable. The UI displays paper counts only.

The optional legacy backend/load_data.py exports the default faculty summary to PostgreSQL. Existing databases with an integer score column must migrate it to DOUBLE PRECISION first; the exporter refuses to truncate fractional credits. This database export is not used by the API.

## Verification

```powershell
python -m unittest discover -s backend/tests -v
node --test tests/publications.test.mjs
npm.cmd run lint
npm.cmd run build
```

Browser checks cover desktop/mobile layouts, faculty search, optional venue filtering, and placeholder routes. Professor checks cover venue previews, keyboard dismissal, internal navigation, complete paper lists, sorting, search, direct-page reloads, and unknown names.

## Data sources

- DBLP public SPARQL service: https://sparql.dblp.org/sparql
- DBLP API documentation: https://blog.dblp.org/2024/09/09/introducing-our-public-sparql-query-service/
- CSRankings rules and reference data: https://github.com/emeryberger/CSrankings/tree/b2e76bcec658a429c26011530767528839d524df
- CORE2023 conference catalogue: https://portal.core.edu.au/conf-ranks/?source=CORE2023

Upstream sources retain their own licenses. Downloaded CSRankings code and full reference data are kept outside tracked project files. The product UI does not link out to CSRankings.
