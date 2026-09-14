"""Serve one validated artifact; PostgreSQL remains an optional legacy export."""
import json
import sys
from functools import lru_cache
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'scripts'))
from build_iiitd_dataset import summarize

app = Flask(__name__)
CORS(app)


@lru_cache(maxsize=2)
def read_dataset(path, modified):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def payload():
    path = BASE / 'data/processed/iiitd_dataset.json'
    if not path.exists():
        raise FileNotFoundError('IIITD dataset is not built. Run backend/scripts/build_iiitd_dataset.py.')
    dataset = read_dataset(str(path), path.stat().st_mtime_ns)
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
    path = BASE / 'data/processed/iiitd_validation.json'
    if not path.exists():
        raise FileNotFoundError('Validation report is not available.')
    return jsonify(json.loads(path.read_text(encoding='utf-8')))


if __name__ == '__main__':
    app.run(debug=True)
