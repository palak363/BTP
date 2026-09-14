"""Adapter for a pinned, locally downloaded CSRankings rules snapshot."""
import importlib.util
import os
from pathlib import Path

REFERENCE = Path(__file__).resolve().parents[1] / 'data' / 'reference'
OPTIONAL_VENUES = {'ase', 'issta', 'icde', 'pods', 'hpca', 'ndss', 'eurosys',
                   'eurographics', 'fast', 'usenixatc', 'icfp', 'oopsla', 'kdd', 'pets'}
AREA_GROUPS = {
    'Artificial intelligence': 'aaai ijcai',
    'Computer vision': 'cvpr iccv eccv',
    'Machine learning & data mining': 'icml nips kdd iclr',
    'Natural language processing': 'acl emnlp naacl',
    'The Web & information retrieval': 'www sigir',
    'Computer architecture': 'asplos isca micro hpca',
    'Computer networks': 'sigcomm nsdi',
    'Computer security': 'ccs oakland usenixsec ndss pets',
    'Databases': 'sigmod vldb icde pods',
    'Design automation': 'dac iccad',
    'Embedded & real-time systems': 'emsoft rtss rtas',
    'High-performance computing': 'sc hpdc ics',
    'Mobile computing': 'mobicom mobisys sensys',
    'Measurement & performance analysis': 'imc sigmetrics',
    'Operating systems': 'sosp osdi eurosys fast usenixatc',
    'Programming languages': 'popl pldi oopsla icfp',
    'Software engineering': 'icse fse ase issta',
    'Algorithms & complexity': 'focs stoc soda',
    'Cryptography': 'crypto eurocrypt',
    'Logic & verification': 'cav lics',
    'Computational biology': 'ismb recomb',
    'Computer graphics': 'siggraph siggraph-asia eurographics',
    'Human-computer interaction': 'chiconf uist ubicomp',
    'Robotics': 'icra iros rss',
    'Visualization': 'vis vr',
    'Economics & computation': 'ec wine',
    'Computer science education': 'sigcse',
}
AREA_NAMES = {key: name for name, keys in AREA_GROUPS.items() for key in keys.split()}


def load_rules(reference=REFERENCE):
    spec = importlib.util.spec_from_file_location('csrankings_reference', reference / 'csrankings.py')
    module = importlib.util.module_from_spec(spec)
    previous = Path.cwd()
    try:
        os.chdir(reference)
        spec.loader.exec_module(module)
    finally:
        os.chdir(previous)
    return module


def classify_csr(paper, rules):
    venue, year = paper['venue'], paper['year']
    area = rules.confdict.get(venue)
    if area is None:
        return None
    volume, number = paper.get('volume') or '0', paper.get('number') or '0'
    if area in {'pacmpl', 'pacmse'}:
        venue = number
        area = rules.confdict.get(venue)
        if area is None:
            return None
    elif area == 'pacmmod':
        venue, year = rules.map_pacmmod_to_conference(venue, year, number)
        area = rules.confdict[venue]
    else:
        mappings = {
            'ACM Trans. Graph.': [('TOG_SIGGRAPH_Volume', 'SIGGRAPH', None),
                                ('TOG_SIGGRAPH_Asia_Volume', 'SIGGRAPH Asia', None)],
            'Comput. Graph. Forum': [('CGF_EUROGRAPHICS_Volume', 'EUROGRAPHICS', None)],
            'IEEE Trans. Vis. Comput. Graph.': [('TVCG_Vis_Volume', venue, 'vis'),
                                               ('TVCG_VR_Volume', 'VR', 'vr')],
        }
        for table, mapped, mapped_area in mappings.get(venue, []):
            pair = getattr(rules, table).get(year)
            if pair and (volume, number) == tuple(map(str, pair)):
                venue = mapped
                area = mapped_area or rules.confdict[venue]
    pages = paper.get('pages', '')
    page_count = rules.pagecount(pages) if pages else -1
    start = rules.startpage(pages) if pages else -1
    if not rules.countPaper(venue, year, volume, number, pages, start, page_count,
                           paper.get('url', ''), paper['title']):
        return None
    return {'venue': venue, 'year': year, 'area': area,
            'domain': AREA_NAMES.get(area, area)}
