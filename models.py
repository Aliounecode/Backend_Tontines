from sqlalchemy import Column, Integer, String, Text, Enum, Date, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    
    id = Column(Integer, primary_key=True, index=True)
    nom_utilisateur = Column(String(50), nullable=False, unique=True)
    telephone = Column(String(20), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    mot_de_passe = Column(String(255), nullable=False)
    role = Column(Enum('membre', 'trésorier', 'admin', name='role_enum'), default='membre')
    date_creation = Column(TIMESTAMP, server_default=func.now())
    
    tontines_crees = relationship("Tontine", back_populates="tresorier")
    membres = relationship("Membre", back_populates="utilisateur")
    paiements = relationship("Paiement", back_populates="payeur")
    tours = relationship("Tour", back_populates="beneficiaire")

class Tontine(Base):
    __tablename__ = "tontines"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    description = Column(Text)
    montant_cotisation = Column(Integer, nullable=False)
    frequence = Column(Enum('journalier', 'hebdomadaire', 'mensuel', name='frequence_enum'), nullable=False)
    mode_rotation = Column(Enum('ordre', 'aléatoire', 'priorité', name='rotation_enum'), nullable=False)
    id_tresorier = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    nombre_max_membres = Column(Integer, nullable=False)
    date_demarrage = Column(Date, nullable=False)
    date_creation = Column(TIMESTAMP, server_default=func.now())
    
    tresorier = relationship("Utilisateur", back_populates="tontines_crees")
    membres = relationship("Membre", back_populates="tontine")
    paiements = relationship("Paiement", back_populates="tontine")
    tours = relationship("Tour", back_populates="tontine")

class Membre(Base):
    __tablename__ = "membres"
    
    id = Column(Integer, primary_key=True, index=True)
    id_tontine = Column(Integer, ForeignKey('tontines.id'), nullable=False)
    id_utilisateur = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    date_adhesion = Column(Date, nullable=False)
    position = Column(Integer, nullable=False)
    
    tontine = relationship("Tontine", back_populates="membres")
    utilisateur = relationship("Utilisateur", back_populates="membres")

class Paiement(Base):
    __tablename__ = "paiements"
    
    id = Column(Integer, primary_key=True, index=True)
    id_tontine = Column(Integer, ForeignKey('tontines.id'), nullable=False)
    id_utilisateur = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    montant = Column(Integer, nullable=False)
    periode = Column(Integer, nullable=False)
    date_versement = Column(TIMESTAMP, server_default=func.now())
    
    tontine = relationship("Tontine", back_populates="paiements")
    payeur = relationship("Utilisateur", back_populates="paiements")

class Tour(Base):
    __tablename__ = "tours"
    
    id = Column(Integer, primary_key=True, index=True)
    id_tontine = Column(Integer, ForeignKey('tontines.id'), nullable=False)
    id_utilisateur = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    periode = Column(Integer, nullable=False)
    montant_recu = Column(Integer, nullable=False)
    date_reception = Column(TIMESTAMP, server_default=func.now())
    
    tontine = relationship("Tontine", back_populates="tours")
    beneficiaire = relationship("Utilisateur", back_populates="tours")