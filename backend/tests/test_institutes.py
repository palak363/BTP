"""Multi-institute rosters, identity resolution and API."""
import json
import sys
import unittest
from pathlib import Path
from urllib.parse import quote

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'scripts'))
sys.path.insert(0, str(BASE))
from institutes import choose, hints, merge_duplicates, slug
from build_institutes import INDEX, INSTITUTES
from api.app import app


def person(*affiliations, webpages=()):
    return {'affiliations': set(affiliations), 'webpages': set(webpages)}


class ResolutionTests(unittest.TestCase):
    entry = {'institution': 'IIT Kharagpur', 'homepage': 'https://cse.iitkgp.ac.in/~someone/'}

    def test_single_and_missing_candidates(self):
        self.assertEqual(choose('A', self.entry, {'pid/1': person()}), ('pid/1', 'single match'))
        self.assertEqual(choose('A', self.entry, {})[0], None)

    def test_affiliation_and_homepage_pick_one_person(self):
        matches = {'pid/1': person('IBM Almaden Research Center, San Jose, CA, USA'),
                   'pid/2': person('Indian Institute of Technology Kharagpur, Department of CSE, India')}
        self.assertEqual(choose('A', self.entry, matches), ('pid/2', 'affiliation match'))
        matches['pid/1']['webpages'].add('https://cse.iitkgp.ac.in/~someone')
        self.assertEqual(choose('A', self.entry, matches), ('pid/1', 'homepage match'))

    def test_ambiguous_affiliation_is_not_guessed(self):
        matches = {'pid/1': person('IIT Kharagpur, India'), 'pid/2': person('IIT Kharagpur, West Bengal')}
        self.assertIsNone(choose('A', self.entry, matches)[0])
        self.assertIsNone(choose('A', self.entry, {'pid/1': person('Kharagpur'), 'pid/2': person('Delhi')})[0])

    def test_iit_hints_do_not_match_other_campuses(self):
        self.assertIn('indian institute of technology bhu', hints('IIT (BHU) Varanasi'))
        self.assertNotIn('indian institute of technology delhi', hints('IIT Bombay'))
        self.assertEqual(slug('IIT (BHU) Varanasi'), 'iit-bhu-varanasi')

    def test_duplicate_reference_names_merge_into_dblp_name(self):
        rows = [{'institution': 'IISc Bangalore', 'name': 'Y. Narahari', 'dblp_url': 'p', 'resolution': 'single match'},
                {'institution': 'IISc Bangalore', 'name': 'Y. Narahari 0001', 'dblp_url': 'p', 'resolution': 'exact name'}]
        self.assertEqual(merge_duplicates(rows), [dict(rows[1], aliases='Y. Narahari')])
        with self.assertRaises(ValueError):
            merge_duplicates([rows[0], dict(rows[1], institution='IIT Delhi')])


@unittest.skipUnless(INDEX.exists(), 'Build institutes first')
class InstituteApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.index = json.loads(INDEX.read_text(encoding='utf-8'))

    def test_index_totals_match_each_institute_summary(self):
        for entry in self.index['institutes']:
            with self.subTest(institute=entry['name']):
                for source, totals in entry['totals'].items():
                    sources = ','.join(self.index['metadata']['available_sources']) if source == 'all' else source
                    payload = self.client.get(f"/institutes/{entry['slug']}/domains?sources={sources}").get_json()
                    self.assertEqual(payload['total_papers'], totals['papers'])
                    self.assertEqual(payload['faculty_paper_count'], totals['faculty_papers'])
                    self.assertEqual(payload['total_faculty'], entry['faculty'])
                    self.assertEqual(sum(f['papers'] > 0 for f in payload['faculty_rankings']), totals['faculty'])

    def test_every_faculty_member_belongs_to_one_institute(self):
        names = [f['name'] for f in self.index['faculty']]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), sum(e['faculty'] for e in self.index['institutes']))
        for entry in self.index['institutes']:
            dataset = json.loads((INSTITUTES / f"{entry['slug']}.json").read_text(encoding='utf-8'))
            self.assertEqual({f['name'] for f in dataset['faculty']},
                             {f['name'] for f in self.index['faculty'] if f['slug'] == entry['slug']})

    def test_faculty_route_finds_any_institute(self):
        member = self.index['faculty'][-1]
        response = self.client.get('/faculty/' + quote(member['name']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['institution'], member['institution'])
        self.assertEqual(self.client.get('/faculty/Unknown%20Professor').status_code, 404)

    def test_unknown_institute_and_legacy_routes(self):
        self.assertEqual(self.client.get('/institutes/unknown/domains').status_code, 404)
        self.assertEqual(self.client.get('/iiitd/domains').get_json(), self.client.get('/institutes/iiit-delhi/domains').get_json())


if __name__ == '__main__':
    unittest.main()
