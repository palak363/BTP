"""Serve validated per-institute artifacts; PostgreSQL remains an optional legacy export."""
import json
import sys
from functools import lru_cache
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'scripts'))
from build_institutes import INDEX, INSTITUTES, summarize

app = Flask(__name__)
CORS(app)
LEGACY_SLUG = 'iiit-delhi'


@lru_cache(maxsize=16)
def read_json(path, modified):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load(path, message):
    if not path.exists():
        raise FileNotFoundError(message)
    return read_json(str(path), path.stat().st_mtime_ns)


def current_index():
    return load(INDEX, 'Institute index is not built. Run backend/scripts/build_institutes.py.')


def current_dataset(slug):
    if not any(entry['slug'] == slug for entry in current_index()['institutes']):
        raise LookupError('Institute not found.')
    return load(INSTITUTES / f'{slug}.json', 'Institute dataset is not built. Run backend/scripts/build_institutes.py.')


def payload(slug):
    dataset = current_dataset(slug)
    start, end = int(request.args.get('start_year', 2016)), int(request.args.get('end_year', 2026))
    if not 1970 <= start <= end <= 2269:
        raise ValueError('Choose an inclusive year range between 1970 and 2269.')
    sources = request.args.get('sources', 'csrankings').split(',')
    if not sources or any(s not in dataset['metadata']['available_sources'] for s in sources):
        raise ValueError('Selected source is unavailable in this dataset.')
    areas = request.args.getlist('area')
    if any(area not in dataset['metadata']['available_areas'] for area in areas):
        raise ValueError('Unknown research area.')
    optional = request.args.get('include_optional', 'false')
    if optional not in {'true', 'false'}:
        raise ValueError('include_optional must be true or false.')
    return summarize(dataset, start, end, sources, areas, optional == 'true')


def faculty_payload(name, slug=None):
    """All loaded paper records, independent of institute summary filters."""
    member = next((f for f in current_index()['faculty'] if f['name'] == name and (slug is None or f['slug'] == slug)), None)
    if member is None:
        return jsonify(error='Faculty member not found.'), 404
    dataset = current_dataset(member['slug'])
    papers = {p['key']: p for p in dataset.get('publications', []) if name in p['faculty']}
    return jsonify({
        'name': name,
        'institution': dataset['metadata']['institution'],
        'slug': member['slug'],
        'generated_at': dataset['metadata']['generated_at'],
        'records_available': dataset['metadata']['data_source'] != 'csrankings-published-counts',
        'publications': list(papers.values()),
    })


@app.errorhandler(ValueError)
def invalid_query(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(LookupError)
def not_found(error):
    return jsonify(error=str(error)), 404


@app.errorhandler(FileNotFoundError)
def unavailable(error):
    return jsonify(error=str(error)), 503


@app.route('/institutes')
def institutes():
    return jsonify(current_index())


@app.route('/institutes/<slug>')
def institute_rankings(slug):
    return jsonify(payload(slug)['faculty_rankings'])


@app.route('/institutes/<slug>/domains')
def institute_domains(slug):
    return jsonify(payload(slug))


@app.route('/institutes/<slug>/validation')
def institute_validation(slug):
    current_dataset(slug)
    return jsonify(load(INSTITUTES / f'{slug}.validation.json', 'Validation report is not available.'))


@app.route('/faculty/<path:name>')
def faculty_profile(name):
    return faculty_payload(name)


# IIIT Delhi routes from the single-institute version of this API.
@app.route('/iiitd')
def iiitd():
    return institute_rankings(LEGACY_SLUG)


@app.route('/iiitd/domains')
def iiitd_domains():
    return institute_domains(LEGACY_SLUG)


@app.route('/iiitd/validation')
def validation():
    return institute_validation(LEGACY_SLUG)


@app.route('/iiitd/faculty/<path:name>')
def iiitd_faculty(name):
    return faculty_payload(name, LEGACY_SLUG)


if __name__ == '__main__':
    app.run(debug=True)
