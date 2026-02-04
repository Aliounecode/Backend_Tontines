from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas
from passlib.context import CryptContext
from datetime import date, datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# CRUD Utilisateur
def get_utilisateur(db: Session, utilisateur_id: int):
    return db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()

def get_utilisateur_by_telephone(db: Session, telephone: str):
    return db.query(models.Utilisateur).filter(models.Utilisateur.telephone == telephone).first()

def get_utilisateur_by_email(db: Session, email: str):
    return db.query(models.Utilisateur).filter(models.Utilisateur.email == email).first()

def get_utilisateurs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Utilisateur).offset(skip).limit(limit).all()

def create_utilisateur(db: Session, utilisateur: schemas.UtilisateurCreate):
    hashed_password = pwd_context.hash(utilisateur.mot_de_passe)
    db_utilisateur = models.Utilisateur(
        nom_utilisateur=utilisateur.nom_utilisateur,
        telephone=utilisateur.telephone,
        email=utilisateur.email,
        mot_de_passe=hashed_password,
        role=utilisateur.role
    )
    db.add(db_utilisateur)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur

def authenticate_utilisateur(db: Session, telephone: str, mot_de_passe: str):
    utilisateur = get_utilisateur_by_telephone(db, telephone)
    if not utilisateur:
        return False
    if not pwd_context.verify(mot_de_passe, utilisateur.mot_de_passe):
        return False
    return utilisateur

def delete_utilisateur(db: Session, utilisateur_id: int):
    db_obj = db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj

# CRUD Tontine
def get_tontine(db: Session, tontine_id: int):
    return db.query(models.Tontine).filter(models.Tontine.id == tontine_id).first()

def get_tontines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Tontine).offset(skip).limit(limit).all()

def get_tontines_by_tresorier(db: Session, tresorier_id: int):
    return db.query(models.Tontine).filter(models.Tontine.id_tresorier == tresorier_id).all()

def create_tontine(db: Session, tontine: schemas.TontineCreate, tresorier_id: int):
    db_tontine = models.Tontine(
        **tontine.dict(),
        id_tresorier=tresorier_id
    )
    db.add(db_tontine)
    db.commit()
    db.refresh(db_tontine)
    return db_tontine

def delete_tontine(db: Session, tontine_id: int):
    db_obj = db.query(models.Tontine).filter(models.Tontine.id == tontine_id).first()
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj

def update_tontine(db: Session, tontine_id: int, tontine_update: schemas.TontineCreate):
    db_tontine = db.query(models.Tontine).filter(models.Tontine.id == tontine_id).first()
    if db_tontine:
        for key, value in tontine_update.dict().items():
            setattr(db_tontine, key, value)
        db.commit()
        db.refresh(db_tontine)
    return db_tontine

# CRUD Membre
def get_membre(db: Session, membre_id: int):
    return db.query(models.Membre).filter(models.Membre.id == membre_id).first()

def get_membres_by_tontine(db: Session, tontine_id: int):
    return db.query(models.Membre).filter(models.Membre.id_tontine == tontine_id).all()

def get_membre_by_user_tontine(db: Session, utilisateur_id: int, tontine_id: int):
    return db.query(models.Membre).filter(
        models.Membre.id_utilisateur == utilisateur_id,
        models.Membre.id_tontine == tontine_id
    ).first()

def add_membre(db: Session, membre: schemas.MembreCreate):
    db_membre = models.Membre(**membre.dict())
    db.add(db_membre)
    db.commit()
    db.refresh(db_membre)
    return db_membre

def count_membres_tontine(db: Session, tontine_id: int):
    return db.query(func.count(models.Membre.id)).filter(
        models.Membre.id_tontine == tontine_id
    ).scalar()

def remove_membre(db: Session, membre_id: int):
    db_obj = db.query(models.Membre).filter(models.Membre.id == membre_id).first()
    if db_obj:
        db.delete(db_obj)
        db.commit()
    return db_obj

# CRUD Paiement
def get_paiement(db: Session, paiement_id: int):
    return db.query(models.Paiement).filter(models.Paiement.id == paiement_id).first()

def get_paiements_by_tontine(db: Session, tontine_id: int):
    return db.query(models.Paiement).filter(models.Paiement.id_tontine == tontine_id).all()

def get_paiements_by_utilisateur(db: Session, utilisateur_id: int):
    return db.query(models.Paiement).filter(models.Paiement.id_utilisateur == utilisateur_id).all()

def create_paiement(db: Session, paiement: schemas.PaiementCreate, utilisateur_id: int):
    db_paiement = models.Paiement(
        **paiement.dict(),
        id_utilisateur=utilisateur_id
    )
    db.add(db_paiement)
    db.commit()
    db.refresh(db_paiement)
    return db_paiement

# CRUD Tour
def get_tour(db: Session, tour_id: int):
    return db.query(models.Tour).filter(models.Tour.id == tour_id).first()

def get_tours_by_tontine(db: Session, tontine_id: int):
    return db.query(models.Tour).filter(models.Tour.id_tontine == tontine_id).all()

def create_tour(db: Session, tour: schemas.TourCreate):
    db_tour = models.Tour(**tour.dict())
    db.add(db_tour)
    db.commit()
    db.refresh(db_tour)
    return db_tour

# Statistiques
def get_statistiques_tontine(db: Session, tontine_id: int):
    total_cotisations = db.query(func.sum(models.Paiement.montant)).filter(
        models.Paiement.id_tontine == tontine_id
    ).scalar() or 0
    
    total_distribue = db.query(func.sum(models.Tour.montant_recu)).filter(
        models.Tour.id_tontine == tontine_id
    ).scalar() or 0
    
    membres_actifs = count_membres_tontine(db, tontine_id)
    
    tours_realises = db.query(func.count(models.Tour.id)).filter(
        models.Tour.id_tontine == tontine_id
    ).scalar() or 0
    
    return {
        "total_cotisations": total_cotisations,
        "total_distribue": total_distribue,
        "solde_restant": total_cotisations - total_distribue,
        "membres_actifs": membres_actifs,
        "tours_realises": tours_realises
    }


# Méthodes supplémentaires
def get_membres_by_utilisateur(db: Session, utilisateur_id: int):
    return db.query(models.Membre).filter(models.Membre.id_utilisateur == utilisateur_id).all()

def get_tontines_by_ids(db: Session, tontine_ids: List[int]):
    return db.query(models.Tontine).filter(models.Tontine.id.in_(tontine_ids)).all()