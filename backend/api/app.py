"""Serve validated publications from the configured database."""
import json
import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'scripts'))
sys.path.insert(0, str(BASE))
from build_iiitd_dataset import summarize
from repository import read_dataset
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
CORS(app)


def current_dataset():
    return read_dataset()


@app.errorhandler(SQLAlchemyError)
def database_unavailable(error):
    return jsonify(error='Database unavailable or not initialized. Check DATABASE_URL and run python backend/load_data.py.'), 503


def payload():
    dataset = current_dataset()
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


@app.errorhandler(ValueError)
def invalid_query(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(FileNotFoundError)
def unavailable(error):
    return jsonify(error=str(error)), 503


@app.route('/iiitd')
def iiitd():
    return jsonify(payload()['faculty_rankings'])


@app.route('/iiitd/domains')
def iiitd_domains():
    return jsonify(payload())


@app.route('/iiitd/validation')
def validation():
    metadata = current_dataset()['metadata']
    return jsonify({**metadata['validation'], 'reference_revision': metadata['reference_revision'],
                    'differences': []})


@app.route('/iiitd/faculty/<path:name>')
def faculty_profile(name):
    """All loaded paper records, independent of institute summary filters."""
    dataset = current_dataset()
    faculty = next((f for f in dataset['faculty'] if f['name'] == name), None)
    if faculty is None:
        return jsonify(error='Faculty member not found.'), 404
    papers = {p['key']: p for p in dataset.get('publications', []) if name in p['faculty']}
    return jsonify({
        'name': name,
        'institution': dataset['metadata']['institution'],
        'generated_at': dataset['metadata']['generated_at'],
        'records_available': dataset['metadata']['data_source'] != 'csrankings-published-counts',
        'publications': list(papers.values()),
    })


if __name__ == '__main__':
    app.run(debug=True)
