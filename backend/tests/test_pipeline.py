"""Regression tests for publication eligibility, counting and API behavior."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'scripts'))
sys.path.insert(0, str(BASE))
from fetch_dblp import parse_profile, fetch_papers
from fetch_sparql import parse_results, SCHEMA, RDF_TYPE
from venue_rules import load_rules, classify_csr
from core_venues import classify_core
from publisher_venues import classify_publisher, dois_from_links
from build_institutes import build_institute
from build_iiitd_dataset import summarize
from api.app import app


def paper(**changes):
    value = dict(key='conf/test/p1', title='A paper', year=2023, venue='AAAI', type='inproceedings',
                 authors=['Alice', 'Bob', 'Student'], pages='1-10', volume='', number='', url='')
    value.update(changes)
    return value


def dataset():
    csr = dict(source='csrankings', year=2023, area='aaai', domain='Artificial intelligence', venue='AAAI')
    core = dict(csr, source='core-a-star')
    return {'metadata': {'data_source': 'dblp-bibliographies'}, 'faculty': [
        {'name': 'Alice'}, {'name': 'Bob'}, {'name': 'Zero'}],
        'publications': [dict(paper(), faculty=['Alice', 'Bob'], memberships=[csr, core])]}


class ParserTests(unittest.TestCase):
    def test_booktitle_nested_title_authors_pages_and_duplicate_key(self):
        entry = '<r><inproceedings key="conf/aaai/test"><author>Alice</author><author>Bob</author><title>A <i>nested</i> title</title><booktitle>AAAI</booktitle><year>2023</year><pages>12:1-12:8</pages></inproceedings></r>'
        xml = '<dblpperson name="Alice"><person><author>Alice Alias</author></person>' + entry * 2 + '</dblpperson>'
        result = parse_profile(xml, 'Alice Alias')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['venue'], 'AAAI')
        self.assertEqual(result[0]['title'], 'A nested title')
        self.assertEqual(result[0]['authors'], ['Alice', 'Bob'])
        self.assertEqual(result[0]['pages'], '12:1-12:8')

    def test_wrong_identity_and_html_fail(self):
        with self.assertRaises(ValueError):
            parse_profile('<dblpperson name="Other" />', 'Alice')
        with self.assertRaises(ValueError):
            parse_profile('<html />', 'Alice')

    def test_no_silent_zero_on_network_error(self):
        with patch('fetch_dblp.requests.get', side_effect=__import__('requests').ConnectionError()), patch('fetch_dblp.time.sleep'):
            with self.assertRaises(__import__('requests').ConnectionError):
                fetch_papers('https://dblp.org/pid/fiction/test.html', refresh=True)


class SparqlTests(unittest.TestCase):
    def payload(self, publication_year, event_year):
        pid, key = 'https://dblp.org/pid/test/alice', 'https://dblp.org/rec/conf/test/paper'
        triples = [(pid, SCHEMA + 'creatorName', 'Alice'),
                   (key, RDF_TYPE, SCHEMA + 'Inproceedings'),
                   (key, SCHEMA + 'authoredBy', pid),
                   (key, SCHEMA + 'title', 'A conference paper'),
                   (key, SCHEMA + 'publishedInBook', 'NAACL-HLT')]
        if publication_year is not None:
            triples.append((key, SCHEMA + 'yearOfPublication', str(publication_year)))
        if event_year is not None:
            triples.append((key, SCHEMA + 'yearOfEvent', str(event_year)))
        rows = [{'subject': {'value': s}, 'p': {'value': p}, 'o': {'value': o}} for s, p, o in triples]
        return {'results': {'bindings': rows}, 'meta': {'result-size-total': len(rows)}}

    def test_conference_year_corrects_bad_publisher_year(self):
        result = parse_results(self.payload(2014, 2024), 'https://dblp.org/pid/test/alice', 'Alice')[0]
        self.assertEqual(result['year'], 2024)
        self.assertEqual(result['publication_year'], 2014)

    def test_missing_publication_year_uses_event_year(self):
        result = parse_results(self.payload(None, 2023), 'https://dblp.org/pid/test/alice', 'Alice')[0]
        self.assertEqual(result['year'], 2023)
        self.assertIsNone(result['publication_year'])

    def test_wrong_identity_or_truncated_query_fails(self):
        payload = self.payload(2024, 2024)
        with self.assertRaises(ValueError):
            parse_results(payload, 'https://dblp.org/pid/test/alice', 'Other')
        payload['meta']['result-size-total'] += 1
        with self.assertRaises(ValueError):
            parse_results(payload, 'https://dblp.org/pid/test/alice', 'Alice')

    def test_dois_are_normalized(self):
        payload = self.payload(2024, 2024)
        row = {'subject': {'value': 'https://dblp.org/rec/conf/test/paper'}, 'p': {'value': SCHEMA + 'doi'},
               'o': {'value': 'https://doi.org/10.1109/ICASSP.2024.1'}}
        payload['results']['bindings'].append(row)
        payload['meta']['result-size-total'] += 1
        result = parse_results(payload, 'https://dblp.org/pid/test/alice', 'Alice')[0]
        self.assertEqual(result['dois'], ['10.1109/icassp.2024.1'])


class PublisherTests(unittest.TestCase):
    def test_only_transactions_journals_receive_ieee_or_acm_membership(self):
        self.assertIsNone(classify_publisher(paper(venue='ICASSP', booktitle='ICASSP', dois=['10.1109/x']), None))
        self.assertIsNone(classify_publisher(paper(venue='CHI', booktitle='CHI', dois=['10.1145/x']), None))
        ieee = paper(type='article', venue='IEEE Trans. Comput. Aided Des. Integr. Circuits Syst.',
                     journal='IEEE Trans. Comput. Aided Des. Integr. Circuits Syst.', dois=['10.1109/x'])
        acm = paper(type='article', venue='ACM Trans. Graph.', journal='ACM Trans. Graph.', dois=['10.1145/x'])
        self.assertEqual(classify_publisher(ieee, None)['source'], 'ieee')
        self.assertEqual(classify_publisher(acm, None)['source'], 'acm')
        self.assertIsNone(classify_publisher(paper(type='article', venue='IEEE Access', journal='IEEE Access',
                                                   dois=['10.1109/x']), None))

    def test_transaction_article_uses_csr_area_when_available(self):
        transaction = paper(type='article', venue='IEEE Trans. Comput. Aided Des. Integr. Circuits Syst.',
                            journal='IEEE Trans. Comput. Aided Des. Integr. Circuits Syst.', year=2023)
        csr = dict(source='csrankings', year=2024, area='aaai', domain='Artificial intelligence', venue='AAAI')
        result = classify_publisher(transaction, csr)
        self.assertEqual((result['venue'], result['area'], result['year']), (transaction['journal'], 'aaai', 2024))

    def test_doi_links_are_normalized(self):
        self.assertEqual(dois_from_links({'https://doi.org/10.1109/X.1'}, {'https://doi.ieeecomputersociety.org/10.1109/x.1',
                         'https://dl.acm.org/doi/10.1145/Y.2', 'http://dl.acm.org/citation.cfm?id=3', 'https://ieeexplore.ieee.org/document/4'}),
                         ['10.1109/x.1', '10.1145/y.2'])

    def test_conferences_and_non_transaction_journals_are_excluded(self):
        for venue in ['CVPR Workshops', 'ICDM (Workshops)', 'WWW (Companion Volume)', 'UbiComp Adjunct',
                      'CHI Extended Abstracts', 'e-Energy (Posters)', 'LLM4CODE@ICSE']:
            self.assertIsNone(classify_publisher(paper(venue=venue, booktitle=venue, dois=['10.1145/x']), None), venue)
        self.assertIsNone(classify_publisher(paper(type='article', dois=['10.1109/x']), None))

    def test_build_keeps_transactions_articles_for_professor_bibliography(self):
        records = [
            paper(key='journals/tcad/test', type='article', venue='IEEE Trans. Comput. Aided Des. Integr. Circuits Syst.',
                  journal='IEEE Trans. Comput. Aided Des. Integr. Circuits Syst.', pages='1-10', dois=['10.1109/x']),
            paper(key='journals/access/test', type='article', venue='IEEE Access', journal='IEEE Access',
                  pages='1-10', dois=['10.1109/y']),
        ]
        roster = {'name': 'Test Institute', 'slug': 'test-institute', 'homepage': '',
                  'faculty': [{'name': 'Virendra Singh', 'dblp_url': 'https://dblp.org/pid/test'}], 'unresolved': []}
        dataset = build_institute(roster, load_rules(), None,
                                  lambda *_args: records)
        self.assertEqual([paper['key'] for paper in dataset['publications']], ['journals/tcad/test'])
        self.assertEqual([m['source'] for m in dataset['publications'][0]['memberships']], ['ieee'])


@unittest.skipUnless((BASE / 'data/reference/csrankings.py').exists(), 'Download reference rules first')
class EligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules()

    def test_full_paper_and_short_paper(self):
        self.assertIsNotNone(classify_csr(paper(pages='1-6'), self.rules))
        self.assertIsNone(classify_csr(paper(pages='1-5'), self.rules))

    def test_exact_workshop_rejection_and_multipart_venue(self):
        self.assertIsNone(classify_csr(paper(venue='CVPR Workshops'), self.rules))
        self.assertEqual(classify_csr(paper(venue='ECCV (12)'), self.rules)['area'], 'eccv')

    def test_journal_proceedings_and_year_mapping(self):
        self.assertEqual(classify_csr(paper(venue='Proc. ACM Program. Lang.', number='POPL'), self.rules)['area'], 'popl')
        result = classify_csr(paper(venue='Proc. ACM Manag. Data', year=2023, number='3'), self.rules)
        self.assertEqual((result['area'], result['year']), ('sigmod', 2024))
        self.assertIsNone(classify_csr(paper(venue='ACM Trans. Graph.', year=2023, volume='42', number='1'), self.rules))

    def test_ase_specific_threshold(self):
        self.assertIsNone(classify_csr(paper(venue='ASE', pages='1-9'), self.rules))

    def test_core_overlap_short_papers_and_workshops(self):
        catalogue = {'venues': {'aaai': {'rank': 'A*', 'acronym': 'AAAI'}}}
        candidate = paper()
        csr = classify_csr(candidate, self.rules)
        self.assertEqual(classify_core(candidate, csr, catalogue, self.rules)['source'], 'core-a-star')
        self.assertIsNone(classify_core(paper(venue='AAAI Workshops'), None, catalogue, self.rules))
        self.assertEqual(classify_core(paper(pages='1-3'), None, catalogue, self.rules)['source'], 'core-a-star')
        self.assertIsNone(classify_core(paper(type='article'), None, catalogue, self.rules))


class CountingTests(unittest.TestCase):
    def test_duplicate_dblp_venue_suffixes_are_merged(self):
        value = dataset()
        duplicate = copy.deepcopy(value['publications'][0])
        duplicate['key'] = 'conf/test/p2'
        duplicate['memberships'][0]['venue'] = 'AAAI (1)'
        value['publications'].append(duplicate)
        result = summarize(value, 2023, 2023)
        self.assertEqual(result['top_venues'], [{'venue': 'AAAI', 'papers': 2}])

    def test_union_and_fractional_authorship(self):
        result = summarize(dataset(), 2023, 2023, ['csrankings', 'core-a-star'])
        self.assertEqual(result['total_papers'], 1)
        self.assertEqual(result['faculty_paper_count'], 2)
        self.assertAlmostEqual(result['adjusted_count'], 2/3)
        self.assertEqual(result['top_areas'][0]['papers'], 1)
        self.assertEqual(result['faculty_rankings'][-1]['papers'], 0)

    def test_former_affiliations_are_excluded_from_institute_summary(self):
        value = dataset()
        value['faculty'][1]['affiliation_status'] = 'former'
        result = summarize(value, 2023, 2023)
        self.assertEqual(result['total_faculty'], 2)
        self.assertEqual(result['faculty_paper_count'], 1)
        self.assertEqual({row['name'] for row in result['faculty_rankings']}, {'Alice', 'Zero'})

    def test_year_area_filters_and_empty_results(self):
        self.assertEqual(summarize(dataset(), 2024, 2024)['total_papers'], 0)
        self.assertEqual(summarize(dataset(), 2023, 2023, areas=['Databases'])['total_papers'], 0)

    def test_optional_venues_only_apply_to_csr_membership(self):
        value = dataset()
        value['publications'][0]['memberships'][0]['area'] = 'kdd'
        self.assertEqual(summarize(value, 2023, 2023)['total_papers'], 0)
        self.assertEqual(summarize(value, 2023, 2023, include_optional=True)['total_papers'], 1)
        self.assertEqual(summarize(value, 2023, 2023, ['core-a-star'])['total_papers'], 1)

    def test_snapshot_does_not_invent_unique_papers(self):
        value = {'metadata': {'data_source': 'csrankings-published-counts'},
                 'faculty': [{'name': 'Alice'}, {'name': 'Zero'}],
                 'counts': [{'name': 'Alice', 'area': 'aaai', 'year': 2023, 'count': 2, 'adjustedcount': .5}]}
        result = summarize(value, 2023, 2023)
        self.assertIsNone(result['total_papers'])
        self.assertEqual(result['faculty_paper_count'], 2)
        self.assertEqual(result['adjusted_count'], .5)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_endpoints_share_one_summary(self):
        response = self.client.get('/iiitd/domains?start_year=2016&end_year=2026')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['total_faculty'], 33)
        self.assertEqual(payload['faculty_paper_count'], sum(r['papers'] for r in payload['faculty_rankings']))
        self.assertEqual(self.client.get('/iiitd').get_json(), payload['faculty_rankings'])

    def test_reject_bad_years_areas_and_unavailable_sources(self):
        for query in ['start_year=abc', 'start_year=2026&end_year=2020', 'area=invalid', 'sources=invalid', 'include_optional=maybe']:
            self.assertEqual(self.client.get('/iiitd/domains?' + query).status_code, 400, query)

    def test_empty_year_range_retains_roster(self):
        payload = self.client.get('/iiitd/domains?start_year=2100&end_year=2100').get_json()
        self.assertEqual(payload['faculty_paper_count'], 0)
        self.assertEqual(len(payload['faculty_rankings']), 33)

    def test_reported_faculty_counts_and_year_boundary(self):
        rows = self.client.get('/iiitd?start_year=2016&end_year=2026').get_json()
        counts = {r['name']: r['papers'] for r in rows}
        self.assertEqual(counts['Md. Shad Akhtar'], 24)
        self.assertEqual(counts['Pushpendra Singh 0001'], 18)
        rows = self.client.get('/iiitd?start_year=2015&end_year=2026').get_json()
        self.assertEqual(next(r['papers'] for r in rows if r['name'] == 'Pushpendra Singh 0001'), 19)

    def test_reconciled_reference_and_source_union(self):
        report = self.client.get('/iiitd/validation').get_json()
        # Reviewed differences are limited to papers DBLP added after the pinned
        # snapshot; no paper the reference counts may be missing or changed.
        self.assertTrue(all(d['expected_papers'] == 0 and d['year'] == 2026 for d in report['differences']))
        totals = [self.client.get('/iiitd/domains?sources=' + source).get_json()['total_papers']
                  for source in ['csrankings', 'core-a-star', 'core-a', 'csrankings,core-a-star,core-a']]
        self.assertGreater(totals[-1], max(totals[:-1]))
        self.assertLess(totals[-1], sum(totals[:-1]))

    def test_ieee_and_acm_sources(self):
        totals = [self.client.get('/iiitd/domains?sources=' + source).get_json()['total_papers']
                  for source in ['ieee', 'acm', 'ieee,acm']]
        self.assertGreater(min(totals), 0)
        self.assertEqual(totals[2], totals[0] + totals[1])
        for source, prefix in [('ieee', 'IEEE Trans.'), ('acm', 'ACM Trans.')]:
            venues = {v['venue'] for v in self.client.get('/iiitd/domains?sources=' + source + '&start_year=1970').get_json()['top_venues']}
            self.assertTrue(venues)
            self.assertTrue(all(venue.startswith(prefix) for venue in venues))


if __name__ == '__main__':
    unittest.main()
