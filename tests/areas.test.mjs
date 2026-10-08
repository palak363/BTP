import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

// Load the bundled summary in Node without Vite's JSON import transform.
const snapshot = JSON.parse(fs.readFileSync(new URL('../backend/data/processed/iiitd_dataset.json', import.meta.url)));
const source = fs.readFileSync(new URL('../src/data.js', import.meta.url), 'utf8')
  .replace('import snapshot from "../backend/data/processed/iiitd_dataset.json";', `const snapshot = ${JSON.stringify(snapshot)};`);
const { localSummary } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

test('all areas preserve existing counts; no areas means no publications', () => {
  const original = localSummary(2016, 2026, '');
  assert.deepEqual(localSummary(2016, 2026, snapshot.metadata.available_areas), original);
  const none = localSummary(2016, 2026, []);
  assert.equal(none.total_papers, 0);
  assert.equal(none.faculty_paper_count, 0);
  assert.equal(none.total_faculty, snapshot.faculty.length);
  assert.ok(none.faculty_rankings.every(faculty => faculty.papers === 0));
});
test('multiple research areas count the matching paper union across sources and years', () => {
  const areas = ['Artificial intelligence', 'Natural language processing'];
  for (const sources of [['csrankings'], ['csrankings', 'core-a-star', 'core-a']]) {
    const result = localSummary(2016, 2026, areas, false, sources);
    const expected = snapshot.publications.filter(paper => paper.memberships.some(m =>
      sources.includes(m.source) && areas.includes(m.domain) && m.year >= 2016 && m.year <= 2026
      && (m.source !== 'csrankings' || !snapshot.metadata.optional_venues.includes(m.area))));
    assert.equal(result.total_papers, expected.length);
    assert.equal(result.faculty_paper_count, expected.reduce((sum, paper) => sum + paper.faculty.length, 0));
    assert.ok(result.top_areas.every(item => areas.includes(item.area)));
  }
});
