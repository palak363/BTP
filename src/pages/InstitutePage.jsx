import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { availableAreas, localSummary } from "../data";

const format = value => new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(value);
const sources = [["csrankings", "CSRankings"], ["core-a-star", "CORE A*"], ["core-a", "CORE A"]];

function Distribution({ title, items, field }) {
  const maximum = items[0]?.papers || 1;
  return <section className="panel distribution"><div className="panel-heading"><h2>{title}</h2><span className="quiet">Top 8</span></div>
    {items.length ? items.slice(0, 8).map(item => <div className="bar-row" key={item[field]}>
      <div><span>{item[field]}</span><strong>{format(item.papers)}</strong></div>
      <div className="bar-track"><div style={{ width: `${item.papers / maximum * 100}%` }} /></div>
    </div>) : <p className="empty">No publications in this selection.</p>}
  </section>;
}

function Pilot() {
  const [filters, setFilters] = useState({ start: 2016, end: 2026, area: "", sources: ["csrankings"], optional: false });
  const [draftStart, setDraftStart] = useState("2016");
  const [draftEnd, setDraftEnd] = useState("2026");
  const [state, setState] = useState({ data: null, loading: true, error: "", local: false });
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("score");
  const [retry, setRetry] = useState(0);
  const validYears = /^\d{4}$/.test(draftStart) && /^\d{4}$/.test(draftEnd) && +draftStart >= 1970 && +draftStart <= +draftEnd && +draftEnd <= 2269;
  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    let active = true;
    const params = new URLSearchParams({ start_year: filters.start, end_year: filters.end, sources: filters.sources.join(","), include_optional: filters.optional });
    if (filters.area) params.set("area", filters.area);
    fetch(`${import.meta.env.VITE_API_BASE_URL || "/api"}/iiitd/domains?${params}`, { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error || "The data service is unavailable.");
        return response.json();
      })
      .then(data => { if (active) setState({ data, loading: false, error: "", local: false }); })
      .catch(error => {
        if (!active) return;
        const fallback = localSummary(filters.start, filters.end, filters.area, filters.optional, filters.sources);
        setState({ data: fallback, loading: false, error: fallback ? "" : error.message, local: Boolean(fallback) });
      }).finally(() => clearTimeout(timeout));
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, [filters, retry]);

  const changeFilters = next => {
    setState(previous => ({ ...previous, loading: true }));
    setFilters(next);
  };
  const data = state.data;
  const rows = (data?.faculty_rankings || []).slice().sort((a,b) => b[sort]-a[sort] || a.name.localeCompare(b.name))
    .map((row,index) => ({...row, rank: index+1})).filter(row => row.name.toLowerCase().includes(search.toLowerCase()));
  const published = data?.metadata.data_source === "csrankings-published-counts";
  return <div className="page">
    <Link className="back-link" to="/">← All institutes</Link>
    <div className="institute-heading"><div><p className="eyebrow">Institution profile / New Delhi</p><h1>IIIT Delhi<span className="badge">Pilot institution</span></h1><p>Indraprastha Institute of Information Technology Delhi</p></div><a className="button secondary" href="https://iiitd.ac.in/" target="_blank" rel="noreferrer">Institute website ↗</a></div>
    <section className="panel filter-panel" aria-label="Publication filters">
      <div className="source-toggles">{sources.map(([id,label]) => <button key={id} aria-pressed={filters.sources.includes(id)}
        disabled={!data?.metadata.available_sources.includes(id)}
        title={id !== "csrankings" && !data?.metadata.available_sources.includes(id) ? "Requires a complete DBLP bibliography refresh" : ""}
        className={filters.sources.includes(id) ? "selected" : ""}
        onClick={() => { const next = filters.sources.includes(id) ? filters.sources.filter(s => s !== id) : [...filters.sources,id]; if (next.length) changeFilters({...filters,sources:next}); }}>{label}</button>)}</div>
      <form className="year-form" onSubmit={e => { e.preventDefault(); if (validYears) changeFilters({...filters,start:+draftStart,end:+draftEnd}); }}>
        <label>From<input inputMode="numeric" value={draftStart} onChange={e => setDraftStart(e.target.value)} maxLength={4} aria-invalid={!validYears} /></label>
        <span className="year-dash">—</span><label>Through<input inputMode="numeric" value={draftEnd} onChange={e => setDraftEnd(e.target.value)} maxLength={4} aria-invalid={!validYears} /></label>
        <button className="secondary" disabled={!validYears}>Apply</button>
      </form>
      <label className="area-filter">Research area<select value={filters.area} onChange={e => changeFilters({...filters,area:e.target.value})}><option value="">All research areas</option>{(data?.metadata.available_areas || availableAreas).map(area => <option key={area}>{area}</option>)}</select></label>
    </section>
    <label className="optional-filter"><input type="checkbox" checked={filters.optional} onChange={e => changeFilters({...filters,optional:e.target.checked})} />Include optional CSRankings venues (off by default on CSRankings)</label>
    {!validYears && <p className="error" role="alert">Enter a valid range from 1970 to 2269, with the start year first.</p>}
    {state.loading ? <div className="panel loading" role="status">Loading research data…</div> : state.error ?
      <div className="panel error" role="alert"><h2>Data could not be loaded</h2><p>{state.error}</p><button onClick={() => {setState({...state,loading:true});setRetry(retry+1);}}>Try again</button></div> :
      data && <>
        <div className="data-note"><span className="status-dot" /><span>{state.local ? (published ? "Bundled reference snapshot" : "Bundled DBLP snapshot") : published ? "Published CSRankings snapshot" : "DBLP bibliography dataset"} · {filters.start}–{filters.end} inclusive · {filters.optional ? "Including optional venues" : "Default CSRankings venues"}</span></div>
        {published && <div className="notice">CSRankings counts are available. CORE A/A* and unique-paper totals need a complete DBLP refresh. <a href="#methodology">How counting works ↓</a></div>}
        <section className="stat-grid" aria-label="Research summary">
          <article><span>Faculty in roster</span><strong>{format(data.total_faculty)}</strong><small>Zero-count faculty included</small></article>
          <article><span>Faculty paper count</span><strong>{format(data.faculty_paper_count)}</strong><small>A paper counts for each faculty author</small></article>
          <article className="accent-stat"><span>Adjusted publication count</span><strong>{format(data.adjusted_count)}</strong><small>Credit split across all coauthors</small></article>
          <article><span>Unique institute papers</span><strong>{data.total_papers == null ? "—" : format(data.total_papers)}</strong><small>{data.total_papers == null ? "Requires full publication records" : "Each DBLP paper counted once"}</small></article>
        </section>
        <div className="chart-grid"><Distribution title="Research areas" items={data.top_areas} field="area" /><Distribution title="Publication venues" items={data.top_venues} field="venue" /></div>
        <section className="panel"><div className="panel-heading faculty-heading"><div><h2>Meet the researchers</h2><p>Explore all {data.total_faculty} faculty in the reference roster.</p></div>
          <div className="table-controls"><label className="sr-only" htmlFor="faculty-search">Search faculty</label><input id="faculty-search" placeholder="Search faculty…" type="search" value={search} onChange={e => setSearch(e.target.value)} />
            <label className="sr-only" htmlFor="faculty-sort">Sort faculty</label><select id="faculty-sort" value={sort} onChange={e => setSort(e.target.value)}><option value="score">Adjusted count</option><option value="papers">Paper count</option></select></div></div>
          <div className="table-scroll"><table><thead><tr><th scope="col">#</th><th scope="col">Faculty member</th><th scope="col">Leading research area</th><th scope="col" className="numeric">Papers</th><th scope="col" className="numeric">Adjusted</th></tr></thead>
            <tbody>{rows.map(f => <tr key={f.name}><td className="rank">{String(f.rank).padStart(2,"0")}</td><td className="institute-name">{f.dblp_url ? <a href={f.dblp_url} target="_blank" rel="noreferrer">{f.name} <span className="quiet">↗</span></a> : f.name}</td><td className="quiet">{f.top_domain}</td><td className="numeric">{f.papers}</td><td className="numeric score">{format(f.score)}</td></tr>)}</tbody></table></div>
          {!rows.length && <p className="empty">No faculty match “{search}”.</p>}
          <div className="table-footer">Showing {rows.length} of {data.total_faculty} faculty · Ordered by {sort === "score" ? "adjusted credit" : "paper count"}</div>
        </section>
        <section className="panel methodology" id="methodology"><p className="eyebrow">Transparent by design</p><h2>What do these numbers mean?</h2>
          <div className="method-grid"><div><h3>Count papers consistently</h3><p>CSRankings eligibility includes venue-specific tracks, page thresholds, and journal proceedings. Select the same years and venues when comparing with the original site.</p></div>
            <div><h3>Share credit fairly</h3><p>Each faculty author receives 1/N credit, where N is the number of all authors. Raw faculty totals can count a shared paper more than once.</p></div>
            <div><h3>Know the source</h3><p>{published ? "This view uses published counts, not an independently recomputed DBLP result. CORE is kept separate until a full bibliography is available." : "Papers are keyed by DBLP identifier. Selecting multiple sources takes their union without counting an overlapping paper twice."}</p></div></div>
          <div className="method-footer"><span>Publication-based counting methodology</span><span>Reference {data.metadata.reference_revision.slice(0,12)} · Built {data.metadata.generated_at.slice(0,10)}</span></div>
        </section>
      </>}
  </div>;
}

export default function InstitutePage() {
  const { name } = useParams();
  if (name !== "IIIT Delhi") return <div className="page"><Link className="back-link" to="/">← All institutes</Link><section className="panel placeholder-page"><span className="badge neutral">Placeholder</span><h1>{name}</h1><p>This institute’s research profile is coming later. Explore the IIIT Delhi pilot for available data.</p><Link className="button primary" to="/institute/IIIT%20Delhi">Explore IIIT Delhi ↗</Link></section></div>;
  return <Pilot />;
}
