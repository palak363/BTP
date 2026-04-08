from sqlalchemy import Column, Integer, String, JSON
from db import Base

class FacultyRanking(Base):
    __tablename__ = "faculty_rankings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    papers = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    domains = Column(JSON, nullable=True)
    top_domain = Column(String, nullable=True)
    top_venues = Column(JSON, nullable=True)
