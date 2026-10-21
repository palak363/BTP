"""Database imports preserve complete snapshots and roll back failed replacements."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from sqlalchemy import create_engine, event, select, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from repository import import_dataset, read_dataset
from models import ResearchDataset, ResearchPaper
from api.app import app


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        self.dataset = json.loads((BASE / 'data/processed/iiitd_dataset.json').read_text(encoding='utf-8-sig'))
        self.identifier = import_dataset(self.dataset, self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_complete_round_trip_and_idempotent_import(self):
        self.assertEqual(read_dataset(self.engine), self.dataset)
        self.assertEqual(import_dataset(self.dataset, self.engine), self.identifier)
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(ResearchDataset)), 1)
            self.assertEqual(session.scalar(select(func.count()).select_from(ResearchPaper)), len(self.dataset['publications']))

    def test_failed_write_preserves_active_snapshot(self):
        replacement = copy.deepcopy(self.dataset)
        replacement['metadata']['generated_at'] = '2030-01-01T00:00:00+00:00'
        def fail_memberships(connection, cursor, statement, parameters, context, executemany):
            if statement.startswith('INSERT INTO research_memberships'):
                raise RuntimeError('Simulated failed import')
        event.listen(self.engine, 'before_cursor_execute', fail_memberships)
        try:
            with self.assertRaises(RuntimeError):
                import_dataset(replacement, self.engine)
        finally:
            event.remove(self.engine, 'before_cursor_execute', fail_memberships)
        self.assertEqual(read_dataset(self.engine), self.dataset)
        with Session(self.engine) as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(ResearchDataset)), 1)

    def test_invalid_authorship_rejected_before_replacement(self):
        replacement = copy.deepcopy(self.dataset)
        replacement['publications'][0]['faculty'] = ['Unknown faculty']
        with self.assertRaises(ValueError):
            import_dataset(replacement, self.engine)
        self.assertEqual(read_dataset(self.engine), self.dataset)

    def test_api_uses_database_and_reports_unavailable_without_details(self):
        replacement = copy.deepcopy(self.dataset)
        replacement['publications'] = []
        import_dataset(replacement, self.engine)
        with patch('api.app.read_dataset', side_effect=lambda: read_dataset(self.engine)):
            result = app.test_client().get('/iiitd/domains').get_json()
            self.assertEqual(result['total_papers'], 0)
            self.assertEqual(result['total_faculty'], 33)
        with patch('api.app.read_dataset', side_effect=OperationalError('secret statement', {}, Exception('secret password'))):
            response = app.test_client().get('/iiitd/domains')
            self.assertEqual(response.status_code, 503)
            self.assertNotIn('secret', response.get_data(as_text=True))
