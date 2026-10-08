import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import useProfessor from "../hooks/useProfessor";
import VenuePie from "../components/VenuePie";
import { filterPapers, sortPapers, sourceNames, venueDistribution, venueName } from "../publications";
import PublicationFilters from "../components/PublicationFilters";

function Profile({ name }) {
  const { data, loading, local } = useProfessor(name);
  const [search, setSearch] = useState("");
  const [order, setOrder] = useState("newest");
  const [filters, setFilters] = useState({ venues: [], sources: [], periods: [] });
  if (!data) return <div className="page"><Link to="/institute/IIIT%20Delhi">← IIIT Delhi</Link><h1>{loading ? "Loading professor…" : "Professor not found"}</h1>{!loading && <p>This professor is not in the loaded IIIT Delhi dataset.</p>}</div>;
  const papers = filterPapers(data.publications, filters);
  const years = papers.map(paper => Number(paper.year)).filter(Boolean);
  const shown = sortPapers(filterPapers(papers, { search }), order);
  return <div className="page professor-page">
    <Link className="back-link" to="/institute/IIIT%20Delhi">← Back to IIIT Delhi</Link>
    <div className="page-heading"><div><p className="eyebrow">FACULTY PUBLICATIONS · {data.institution}</p><h1>{name}</h1><p className="quiet">All loaded years and sources. Institute filters do not limit this bibliography.</p></div></div>
    <PublicationFilters venues={[...new Set(data.publications.map(venueName))].sort((a, b) => a.localeCompare(b))} filters={filters} onChange={setFilters} />
    <div className="stat-grid"><article className="accent-stat"><span>Selected papers</span><strong>{papers.length}</strong><small>Of {data.publications.length} loaded papers</small></article><article><span>Publication venues</span><strong>{venueDistribution(papers).length}</strong></article><article><span>Publication years</span><strong>{years.length ? `${Math.min(...years)}–${Math.max(...years)}` : "—"}</strong></article></div>
    <section className="panel profile-chart"><div className="panel-heading"><h2>Publication venues</h2><span className="quiet">Selected filters · One paper counted once</span></div><VenuePie papers={papers} /></section>
    <section className="panel bibliography"><div className="panel-heading"><div><h2>Research papers</h2><p className="quiet">Showing {shown.length} of {data.publications.length} loaded papers</p></div></div>
      <div className="paper-controls"><label>Search papers<input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search title or venue" /></label><label>Sort papers<select value={order} onChange={event => setOrder(event.target.value)}><option value="newest">Year: newest first</option><option value="oldest">Year: oldest first</option><option value="venue">Venue: A–Z</option></select></label></div>
      {!data.records_available && <p className="empty">Paper records are not available in this snapshot.</p>}
      {shown.map(paper => <article className="paper-card" key={paper.key}><div className="paper-year">{paper.year || "Unknown year"}</div><div><h3>{paper.title || "Untitled paper"}</h3><p className="paper-venue">{venueName(paper)}</p><p className="quiet">{paper.type === "article" ? "Journal article" : "Conference paper"}{paper.pages ? ` · Pages ${paper.pages}` : ""}{paper.volume ? ` · Volume ${paper.volume}` : ""}</p><div className="paper-sources">{[...new Set(paper.memberships.map(item => item.source))].map(source => <span key={source}>{sourceNames[source] || source}</span>)}</div></div></article>)}
      {!shown.length && <p className="empty">{data.publications.length ? "No papers match your filters or search." : "No research papers are loaded for this professor."}</p>}
    </section><p className="quiet profile-source">{local ? "Bundled snapshot" : "Dataset updated"} · {new Date(data.generated_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</p>
  </div>;
}
export default function ProfessorPage() {
  const { name } = useParams();
  return <Profile key={name} name={name} />;
}
