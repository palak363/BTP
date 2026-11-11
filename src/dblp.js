// Accept DBLP person identifiers and profile URLs without fetching user-supplied URLs.
export function normalizeDblpId(value) {
  let text = value.trim();
  if (/^(?:https?:\/\/|(?:www\.)?dblp\.)/i.test(text)) {
    try {
      const url = new URL(/^https?:\/\//i.test(text) ? text : `https://${text}`);
      if (!['dblp.org', 'www.dblp.org', 'dblp.uni-trier.de'].includes(url.hostname.toLowerCase())) return '';
      if (!url.pathname.startsWith('/pid/')) return '';
      text = decodeURIComponent(url.pathname);
    } catch { return ''; }
  }
  text = text.replace(/^\/?pid\//, '').replace(/\.(?:html|xml|json)$/, '').replace(/\/$/, '');
  return /^[a-zA-Z0-9/_-]+$/.test(text) ? text : '';
}

export function findDblpFaculty(faculty, query) {
  const id = normalizeDblpId(query);
  if (!id) return [];
  return faculty.filter(person => normalizeDblpId(person.dblp_url || '').includes(id))
    .sort((a, b) => Number(normalizeDblpId(b.dblp_url) === id) - Number(normalizeDblpId(a.dblp_url) === id) || a.name.localeCompare(b.name));
}

const normalizedName = value => value.normalize("NFKD").replace(/\p{Diacritic}/gu, "")
  .toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, " ").trim();

export function findFaculty(faculty, query) {
  const dbplMatches = findDblpFaculty(faculty, query);
  if (dbplMatches.length) return dbplMatches;
  const terms = normalizedName(query).split(" ").filter(Boolean);
  if (!terms.length) return [];
  return faculty.filter(person => {
    const name = normalizedName(person.name);
    return terms.every(term => name.includes(term));
  }).sort((a, b) => {
    const left = normalizedName(a.name), right = normalizedName(b.name), whole = terms.join(" ");
    return Number(right === whole) - Number(left === whole)
      || Number(right.startsWith(whole)) - Number(left.startsWith(whole))
      || a.name.localeCompare(b.name);
  });
}
