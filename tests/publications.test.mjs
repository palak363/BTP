import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { filterPapers, sortPapers, venueDistribution, venueName } from '../src/publications.js';

const dataset = JSON.parse(fs.readFileSync(new URL('../backend/data/processed/iiitd_dataset.json', import.meta.url)));
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
