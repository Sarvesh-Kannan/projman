from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import os

# Create database directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Create SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///data/project_manager.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    description = Column(Text)
    start_date = Column(DateTime, default=datetime.datetime.now)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")
    priority = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    dependencies = relationship("ProjectDependency", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True)
    description = Column(Text)
    status = Column(String(20), default="pending")
    priority = Column(Integer, default=3)
    project_id = Column(Integer, ForeignKey("projects.id"))
    assigned_to = Column(String(100), nullable=True)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    project = relationship("Project", back_populates="tasks")
    dependencies = relationship("TaskDependency", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    metrics = relationship("TaskMetric", back_populates="task", cascade="all, delete-orphan")

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    depends_on_id = Column(Integer, ForeignKey("tasks.id"))
    dependency_type = Column(String(20), default="finish_to_start")  # finish_to_start, start_to_start, etc.
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    task = relationship("Task", back_populates="dependencies", foreign_keys=[task_id])

class ProjectDependency(Base):
    __tablename__ = "project_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    depends_on_id = Column(Integer, ForeignKey("projects.id"))
    dependency_type = Column(String(20), default="finish_to_start")
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    project = relationship("Project", back_populates="dependencies", foreign_keys=[project_id])

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    content = Column(Text)
    author = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    task = relationship("Task", back_populates="comments")

class TaskMetric(Base):
    __tablename__ = "task_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    metric_type = Column(String(50))  # complexity, sentiment, etc.
    metric_value = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.now)
    
    task = relationship("Task", back_populates="metrics")

class WorkflowMetric(Base):
    __tablename__ = "workflow_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    flow_name = Column(String(100))
    run_id = Column(String(100))
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20))
    tasks_processed = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 