import unittest
import json
from pathlib import Path
from journal_policy import is_visible_paper, transaction_publisher
from api.app import app


class JournalPolicyTests(unittest.TestCase):
    def test_only_transactions_are_visible_for_acm_and_ieee_journal_articles(self):
        base = {'key': 'journal/test', 'type': 'article', 'dois': []}
        for venue in ['ACM Trans. Graph.', 'IEEE Trans. Vis. Comput. Graph.']:
            self.assertTrue(is_visible_paper(dict(base, venue=venue, journal=venue)))
        for venue, doi in [('Proc. ACM Program. Lang.', '10.1145/1'), ('IEEE Access', '10.1109/1'),
                           ('J. ACM', '10.1145/2')]:
            self.assertFalse(is_visible_paper(dict(base, venue=venue, journal=venue, dois=[doi])))

    def test_conference_and_other_publisher_journal_are_unchanged(self):
        self.assertTrue(is_visible_paper({'type': 'inproceedings', 'venue': 'ACM Conference', 'dois': ['10.1145/1']}))
        self.assertTrue(is_visible_paper({'type': 'article', 'venue': 'J. Mach. Learn. Res.', 'dois': ['10.5555/1']}))

    def test_ranked_acm_journal_is_visible(self):
        paper = {'type': 'article', 'venue': 'Proc. ACM Program. Lang.',
                 'journal': 'Proc. ACM Program. Lang.', 'dois': ['10.1145/1'],
                 'memberships': [{'source': 'csrankings'}]}
        self.assertTrue(is_visible_paper(paper))

    def test_every_iiitd_api_bibliography_obeys_the_policy(self):
        base = Path(__file__).resolve().parents[1]
        dataset = json.loads((base / 'data/processed/institutes/iiit-delhi.json').read_text(encoding='utf-8-sig'))
        client = app.test_client()
        for faculty in dataset['faculty']:
            with self.subTest(faculty=faculty['name']):
                response = client.get('/iiitd/faculty/' + faculty['name'])
                self.assertEqual(response.status_code, 200)
                self.assertTrue(all(is_visible_paper(paper) for paper in response.get_json()['publications']))

    def test_publisher_memberships_are_transactions_across_all_institutes(self):
        root = Path(__file__).resolve().parents[1] / 'data/processed/institutes'
        datasets = [path for path in root.glob('*.json') if '.validation' not in path.name]
        self.assertTrue(datasets)
        for path in datasets:
            data = json.loads(path.read_text(encoding='utf-8'))
            for paper in data['publications']:
                for membership in paper.get('memberships', []):
                    if membership['source'] in {'ieee', 'acm'}:
                        with self.subTest(dataset=path.name, key=paper['key']):
                            self.assertEqual(transaction_publisher(paper), membership['source'])
