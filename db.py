# db.py
from sqlmodel import SQLModel, create_engine, Session

# Vytvorenie SQLite databázy v súbore
engine = create_engine("sqlite:///digitalpsych.db", echo=False)

def init_db():
    # Vytvorenie všetkých tabuliek podľa modelov
    SQLModel.metadata.create_all(engine)

def get_session():
    # Funkcia na získanie sessions (pripojenia k DB)
    return Session(engine)
