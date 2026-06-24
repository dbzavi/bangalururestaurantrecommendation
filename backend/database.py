from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# Locate the database dynamically based on the current file's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Assuming backend/ and data_pipeline/ are sibling directories
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'data_pipeline', 'zomato.db'))

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLite requires connect_args={"check_same_thread": False}
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
