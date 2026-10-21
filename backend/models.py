from sqlalchemy import Column, Integer, Float, String, JSON, ForeignKey, ForeignKeyConstraint
from db import Base

class FacultyRanking(Base):
    __tablename__ = "faculty_rankings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    papers = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    domains = Column(JSON, nullable=True)
    top_domain = Column(String, nullable=True)
    top_venues = Column(JSON, nullable=True)


class ResearchDataset(Base):
    __tablename__ = 'research_datasets'
    id = Column(String(64), primary_key=True)
    data_metadata = Column(JSON, nullable=False)


class ActiveDataset(Base):
    __tablename__ = 'research_active_datasets'
    institution = Column(String(256), primary_key=True)
    dataset_id = Column(String(64), ForeignKey('research_datasets.id'), nullable=False)


class ResearchFaculty(Base):
    __tablename__ = 'research_faculty'
    dataset_id = Column(String(64), ForeignKey('research_datasets.id'), primary_key=True)
    name = Column(String(256), primary_key=True)
    record = Column(JSON, nullable=False)


class ResearchPaper(Base):
    __tablename__ = 'research_papers'
    dataset_id = Column(String(64), ForeignKey('research_datasets.id'), primary_key=True)
    paper_key = Column(String(512), primary_key=True)
    record = Column(JSON, nullable=False)


class ResearchAuthorship(Base):
    __tablename__ = 'research_authorships'
    dataset_id = Column(String(64), primary_key=True)
    paper_key = Column(String(512), primary_key=True)
    faculty_name = Column(String(256), primary_key=True)
    position = Column(Integer, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(['dataset_id', 'paper_key'], ['research_papers.dataset_id', 'research_papers.paper_key']),
        ForeignKeyConstraint(['dataset_id', 'faculty_name'], ['research_faculty.dataset_id', 'research_faculty.name']),
    )


class ResearchMembership(Base):
    __tablename__ = 'research_memberships'
    dataset_id = Column(String(64), primary_key=True)
    paper_key = Column(String(512), primary_key=True)
    source = Column(String(64), primary_key=True)
    position = Column(Integer, nullable=False)
    record = Column(JSON, nullable=False)
    __table_args__ = (ForeignKeyConstraint(['dataset_id', 'paper_key'], ['research_papers.dataset_id', 'research_papers.paper_key']),)
