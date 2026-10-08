import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";
import useProfessor from "../hooks/useProfessor";
import VenuePie from "./VenuePie";

function Preview({ name }) {
  const { data, loading } = useProfessor(name);
  return <><strong>{name}</strong><p className="quiet">Publication venues · All loaded years and sources</p>
    {data ? <VenuePie papers={data.publications} compact /> : <p>{loading ? "Loading publications…" : "No loaded publication records."}</p>}</>;
}
export default function ProfessorLink({ name }) {
  const [position, setPosition] = useState(null);
  const timer = useRef(null);
  const id = useId();
  const cancel = () => clearTimeout(timer.current);
  const hide = () => { cancel(); timer.current = setTimeout(() => setPosition(null), 150); };
  const show = event => {
    cancel();
    const rect = event.currentTarget.getBoundingClientRect();
    const width = Math.min(320, rect.left - 24);
    // Narrow screens use the profile chart; never cover the name with a preview.
    if (width < 150) return;
    setPosition({ width, left: 12, top: Math.max(12, Math.min(rect.top, window.innerHeight - 440)) });
  };
  useEffect(() => {
    if (!position) return;
    const close = () => setPosition(null);
    const key = event => { if (event.key === "Escape") close(); };
    window.addEventListener("resize", close);
    window.addEventListener("keydown", key);
    const scroll = event => { if (!event.target.closest?.('.professor-preview')) close(); };
    window.addEventListener("scroll", scroll, true);
    return () => { window.removeEventListener("resize", close); window.removeEventListener("keydown", key); window.removeEventListener("scroll", scroll, true); };
  }, [position]);
  useEffect(() => () => clearTimeout(timer.current), []);
  return <><Link className="professor-link" to={`/professor/${encodeURIComponent(name)}`} onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide} onClick={() => setPosition(null)} aria-describedby={position ? id : undefined}>{name}</Link>
    {position && createPortal(<div id={id} role="tooltip" className="professor-preview" style={position} onMouseEnter={cancel} onMouseLeave={hide}><Preview key={name} name={name} /></div>, document.body)}</>;
}
