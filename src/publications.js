export const sourceNames = { csrankings: "CSRankings", "core-a-star": "CORE A*", "core-a": "CORE A", ieee: "IEEE Trans.", acm: "ACM Trans." };
export const normalizeVenueName = value => String(value || "").replace(/\s+\(\d+\)$/, "").trim();
export const venueName = paper => normalizeVenueName(paper.venue || paper.booktitle || paper.journal || "Unknown venue");
const transactionJournal = /^(?:ACM|IEEE)\s+(?:Trans\.(?:\s|$)|Transactions?\b)/i;
const transactionJournals = {
  ieee: /^IEEE\s+(?:Trans\.(?:\s|$)|Transactions?\b)/i,
  acm: /^ACM\s+(?:Trans\.(?:\s|$)|Transactions?\b)/i,
};
const acmIeeeJournalName = /^(?:ACM|IEEE|Proc\.\s*ACM|J\.\s*ACM)\b/i;
const acmIeeeDoi = /^(?:10\.1145|10\.1109)\//i;

export function isTransactionPaper(paper, source) {
  if (paper.type !== "article") return false;
  const venue = paper.journal || venueName(paper);
  return source ? Boolean(transactionJournals[source]?.test(venue))
    : Object.values(transactionJournals).some(pattern => pattern.test(venue));
}

export function isVisiblePaper(paper) {
  if (paper.type !== "article") return true;
  const isRankedVenue = (paper.memberships || []).some(({ source }) =>
    source === "csrankings" || source === "core-a-star" || source === "core-a");
  if (isRankedVenue) return true;
  const venue = paper.journal || venueName(paper);
  const isAcmIeee = acmIeeeJournalName.test(venue) || (paper.dois || []).some(doi => acmIeeeDoi.test(doi));
  return !isAcmIeee || transactionJournal.test(venue);
}
export function filterPapers(papers, { venues = [], sources = [], periods = [], search = "", optionalVenues = [], includeOptional = false } = {}) {
  const query = search.trim().toLowerCase();
  const isOptionalCsrMembership = item => item.source === "csrankings" && optionalVenues.includes(item.area);
  const matchesSource = (paper, source) => source === "ieee" || source === "acm"
    ? isTransactionPaper(paper, source) && paper.memberships.some(item => item.source === source)
    : paper.memberships.some(item => item.source === source && (includeOptional || !isOptionalCsrMembership(item)));
  return papers.filter(paper => {
    const memberships = paper.memberships || [];
    const hasOptionalCsrMembership = memberships.some(isOptionalCsrMembership);
    const hasEligibleMembership = memberships.some(item => includeOptional || !isOptionalCsrMembership(item));
    return isVisiblePaper(paper) && (!hasOptionalCsrMembership || includeOptional || hasEligibleMembership)
    && (!venues.length || venues.includes(venueName(paper)))
    && (!sources.length || sources.some(source => matchesSource(paper, source)))
    && (!periods.length || periods.some(({ start, end }) => paper.year >= start && paper.year <= end))
    && `${paper.title} ${venueName(paper)}`.toLowerCase().includes(query);
  });
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
