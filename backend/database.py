from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./smartprep.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    user_class = Column(String)  # 11, 12, Dropper
    exam = Column(String)  # JEE, NEET
    target_year = Column(Integer)
    xp = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    profile_data = Column(JSON, default={}) # Store topics confidence, etc.

class QuestionAttempt(Base):
    __tablename__ = "question_attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer)
    topic = Column(String)
    subject = Column(String)
    is_correct = Column(Integer) # 0 or 1
    time_taken = Column(Float)
    difficulty = Column(Integer)
    mistake_type = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class DailyPlan(Base):
    __tablename__ = "daily_plans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    plan_json = Column(JSON) # Store the generated plan

def init_db():
    Base.metadata.create_all(bind=engine)
