export const sourceNames = { csrankings: "CSRankings", "core-a-star": "CORE A*", "core-a": "CORE A" };
export const venueName = paper => paper.venue || paper.booktitle || paper.journal || "Unknown venue";
export function filterPapers(papers, { venues = [], sources = [], periods = [], search = "" } = {}) {
  const query = search.trim().toLowerCase();
  return papers.filter(paper => (!venues.length || venues.includes(venueName(paper)))
    && (!sources.length || paper.memberships.some(item => sources.includes(item.source)))
    && (!periods.length || periods.some(({ start, end }) => paper.year >= start && paper.year <= end))
    && `${paper.title} ${venueName(paper)}`.toLowerCase().includes(query));
}
export function venueDistribution(papers) {
  const counts = new Map();
  for (const paper of new Map(papers.map(p => [p.key, p])).values()) {
    const name = venueName(paper);
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  return [...counts].map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}
export function sortPapers(papers, order) {
  return [...papers].sort((a, b) => {
    const year = (Number(b.year) || 0) - (Number(a.year) || 0);
    const venue = venueName(a).localeCompare(venueName(b));
    return (order === "oldest" ? -year : order === "venue" ? venue || year : year)
      || (a.title || "").localeCompare(b.title || "") || a.key.localeCompare(b.key);
  });
}
