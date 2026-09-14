import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { availableSources } from "../data";

const institutes = [
  { name: "IIT Delhi", location: "New Delhi", papers: 420 },
  { name: "IIT Bombay", location: "Mumbai", papers: 410 },
  { name: "IISc", location: "Bengaluru", papers: 390 },
  { name: "IIIT Delhi", location: "New Delhi", papers: 142 },
];

export default function HomePage() {
  const [first, setFirst] = useState("");
  const [second, setSecond] = useState("");
  const navigate = useNavigate();
  return <div className="page">
    <section className="hero">
      <div><p className="eyebrow">A closer look at computer science</p>
        <h1>Discover research.<br /><span>Understand its impact.</span></h1>
        <p className="hero-copy">Explore the people, research areas, and publication venues shaping computer science in India.</p>
        <Link className="button primary" to="/institute/IIIT%20Delhi">Explore IIIT Delhi ↗</Link>
        <p className="quiet hero-footnote">Starting with IIIT Delhi. Built on transparent publication counts.</p>
      </div>
      <div className="hero-graphic" aria-hidden="true">
        <div className="orbit orbit-one" /><div className="orbit orbit-two" />
        <div className="graph-center">Research<span>in focus</span></div>
        <span className="graph-node node-one">AI & ML</span><span className="graph-node node-two">Systems</span>
        <span className="graph-node node-three">Theory</span><span className="graph-node node-four">People</span>
        <div className="graph-caption">CONNECTED BY CURIOSITY</div>
      </div>
    </section>
    <div className="section-heading"><div><p className="eyebrow">Explore the landscape</p><h2>One view. Three venue selections.</h2></div><span className="quiet">Publication-based research metrics</span></div>
    <section className="source-cards" aria-label="Ranking sources">
      {[["CSRankings","Available baseline","Faculty publication counts and fractional credit from a pinned reference snapshot."],["CORE A*","Bibliography refresh needed","Expand the selection with A* conferences from the CORE2023 catalogue."],["CORE A","Bibliography refresh needed","Include A-ranked conferences, counting overlapping papers only once."]].map(([title,status,copy],index) =>
        <article className="source-card" key={title}><span className="source-number">0{index+1}</span><span className="badge">{availableSources.includes(["csrankings","core-a-star","core-a"][index]) ? "Available in IIITD pilot" : status}</span><h3>{title}</h3><p>{index === 0 ? "Paper eligibility follows CSRankings, with fractional credit across all coauthors." : copy}</p></article>)}
    </section>
    <section className="panel">
      <div className="panel-heading"><div><h2>Institute overview</h2><p>Preview of the national view. These numbers are placeholders.</p></div><span className="badge neutral">Sample data</span></div>
      <div className="table-scroll"><table><thead><tr><th scope="col">Preview rank</th><th scope="col">Institute</th><th scope="col">Location</th><th scope="col" className="numeric">Sample papers</th><th scope="col">Explore</th></tr></thead>
        <tbody>{institutes.map((institute, index) => <tr key={institute.name}>
          <td className="rank">{String(index + 1).padStart(2, "0")}</td><td className="institute-name">{institute.name}</td><td className="quiet">{institute.location}</td><td className="numeric">{institute.papers}</td>
          <td><Link to={`/institute/${encodeURIComponent(institute.name)}`}>{institute.name === "IIIT Delhi" ? "Open pilot ↗" : "Preview ↗"}</Link></td>
        </tr>)}</tbody></table></div>
    </section>
    <section className="panel compare-panel">
      <div><p className="eyebrow">Side by side</p><h2>Compare institutes</h2><p>Explore the comparison layout with sample data.</p></div>
      <form className="compare-form" onSubmit={event => { event.preventDefault(); navigate(`/compare/${encodeURIComponent(first)}/${encodeURIComponent(second)}`); }}>
        <label>First institute<select value={first} onChange={event => setFirst(event.target.value)} required><option value="">Choose an institute</option>{institutes.map(i => <option key={i.name}>{i.name}</option>)}</select></label>
        <label>Second institute<select value={second} onChange={event => setSecond(event.target.value)} required><option value="">Choose an institute</option>{institutes.map(i => <option key={i.name} disabled={i.name === first}>{i.name}</option>)}</select></label>
        <button className="primary" disabled={!first || !second || first === second}>Compare →</button>
      </form>
    </section>
  </div>;
}
