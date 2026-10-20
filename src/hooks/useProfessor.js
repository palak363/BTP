import { useEffect, useState } from "react";
import { localProfessor } from "../data";

export default function useProfessor(name) {
  const [state, setState] = useState({ data: null, loading: true, local: true });
  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    let active = true;
    fetch(`${import.meta.env.VITE_API_BASE_URL || "/api"}/faculty/${encodeURIComponent(name)}`, { signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error("The faculty data service is unavailable.");
        const data = await response.json();
        if (data.name !== name || !Array.isArray(data.publications)) throw new Error("Invalid faculty data.");
        if (active) setState({ data, loading: false, local: false });
      })
      .catch(() => localProfessor(name).catch(() => null)
        .then(data => { if (active) setState({ data, loading: false, local: true }); }))
      .finally(() => clearTimeout(timeout));
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, [name]);
  return state;
}
