from db import engine, Base
from models import FacultyRanking

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
