import { useId, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { facultyDirectory } from "../data";
import { findDblpFaculty, normalizeDblpId } from "../dblp";

export default function DblpSearch() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const id = useId();
  const matches = findDblpFaculty(facultyDirectory, query);
  const open = person => { setQuery(""); navigate(`/professor/${encodeURIComponent(person.name)}`); };
  return <section className="dblp-search" aria-label="Find professor by DBLP ID">
    <form role="search" onSubmit={event => {
      event.preventDefault();
      const exact = matches.find(person => normalizeDblpId(person.dblp_url) === normalizeDblpId(query));
      if (exact || matches.length === 1) open(exact || matches[0]);
    }}>
      <label className="sr-only" htmlFor={id}>Search by DBLP ID or profile URL</label>
      <div className="dblp-search-controls"><input id={id} type="search" value={query} onChange={event => setQuery(event.target.value)} onKeyDown={event => { if (event.key === 'Escape') setQuery(''); }} placeholder="Search DBLP ID" title="Enter a DBLP person ID or profile URL" autoComplete="off" spellCheck="false" /><button type="submit" disabled={!matches.length} aria-label="Find professor" title="Find professor"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></svg></button></div>
    </form>
    {query.trim() && <div className="dblp-search-results"><p role="status">{matches.length ? `${matches.length} matching professor${matches.length === 1 ? '' : 's'}` : 'No matching DBLP ID found.'}</p>
      {matches.length > 0 && <ul>{matches.map(person => <li key={person.name}><Link to={`/professor/${encodeURIComponent(person.name)}`} onClick={() => setQuery("")}><span>{person.name}</span><code>{normalizeDblpId(person.dblp_url)}</code></Link></li>)}</ul>}
    </div>}
  </section>;
}
