import snapshot from "../backend/data/processed/iiitd_dataset.json";

export const availableAreas = snapshot.metadata.available_areas;
export const availableSources = snapshot.metadata.available_sources;

export function localSummary(start, end, area, includeOptional = false, sources = ["csrankings"]) {
  if (sources.some(source => !availableSources.includes(source))) return null;
  const rows = new Map(snapshot.faculty.map(f => [f.name, { ...f, papers: 0, score: 0, domains: {} }]));
  const domains = {}, venues = {};
  const published = snapshot.metadata.data_source === "csrankings-published-counts";
  let unique = 0;
  const addFaculty = (name, domain, count, credit) => {
    const row = rows.get(name);
    row.papers += count;
    row.score += credit;
    row.domains[domain] = (row.domains[domain] || 0) + count;
  };
  const addDistribution = (domain, venue, count) => {
    domains[domain] = (domains[domain] || 0) + count;
    venues[venue] = (venues[venue] || 0) + count;
  };
  if (published) {
    for (const cell of snapshot.counts) {
      if (!includeOptional && snapshot.metadata.optional_venues.includes(cell.area)) continue;
      const domain = snapshot.metadata.area_names[cell.area] || cell.area;
      if (cell.year < start || cell.year > end || (area && domain !== area)) continue;
      addFaculty(cell.name, domain, cell.count, cell.adjustedcount);
      addDistribution(domain, cell.area, cell.count);
    }
  } else {
    for (const paper of snapshot.publications) {
      const membership = paper.memberships.find(m => sources.includes(m.source) && m.year >= start && m.year <= end &&
        (!area || m.domain === area) && (m.source !== "csrankings" || includeOptional || !snapshot.metadata.optional_venues.includes(m.area)));
      if (!membership) continue;
      unique += 1;
      addDistribution(membership.domain, membership.venue, 1);
      for (const name of paper.faculty) addFaculty(name, membership.domain, 1, 1 / paper.authors.length);
    }
  }
  const faculty = [...rows.values()].map(row => ({ ...row, top_domain: Object.entries(row.domains).sort((a,b) => b[1]-a[1])[0]?.[0] || "No selected papers" }));
  return { metadata: snapshot.metadata, total_faculty: faculty.length, total_papers: published ? null : unique,
    faculty_paper_count: faculty.reduce((sum,f) => sum + f.papers, 0),
    adjusted_count: faculty.reduce((sum,f) => sum + f.score, 0), faculty_rankings: faculty,
    top_areas: Object.entries(domains).map(([area,papers]) => ({area,papers})).sort((a,b) => b.papers-a.papers),
    top_venues: Object.entries(venues).map(([venue,papers]) => ({venue,papers})).sort((a,b) => b.papers-a.papers) };
}
