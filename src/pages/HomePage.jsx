import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { availableSources, defaultWindow, facultyDirectory, institutes } from "../data";
import { sourceNames } from "../publications";

const rankingSources = [...availableSources.map(source => [source, sourceNames[source] || source]), ["all", "All sources"]];

export default function HomePage() {
  const [first, setFirst] = useState("");
  const [second, setSecond] = useState("");
  const [source, setSource] = useState("csrankings");
  const [search, setSearch] = useState("");
  const navigate = useNavigate();
  const { hash } = useLocation();
  useEffect(() => { if (hash) document.getElementById(hash.slice(1))?.scrollIntoView(); }, [hash]);
  const ranked = [...institutes].sort((a, b) => b.totals[source].papers - a.totals[source].papers
    || b.totals[source].faculty_papers - a.totals[source].faculty_papers || a.name.localeCompare(b.name))
    .map((institute, index) => ({ ...institute, rank: index + 1 }));
  const shown = ranked.filter(institute => institute.name.toLowerCase().includes(search.trim().toLowerCase()));
  const names = institutes.map(institute => institute.name).sort((a, b) => a.localeCompare(b));
  return <div className="page">
    <section className="hero">
      <div><p className="eyebrow">A closer look at computer science</p>
        <h1>Discover research.<br /><span>Understand its impact.</span></h1>
        <p className="hero-copy">Explore the people, research areas, and publication venues shaping computer science in India.</p>
        <a className="button primary" href="#institutes">Browse institutes ↓</a>
        <p className="quiet hero-footnote">{institutes.length} Indian institutes and {facultyDirectory.length.toLocaleString("en-IN")} faculty from the CSRankings roster. Built on transparent publication counts.</p>
      </div>
      <div className="hero-graphic" aria-hidden="true">
        <div className="orbit orbit-one" /><div className="orbit orbit-two" />
        <div className="graph-center">Research<span>in focus</span></div>
        <span className="graph-node node-one">AI & ML</span><span className="graph-node node-two">Systems</span>
        <span className="graph-node node-three">Theory</span><span className="graph-node node-four">People</span>
      </div>
    </section>
    <div className="section-heading"><div><p className="eyebrow">Explore the landscape</p><h2>One view. Five venue selections.</h2></div><span className="quiet">Publication-based research metrics</span></div>
    <section className="source-cards" aria-label="Ranking sources">
      {[["CSRankings","Available baseline","Explore faculty publications that meet CSRankings venue and paper eligibility rules."],["CORE A*","Bibliography refresh needed","Expand the selection with A* conferences from the CORE2023 catalogue."],["CORE A","Bibliography refresh needed","Include A-ranked conferences, counting overlapping papers only once."],["IEEE","Bibliography refresh needed","Main-conference papers published by IEEE, identified by DOI. Workshops are excluded."],["ACM","Bibliography refresh needed","Main-conference papers published by ACM, identified by DOI. Workshops are excluded."]].map(([title,status,copy],index) =>
        <article className="source-card" key={title}><span className="source-number">0{index+1}</span><span className="badge">{availableSources.includes(["csrankings","core-a-star","core-a","ieee","acm"][index]) ? "Available" : status}</span><h3>{title}</h3><p>{copy}</p></article>)}
    </section>
    <section className="panel" id="institutes">
      <div className="panel-heading institutes-heading"><div><h2>Institute overview</h2><p>Unique papers per institute, {defaultWindow[0]}–{defaultWindow[1]} inclusive. Each DBLP paper is counted once per institute.</p></div>
        <div className="table-controls"><label className="sr-only" htmlFor="institute-search">Search institutes</label><input id="institute-search" type="search" placeholder="Search institutes…" value={search} onChange={event => setSearch(event.target.value)} />
          <label className="sr-only" htmlFor="ranking-source">Count papers from</label><select id="ranking-source" value={source} onChange={event => setSource(event.target.value)}>{rankingSources.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div></div>
      <div className="table-scroll"><table><thead><tr><th scope="col">#</th><th scope="col">Institute</th><th scope="col" className="numeric" title="Faculty with at least one selected paper in these years, as on csrankings.org">Faculty</th><th scope="col" className="numeric">Unique papers</th><th scope="col">Explore</th></tr></thead>
        <tbody>{shown.map(institute => <tr key={institute.slug}>
          <td className="rank">{String(institute.rank).padStart(2, "0")}</td><td className="institute-name">{institute.name}</td>
          <td className="numeric">{institute.totals[source].faculty}</td>
          <td className="numeric">{institute.totals[source].papers.toLocaleString("en-IN")}</td>
          <td><Link to={`/institute/${encodeURIComponent(institute.name)}`}>View profile ↗</Link></td>
        </tr>)}</tbody></table></div>
      {!shown.length && <p className="empty">No institutes match “{search}”.</p>}
      <div className="table-footer">Showing {shown.length} of {institutes.length} institutes · Ranked by unique {rankingSources.find(([value]) => value === source)[1]} papers · Faculty counts only those with at least one of these papers</div>
    </section>
    <section className="panel compare-panel">
      <div><p className="eyebrow">Side by side</p><h2>Compare institutes</h2><p>Paper counts for every source, faculty and authorship credit.</p></div>
      <form className="compare-form" onSubmit={event => { event.preventDefault(); navigate(`/compare/${encodeURIComponent(first)}/${encodeURIComponent(second)}`); }}>
        <label>First institute<select value={first} onChange={event => setFirst(event.target.value)} required><option value="">Choose an institute</option>{names.map(name => <option key={name}>{name}</option>)}</select></label>
        <label>Second institute<select value={second} onChange={event => setSecond(event.target.value)} required><option value="">Choose an institute</option>{names.map(name => <option key={name} disabled={name === first}>{name}</option>)}</select></label>
        <button className="primary" disabled={!first || !second || first === second}>Compare →</button>
      </form>
    </section>
  </div>;
}
