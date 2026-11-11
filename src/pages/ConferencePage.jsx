import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { facultyDirectory, loadAllInstitutes } from "../data";
import { isTransactionPaper, isVisiblePaper, venueName } from "../publications";
import ProfessorLink from "../components/ProfessorLink";

const conferenceName = value => value.replace(/\s+\(\d+\)$/, "").trim();

function isConferenceOrTransaction(paper) {
  return paper.type !== "article"
    || isTransactionPaper(paper)
    || paper.memberships?.some(({ source }) => source === "acm" || source === "ieee");
}

function buildCatalog(datasets) {
  const venues = new Map();
  const papers = [];
  datasets.forEach(dataset => {
    (dataset.publications || []).forEach(paper => {
      if (!isVisiblePaper(paper) || !isConferenceOrTransaction(paper)) return;
      const memberships = paper.memberships || [];
      const names = new Set(memberships.map(membership => conferenceName(membership.venue || venueName(paper))).filter(Boolean));
      if (isTransactionPaper(paper)) names.add(conferenceName(venueName(paper)));
      names.forEach(name => {
        const entry = venues.get(name) || { name, fields: new Set(), papers: 0 };
        memberships.filter(membership => conferenceName(membership.venue || venueName(paper)) === name)
          .forEach(membership => entry.fields.add(membership.domain || "Other"));
        if (isTransactionPaper(paper) && name === conferenceName(venueName(paper)) && !entry.fields.size) entry.fields.add("ACM/IEEE transactions");
        entry.papers += 1;
        venues.set(name, entry);
      });
      papers.push({ ...paper, institute: dataset.metadata.institution, slug: dataset.metadata.slug });
    });
  });
  return {
    venues: [...venues.values()].map(({ fields, ...venue }) => ({ ...venue, fields: [...fields].sort() }))
      .sort((a, b) => a.name.localeCompare(b.name)),
    papers,
  };
}

export default function ConferencePage() {
  const [catalog, setCatalog] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [field, setField] = useState("");
  const [selected, setSelected] = useState([]);

  useEffect(() => {
    let active = true;
    loadAllInstitutes()
      .then(datasets => { if (active) setCatalog(buildCatalog(datasets)); })
      .catch(loadError => { if (active) setError(loadError.message); });
    return () => { active = false; };
  }, []);

  const fields = useMemo(() => [...new Set((catalog?.venues || []).flatMap(venue => venue.fields))]
    .sort((a, b) => a.localeCompare(b)), [catalog]);
  const visibleVenues = useMemo(() => (catalog?.venues || []).filter(venue =>
    (!field || venue.fields.includes(field)) && venue.name.toLowerCase().includes(search.trim().toLowerCase())), [catalog, field, search]);
  const selectedPapers = useMemo(() => new Map((catalog?.papers || [])
    .filter(paper => paper.memberships?.some(membership => selected.includes(conferenceName(membership.venue || venueName(paper))))
      || (isTransactionPaper(paper) && selected.includes(conferenceName(venueName(paper)))))
    .map(paper => [`${paper.slug}:${paper.key}`, paper])), [catalog, selected]);
  const facultyRows = useMemo(() => {
    const rows = new Map();
    selectedPapers.forEach(paper => paper.faculty.forEach(name => {
      const member = facultyDirectory.find(person => person.name === name && person.slug === paper.slug)
        || facultyDirectory.find(person => person.name === name);
      if (!member) return;
      const key = `${member.slug}:${name}`;
      const row = rows.get(key) || { name, slug: member.slug, papers: new Set() };
      row.papers.add(`${paper.slug}:${paper.key}`);
      rows.set(key, row);
    }));
    return [...rows.values()].map(row => ({ ...row, papers: row.papers.size }))
      .sort((a, b) => b.papers - a.papers || a.name.localeCompare(b.name));
  }, [selectedPapers]);

  const toggleVenue = name => setSelected(current => current.includes(name)
    ? current.filter(value => value !== name) : [...current, name]);

  return <div className="page">
    <Link className="back-link" to="/">← Overview</Link>
    <div className="page-heading"><div><p className="eyebrow">PUBLICATION VENUES</p><h1>Search by conferences</h1>
      <p className="quiet">Select one or more conferences or ACM/IEEE transactions. Results show the union of papers across your selection.</p></div></div>
    <section className="panel conference-selector" aria-label="Conference selection">
      <div className="conference-controls">
        <label>Filter by field<select value={field} onChange={event => setField(event.target.value)}><option value="">All fields</option>{fields.map(value => <option key={value}>{value}</option>)}</select></label>
        <label>Search conferences<input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Search venue name" /></label>
      </div>
      <div className="conference-list" role="group" aria-label="Available conferences">
        {!catalog && !error && <p className="loading" role="status">Loading conference data…</p>}
        {error && <p className="error" role="alert">Conference data could not be loaded: {error}</p>}
        {visibleVenues.map(venue => <label className="conference-option" key={venue.name}>
          <input type="checkbox" checked={selected.includes(venue.name)} onChange={() => toggleVenue(venue.name)} />
          <span><strong>{venue.name}</strong><small>{venue.fields.join(" · ")} · {venue.papers} papers</small></span>
        </label>)}
        {catalog && !visibleVenues.length && <p className="empty">No conferences match this field or search.</p>}
      </div>
      <p className="conference-selection">{selected.length ? `${selected.length} selected: ${selected.join(", ")}` : "Choose one or more venues to see participating faculty."}</p>
    </section>
    <section className="panel">
      <div className="panel-heading"><div><h2>Faculty with selected papers</h2><p>{selected.length ? `${selectedPapers.size} unique papers across the selected venues` : "No venues selected"}</p></div></div>
      {facultyRows.length ? <div className="table-scroll"><table><thead><tr><th>Faculty</th><th>Institute</th><th className="numeric">Papers</th></tr></thead><tbody>
        {facultyRows.map(row => <tr key={`${row.slug}:${row.name}`}><td><ProfessorLink name={row.name} /></td><td>{facultyDirectory.find(person => person.name === row.name && person.slug === row.slug)?.institution || "—"}</td><td className="numeric">{row.papers}</td></tr>)}
      </tbody></table></div> : <p className="empty conference-empty">{selected.length ? "No faculty have papers in the selected venues." : "Select a venue above to begin."}</p>}
    </section>
  </div>;
}
