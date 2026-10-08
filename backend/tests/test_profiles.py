"""Faculty bibliographies must preserve every loaded record and exact identity."""
import json
import sys
import unittest
from pathlib import Path
from urllib.parse import quote

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from api.app import app


class Profiles(unittest.TestCase):
    def test_every_loaded_faculty(self):
        dataset = json.loads((BASE / 'data/processed/iiitd_dataset.json').read_text(encoding='utf-8'))
        client = app.test_client()
        for faculty in dataset['faculty']:
            with self.subTest(name=faculty['name']):
                response = client.get('/iiitd/faculty/' + quote(faculty['name']) + '?start_year=2026&sources=csrankings')
                self.assertEqual(response.status_code, 200)
                actual = response.get_json()
                expected = {p['key']: p for p in dataset['publications'] if faculty['name'] in p['faculty']}
                self.assertEqual(actual['name'], faculty['name'])
                self.assertEqual(len(actual['publications']), len(expected))
                self.assertEqual({p['key']: p for p in actual['publications']}, expected)

    def test_unknown_identity(self):
        self.assertEqual(app.test_client().get('/iiitd/faculty/Unknown%20Professor').status_code, 404)
