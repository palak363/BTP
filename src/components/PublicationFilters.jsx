import { useState } from "react";
import { sourceNames } from "../publications";

export default function PublicationFilters({ venues, filters, onChange }) {
  const [start, setStart] = useState("2016");
  const [end, setEnd] = useState("2026");
  const valid = /^\d{4}$/.test(start) && /^\d{4}$/.test(end) && +start >= 1970 && +end <= 2269 && +start <= +end;
  const toggle = (field, value) => onChange({ ...filters, [field]: filters[field].includes(value) ? filters[field].filter(item => item !== value) : [...filters[field], value] });
  return <section className="panel publication-filters" aria-label="Publication filters">
    <div className="panel-heading"><div><h2>Filter publications</h2><p>Select multiple sources, conferences, or inclusive year periods. Empty selections include everything.</p></div><button type="button" onClick={() => onChange({ venues: [], sources: [], periods: [] })}>Reset filters</button></div>
    <div className="publication-filter-body">
      <fieldset><legend>Conference sources</legend><div className="source-toggles">{Object.entries(sourceNames).map(([value, label]) => <button type="button" key={value} aria-pressed={filters.sources.includes(value)} className={filters.sources.includes(value) ? "selected" : ""} onClick={() => toggle("sources", value)}>{label}</button>)}</div></fieldset>
      <details className="venue-picker"><summary>Conferences / publication venues · {filters.venues.length ? `${filters.venues.length} selected` : "All venues"}</summary><div className="venue-options">{venues.map(venue => <label key={venue}><input type="checkbox" checked={filters.venues.includes(venue)} onChange={() => toggle("venues", venue)} /><span>{venue}</span></label>)}</div></details>
      <fieldset><legend>Year periods</legend><form className="year-form" onSubmit={event => { event.preventDefault(); if (valid && !filters.periods.some(p => p.start === +start && p.end === +end)) onChange({ ...filters, periods: [...filters.periods, { start: +start, end: +end }] }); }}><label>From<input aria-label="Period start year" inputMode="numeric" value={start} onChange={event => setStart(event.target.value)} aria-invalid={!valid} /></label><label>To<input aria-label="Period end year" inputMode="numeric" value={end} onChange={event => setEnd(event.target.value)} aria-invalid={!valid} /></label><button disabled={!valid}>Add period</button></form>{!valid && <p role="alert">Enter years from 1970 to 2269, with the start no later than the end.</p>}
        <div className="period-chips">{filters.periods.length ? filters.periods.map((period, index) => <button type="button" key={`${period.start}-${period.end}`} aria-label={`Remove period ${period.start} to ${period.end}`} onClick={() => onChange({ ...filters, periods: filters.periods.filter((_, i) => i !== index) })}>{period.start}–{period.end} ×</button>) : <span className="quiet">All loaded years</span>}</div>
      </fieldset>
    </div>
  </section>;
}
