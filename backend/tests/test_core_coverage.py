"""Coverage and alias regressions against the pinned CORE catalogue."""
import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'scripts'))
from core_venues import resolve_core_entry, classify_core
from venue_rules import load_rules, classify_csr


class CoreCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue = json.loads((BASE / 'data/raw/core_venues.json').read_text(encoding='utf-8'))

    def test_every_ranked_catalogue_entry_is_resolvable_by_exact_title(self):
        ranked = [v for v in self.catalogue['by_id'].values() if v['rank'] in {'A*', 'A'}]
        self.assertEqual(sum(v['rank'] == 'A*' for v in ranked), 60)
        self.assertEqual(sum(v['rank'] == 'A' for v in ranked), 117)
        for entry in ranked:
            with self.subTest(venue=entry['title']):
                self.assertEqual(resolve_core_entry({'venue': entry['title']}, None, self.catalogue)['id'], entry['id'])

    def test_aliases_and_ambiguous_names(self):
        for venue, acronym in [('ECML/PKDD (7)', 'ECML PKDD'), ('APPROX-RANDOM', 'APPROX/RANDOM'),
                               ('ICSM', 'ICSME'), ('OOPSLA2', 'OOPSLA'), ('SP', 'SP'),
                               ('IEEE Symposium on Security and Privacy', 'SP'), ('Proc. Priv. Enhancing Technol.', 'PETS')]:
            self.assertEqual(resolve_core_entry({'venue': venue}, None, self.catalogue)['acronym'], acronym)
        self.assertIsNone(resolve_core_entry({'venue': 'ISWC', 'key': 'conf/iswc/test'}, None, self.catalogue))
        self.assertEqual(resolve_core_entry({'venue': 'ISWC (2)', 'key': 'conf/semweb/test'}, None, self.catalogue)['id'], '1338')
        for venue in ['ISWC (Posters & Demos)', 'ECML/PKDD Workshops', 'AAAI Workshops']:
            self.assertIsNone(resolve_core_entry({'venue': venue, 'key': 'conf/semweb/test'}, None, self.catalogue))

    @unittest.skipUnless((BASE / 'data/reference/csrankings.py').exists(), 'Reference required')
    def test_journal_proceedings_require_validated_issues_and_short_papers_stay_excluded(self):
        rules = load_rules()
        paper = dict(key='journals/pacmpl/test', venue='Proc. ACM Program. Lang.', year=2022,
                     pages='786-810', type='article', number='OOPSLA2', volume='6', title='Example', url='')
        csr = classify_csr(paper, rules)
        self.assertEqual(classify_core(paper, csr, self.catalogue, rules)['source'], 'core-a')
        self.assertIsNone(classify_core(paper, None, self.catalogue, rules))
        paper.update(venue='ECML/PKDD (2)', pages='1-5', type='inproceedings')
        self.assertIsNone(classify_core(paper, None, self.catalogue, rules))
