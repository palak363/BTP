import index from "../backend/data/processed/institutes.json";
import { localProfessor as professorFrom, localSummary as summarize } from "./summary";

// Each institute's dataset is a separate static file, fetched only when needed.
const files = import.meta.glob(["../backend/data/processed/institutes/*.json", "!**/*.validation*.json"], { query: "?url", import: "default" });
const loaded = new Map();

export const institutes = index.institutes;
export const availableAreas = index.metadata.available_areas;
export const areaNames = index.metadata.area_names;
export const availableSources = index.metadata.available_sources;
export const defaultWindow = index.metadata.default_window;
export const facultyDirectory = index.faculty;
export const instituteByName = name => institutes.find(institute => institute.name === name);
export const facultyMember = name => facultyDirectory.find(person => person.name === name);

export function loadInstitute(slug) {
  if (!loaded.has(slug)) {
    const file = files[`../backend/data/processed/institutes/${slug}.json`];
    const request = file ? file().then(url => fetch(url)).then(response => {
      if (!response.ok) throw new Error("The bundled institute data could not be loaded.");
      return response.json();
    }) : Promise.reject(new Error("No bundled data for this institute."));
    loaded.set(slug, request.catch(error => { loaded.delete(slug); throw error; }));
  }
  return loaded.get(slug);
}

export async function localSummary(slug, ...filters) {
  return summarize(await loadInstitute(slug), ...filters);
}

export async function localProfessor(name) {
  const member = facultyMember(name);
  return member ? professorFrom(await loadInstitute(member.slug), name) : null;
}
