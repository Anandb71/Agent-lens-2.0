from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session as DBSession, create_engine, select
from typing import Optional

# Database Models
class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default="New Session")

class Step(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    step_type: str
    content: str
    session_id: int = Field(foreign_key="session.id")

# SQLite Database Setup
sqlite_file_name = "agent_lens.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# FastAPI App Setup
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints
@app.post("/log/")
def create_log(step: Step):
    with DBSession(engine) as session:
        session.add(step)
        session.commit()
        session.refresh(step)
        return step

@app.post("/session/")
def create_session():
    new_session = Session()
    with DBSession(engine) as session:
        session.add(new_session)
        session.commit()
        session.refresh(new_session)
        return new_session

@app.get("/sessions/")
def get_sessions():
    with DBSession(engine) as session:
        sessions = session.exec(select(Session)).all()
        return sessions

@app.get("/session/{session_id}")
def get_session_steps(session_id: int):
    with DBSession(engine) as session:
        steps = session.exec(select(Step).where(Step.session_id == session_id)).all()
        return steps

