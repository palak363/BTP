import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { findDblpFaculty, normalizeDblpId } from '../src/dblp.js';
const { faculty } = JSON.parse(fs.readFileSync(new URL('../backend/data/processed/iiitd_dataset.json', import.meta.url)));

test('DBLP IDs and profile URLs resolve every loaded faculty identity', () => {
  for (const person of faculty) {
    const id = normalizeDblpId(person.dblp_url);
    assert.ok(id);
    for (const input of [id, person.dblp_url, `${person.dblp_url}.html`, ` pid/${id} `, `https://dblp.org/pid/${id}.xml?view=bibtex`]) {
      assert.equal(findDblpFaculty(faculty, input)[0]?.name, person.name);
    }
  }
});
test('partial searches and invalid inputs are handled without false URL matches', () => {
  assert.ok(findDblpFaculty(faculty, '232/').length > 0);
  for (const input of ['', 'https://example.com/pid/232/6141', 'https://dblp.org.evil.test/pid/232/6141', 'https://dblp.org/rec/conf/example', 'javascript:alert(1)', '%', 'not a person id']) {
    assert.deepEqual(findDblpFaculty(faculty, input), []);
  }
});
