"""Atomic, versioned database imports; readers always use one complete snapshot."""
import hashlib
import json
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from db import Base, engine
from models import ActiveDataset, ResearchDataset, ResearchFaculty, ResearchPaper, ResearchAuthorship, ResearchMembership

TABLES = [model.__table__ for model in (ResearchDataset, ActiveDataset, ResearchFaculty, ResearchPaper, ResearchAuthorship, ResearchMembership)]


def validate_dataset(dataset):
    metadata = dataset['metadata']
    if not metadata.get('institution') or metadata.get('data_source') == 'csrankings-published-counts':
        raise ValueError('Import a complete publication dataset, not reference-only counts.')
    if not metadata.get('validation', {}).get('matching'):
        raise ValueError('Import requires a successfully reconciled dataset.')
    faculty = dataset['faculty']
    names = {f['name'] for f in faculty}
    if not names or '' in names or len(names) != len(faculty):
        raise ValueError('Faculty names must be nonempty and unique.')
    identities = [f['dblp_url'] for f in faculty]
    if len(set(identities)) != len(identities):
        raise ValueError('Duplicate DBLP identity.')
    keys = set()
    for paper in dataset['publications']:
        if paper['key'] in keys:
            raise ValueError('Duplicate publication key.')
        keys.add(paper['key'])
        if not paper['faculty'] or len(set(paper['faculty'])) != len(paper['faculty']) or not set(paper['faculty']) <= names:
            raise ValueError('Invalid faculty authorship.')
        sources = [m['source'] for m in paper['memberships']]
        if not sources or len(set(sources)) != len(sources) or not set(sources) <= set(metadata['available_sources']):
            raise ValueError('Invalid publication source memberships.')


def import_dataset(dataset, database_engine=engine):
    validate_dataset(dataset)
    identifier = hashlib.sha256(json.dumps(dataset, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    Base.metadata.create_all(database_engine, tables=TABLES)
    with Session(database_engine) as session, session.begin():
        if database_engine.dialect.name == 'postgresql':
            session.execute(text('SELECT pg_advisory_xact_lock(4815162342)'))
        if session.get(ResearchDataset, identifier) is None:
            session.add(ResearchDataset(id=identifier, data_metadata=dataset['metadata']))
            session.flush()
            session.execute(ResearchFaculty.__table__.insert(), [dict(dataset_id=identifier, name=f['name'], record=f) for f in dataset['faculty']])
            papers = dataset['publications']
            if papers:
                session.execute(ResearchPaper.__table__.insert(), [dict(dataset_id=identifier, paper_key=p['key'],
                    record={k: v for k, v in p.items() if k not in {'faculty', 'memberships'}}) for p in papers])
                session.execute(ResearchAuthorship.__table__.insert(), [dict(dataset_id=identifier, paper_key=p['key'], faculty_name=name, position=i)
                    for p in papers for i, name in enumerate(p['faculty'])])
                session.execute(ResearchMembership.__table__.insert(), [dict(dataset_id=identifier, paper_key=p['key'], source=m['source'], position=i, record=m)
                    for p in papers for i, m in enumerate(p['memberships'])])
        active = session.get(ActiveDataset, dataset['metadata']['institution'])
        if active:
            active.dataset_id = identifier
        else:
            session.add(ActiveDataset(institution=dataset['metadata']['institution'], dataset_id=identifier))
    return identifier


def read_dataset(database_engine=engine, institution='IIIT Delhi'):
    with Session(database_engine) as session:
        active = session.get(ActiveDataset, institution)
        if active is None:
            raise FileNotFoundError('No dataset is loaded in the database. Run python backend/load_data.py.')
        identifier = active.dataset_id
        metadata = session.get(ResearchDataset, identifier).data_metadata
        faculty = [row.record for row in session.scalars(select(ResearchFaculty).where(ResearchFaculty.dataset_id == identifier).order_by(ResearchFaculty.name))]
        papers = {row.paper_key: dict(row.record, faculty=[], memberships=[]) for row in session.scalars(
            select(ResearchPaper).where(ResearchPaper.dataset_id == identifier).order_by(ResearchPaper.paper_key))}
        for row in session.scalars(select(ResearchAuthorship).where(ResearchAuthorship.dataset_id == identifier).order_by(ResearchAuthorship.position)):
            papers[row.paper_key]['faculty'].append(row.faculty_name)
        for row in session.scalars(select(ResearchMembership).where(ResearchMembership.dataset_id == identifier).order_by(ResearchMembership.position)):
            papers[row.paper_key]['memberships'].append(row.record)
        return {'metadata': metadata, 'faculty': faculty, 'publications': list(papers.values())}
