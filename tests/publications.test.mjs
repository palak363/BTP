import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { filterPapers, isVisiblePaper, sortPapers, venueDistribution, venueName } from '../src/publications.js';
import { localSummary } from '../src/summary.js';

const dataset = JSON.parse(fs.readFileSync(new URL('../backend/data/processed/institutes/iiit-delhi.json', import.meta.url)));
const iitBombay = JSON.parse(fs.readFileSync(new URL('../backend/data/processed/institutes/iit-bombay.json', import.meta.url)));
test('ranked papers and ACM or IEEE Transactions journal articles are visible', () => {
  const records = [
    { key: 'conference', type: 'inproceedings', venue: 'ACM Conference', dois: ['10.1145/1'], memberships: [] },
    { key: 'acm-transaction', type: 'article', venue: 'ACM Trans. Graph.', dois: ['10.1145/2'], memberships: [{ source: 'acm' }] },
    { key: 'ieee-transaction', type: 'article', venue: 'IEEE Trans. Vis. Comput. Graph.', dois: ['10.1109/3'], memberships: [{ source: 'ieee' }] },
    { key: 'full-ieee-transaction', type: 'article', venue: 'IEEE Transactions on Example', memberships: [{ source: 'ieee' }] },
    { key: 'acm-proceedings', type: 'article', venue: 'Proc. ACM Program. Lang.', dois: ['10.1145/4'], memberships: [] },
    { key: 'ranked-acm-proceedings', type: 'article', venue: 'Proc. ACM Program. Lang.', dois: ['10.1145/7'], memberships: [{ source: 'csrankings' }] },
    { key: 'ieee-journal', type: 'article', venue: 'IEEE Access', dois: ['10.1109/5'], memberships: [] },
    { key: 'ieee-conference-membership', type: 'inproceedings', venue: 'ICASSP', dois: ['10.1109/8'], memberships: [{ source: 'ieee' }] },
    { key: 'acm-conference-membership', type: 'inproceedings', venue: 'CHI', dois: ['10.1145/9'], memberships: [{ source: 'acm' }] },
    { key: 'other-journal', type: 'article', venue: 'J. Mach. Learn. Res.', dois: ['10.5555/6'], memberships: [] },
  ];
  assert.deepEqual(records.filter(isVisiblePaper).map(record => record.key), ['conference', 'acm-transaction', 'ieee-transaction', 'full-ieee-transaction', 'ranked-acm-proceedings', 'ieee-conference-membership', 'acm-conference-membership', 'other-journal']);
  assert.deepEqual(filterPapers(records).map(record => record.key), ['conference', 'acm-transaction', 'ieee-transaction', 'full-ieee-transaction', 'ranked-acm-proceedings', 'ieee-conference-membership', 'acm-conference-membership', 'other-journal']);
  assert.deepEqual(filterPapers(records, { sources: ['ieee'] }).map(record => record.key), ['ieee-transaction', 'full-ieee-transaction']);
  assert.deepEqual(filterPapers(records, { sources: ['acm'] }).map(record => record.key), ['acm-transaction']);
  assert.deepEqual(filterPapers(records, { sources: ['csrankings', 'ieee'] }).map(record => record.key), ['ieee-transaction', 'full-ieee-transaction', 'ranked-acm-proceedings']);
});
test('Virendra Singh IEEE source filter shows his five Transactions articles, not conferences', () => {
  const papers = iitBombay.publications.filter(paper => paper.faculty.includes('Virendra Singh'));
  const selected = filterPapers(papers, { sources: ['ieee'] });
  assert.deepEqual(selected.map(paper => paper.key).sort(), [
    'journals/tcad/KumarBFS20',
    'journals/tcad/VineeshKSSFS21',
    'journals/tkde/GuptaOAPS25',
    'journals/tvlsi/KumarABFS20',
    'journals/tvlsi/SinghISF06',
  ]);
  assert.ok(selected.every(paper => paper.type === 'article'));
});
test('multiple venues and overlapping year periods combine without duplicate papers', () => {
  const papers = [
    { key: 'a', title: 'First', venue: 'ACL', year: 2016, memberships: [{ source: 'csrankings' }, { source: 'core-a-star' }] },
    { key: 'b', title: 'Second', venue: 'AAAI', year: 2020, memberships: [{ source: 'core-a-star' }] },
    { key: 'c', title: 'Third', venue: 'CHI', year: 2026, memberships: [{ source: 'core-a' }] },
  ];
  assert.deepEqual(filterPapers(papers), papers);
  const filters = { venues: ['ACL', 'AAAI'], sources: ['csrankings', 'core-a-star'], periods: [{ start: 2016, end: 2020 }, { start: 2020, end: 2026 }] };
  assert.deepEqual(filterPapers(papers, filters).map(p => p.key), ['a', 'b']);
  assert.deepEqual(filterPapers(papers, { ...filters, search: 'second' }).map(p => p.key), ['b']);
  assert.deepEqual(filterPapers(papers, { periods: [{ start: 2021, end: 2025 }] }), []);
  assert.deepEqual(filterPapers(papers, { periods: [{ start: 2016, end: 2016 }, { start: 2026, end: 2026 }] }).map(p => p.key), ['a', 'c']);
});
test('duplicate DBLP venue suffixes are removed and their papers share one venue', () => {
  const papers = [
    { key: 'plain', title: 'Plain', venue: 'ACL', memberships: [{ source: 'csrankings' }] },
    { key: 'disambiguated', title: 'Disambiguated', venue: 'ACL (1)', memberships: [{ source: 'csrankings' }] },
  ];
  assert.equal(venueName(papers[1]), 'ACL');
  assert.deepEqual(filterPapers(papers, { venues: ['ACL'] }), papers);
  assert.deepEqual(venueDistribution(papers), [{ name: 'ACL', count: 2 }]);
});
test('local institute summaries merge suffixed venue counts', () => {
  const membership = venue => ({ source: 'csrankings', year: 2023, area: 'acl', domain: 'NLP', venue });
  const snapshot = {
    metadata: { available_sources: ['csrankings'], data_source: 'dblp-bibliographies', optional_venues: [] },
    faculty: [{ name: 'Alice' }],
    publications: [
      { key: 'plain', faculty: ['Alice'], memberships: [membership('ACL')] },
      { key: 'disambiguated', faculty: ['Alice'], memberships: [membership('ACL (1)')] },
    ],
  };
  assert.deepEqual(localSummary(snapshot, 2020, 2024, '').top_venues, [{ venue: 'ACL', papers: 2 }]);
});
test('CSRankings optional venues are excluded unless explicitly enabled', () => {
  const optionalVenues = dataset.metadata.optional_venues;
  for (const [name, defaultCount, includedCount] of [
    ['Vikram Goyal', 4, 7],
    ['Mukesh K. Mohania', 6, 10],
  ]) {
    const papers = dataset.publications.filter(paper => paper.faculty.includes(name));
    assert.equal(filterPapers(papers, { sources: ['csrankings'], optionalVenues }).length, defaultCount);
    assert.equal(filterPapers(papers, { sources: ['csrankings'], optionalVenues, includeOptional: true }).length, includedCount);
  }
});
test('every faculty chart totals unique loaded papers', () => {
  for (const faculty of dataset.faculty) {
    const papers = dataset.publications.filter(paper => paper.faculty.includes(faculty.name));
    assert.equal(venueDistribution([...papers, ...papers]).reduce((sum, venue) => sum + venue.count, 0), new Set(papers.map(p => p.key)).size);
  }
});
test('paper sorting preserves records and orders years and venues', () => {
  const original = [...dataset.publications];
  for (const order of ['newest', 'oldest', 'venue']) {
    const sorted = sortPapers(original, order);
    assert.equal(sorted.length, original.length);
    for (let i = 1; i < sorted.length; i++) {
      if (order === 'venue') assert.ok(venueName(sorted[i - 1]).localeCompare(venueName(sorted[i])) <= 0);
      else assert.ok(order === 'oldest' ? sorted[i - 1].year <= sorted[i].year : sorted[i - 1].year >= sorted[i].year);
    }
  }
  assert.deepEqual(original, dataset.publications);
  assert.deepEqual(sortPapers([], 'newest'), []);
  assert.deepEqual(venueDistribution([]), []);
});
