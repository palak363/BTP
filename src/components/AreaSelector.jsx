import { useEffect, useRef } from "react";

const groups = [
  { name: "AI", tone: "ai", areas: ["Artificial intelligence", "Computer vision", "Machine learning & data mining", "Natural language processing", "The Web & information retrieval"] },
  { name: "Systems", tone: "systems", areas: ["Computer architecture", "Computer networks", "Computer security", "Databases", "Design automation", "Embedded & real-time systems", "High-performance computing", "Mobile computing", "Measurement & performance analysis", "Operating systems", "Programming languages", "Software engineering"] },
  { name: "Theory", tone: "theory", areas: ["Algorithms & complexity", "Cryptography", "Logic & verification"] },
  { name: "Interdisciplinary Areas", tone: "interdisciplinary", areas: ["Computational biology", "Computer graphics", "Computer science education", "Economics & computation", "Human-computer interaction", "Robotics", "Visualization"] },
];

function Selection({ label, values, selected, onChange }) {
  const ref = useRef(null);
  const count = values.filter(value => selected.includes(value)).length;
  useEffect(() => { ref.current.indeterminate = count > 0 && count < values.length; }, [count, values.length]);
  return <label className="area-selection"><input ref={ref} type="checkbox" checked={values.length > 0 && count === values.length} onChange={event => onChange(event.target.checked ? [...new Set([...selected, ...values])] : selected.filter(value => !values.includes(value)))} /><span>{label}</span></label>;
}

export default function AreaSelector({ available, selected, onChange, areaNames }) {
  const extra = available.filter(area => !groups.some(group => group.areas.includes(area)));
  const sections = [...groups, ...(extra.length ? [{ name: "Additional areas", tone: "other", areas: extra }] : [])];
  return <details className="panel area-selector" aria-label="Research area selection">
    <summary className="area-selector-summary"><span><strong>Research areas</strong><span className="area-summary-count">{selected.length === available.length ? "All areas" : selected.length ? `${selected.length} of ${available.length} selected` : "No areas selected"}</span></span><span className="area-edit-label">Edit areas <span aria-hidden="true">⌄</span></span></summary>
    <div className="area-selector-content">
    <div className="panel-heading"><p>Select domains or individual areas.</p><Selection label="All Areas" values={available} selected={selected} onChange={onChange} /></div>
    <div className="area-groups">{sections.map(group => {
      const areas = group.areas.filter(area => available.includes(area));
      if (!areas.length) return null;
      return <fieldset key={group.name} className={`area-group ${group.tone}`}><legend><Selection label={group.name} values={areas} selected={selected} onChange={onChange} /></legend>
        {areas.map(area => <div className="area-row" key={area}><details><summary>{area}</summary><p>{Object.entries(areaNames).filter(([, name]) => name === area).map(([venue]) => venue.toUpperCase()).join(" · ") || "CORE venues outside the CSRankings area map."}</p></details><input type="checkbox" aria-label={area} checked={selected.includes(area)} onChange={event => onChange(event.target.checked ? [...selected, area] : selected.filter(value => value !== area))} /></div>)}
      </fieldset>;
    })}</div><p className="area-selection-note">{selected.length} of {available.length} areas selected{!selected.length ? " · Select an area to show publications." : ""}</p>
    </div>
  </details>;
}
