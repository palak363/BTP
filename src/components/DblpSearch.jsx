import { useId, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { facultyDirectory } from "../data";
import { findFaculty, normalizeDblpId } from "../dblp";

export default function DblpSearch() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const id = useId();
  const matches = findFaculty(facultyDirectory, query);
  const open = person => { setQuery(""); navigate(`/professor/${encodeURIComponent(person.name)}`); };
  return <section className="dblp-search" aria-label="Find professor by DBLP ID">
    <form role="search" onSubmit={event => {
      event.preventDefault();
      const normalized = query.trim().toLocaleLowerCase();
      const exact = matches.find(person => normalizeDblpId(person.dblp_url) === normalizeDblpId(query)
        || person.name.toLocaleLowerCase() === normalized);
      if (exact || matches.length === 1) open(exact || matches[0]);
    }}>
      <label className="sr-only" htmlFor={id}>Search professor name, DBLP ID, or profile URL</label>
      <div className="dblp-search-controls"><input id={id} type="search" value={query} onChange={event => setQuery(event.target.value)} onKeyDown={event => { if (event.key === 'Escape') setQuery(''); }} placeholder="Search professor or DBLP ID" title="Enter a professor name, DBLP person ID, or DBLP profile URL" autoComplete="off" spellCheck="false" /><button type="submit" disabled={!matches.length} aria-label="Find professor" title="Find professor"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></svg></button></div>
    </form>
    {query.trim() && <div className="dblp-search-results"><p role="status">{matches.length ? `${matches.length} matching professor${matches.length === 1 ? '' : 's'}` : 'No matching professor or DBLP ID found.'}</p>
      {matches.length > 0 && <ul>{matches.slice(0, 12).map(person => <li key={person.name}><Link to={`/professor/${encodeURIComponent(person.name)}`} onClick={() => setQuery("")}><span>{person.name}<small>{person.institution}</small></span><code>{normalizeDblpId(person.dblp_url)}</code></Link></li>)}{matches.length > 12 && <li className="search-more">Refine your search to view the remaining {matches.length - 12} results.</li>}</ul>}
    </div>}
  </section>;
}
