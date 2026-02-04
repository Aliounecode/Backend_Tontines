from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Charge les variables du fichier .env
load_dotenv()

# Récupère l'URL. Si elle n'existe pas, renvoie None.
DATABASE_URL = os.getenv("DATABASE_URL")

# Sécurité : On vérifie que l'URL est bien chargée
if not DATABASE_URL:
    raise ValueError("❌ Erreur : La variable DATABASE_URL est introuvable. Vérifie ton fichier .env !")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()